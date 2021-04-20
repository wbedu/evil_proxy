import sys
import socket
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import as_completed
from tools import Debuger
from Harvester import Harvester
import json
import http
import requests

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
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        self.workers = []
        self.debuger = Debuger(verbosity)
        self.harvester = Harvester(hostname, mode, database="harvest.sqlite")
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
        return {
            "method": method,
            "url": url
        }


    def _format_headers(self, raw_headers):
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
        server_response = requests.request(**request)
        proto = 'HTTP/1.1'
        status_code = server_response.status_code
        status_text = server_response.reason if server_response.reason else ""

        headers = self._format_headers(server_response.headers)
        if server_response.encoding is not None:
            encoding = server_response.encoding
            content = self._decode_body(server_response.content, encoding)
            print("start harvest")
            self.harvester.harvest(server_response, addr[0])
        else:
            encoding = ""
            rq_data = real_request.data
        head = f"{proto} {status_code} {status_text}\n{headers}\r\n\r\n"

        conn.sendall(head.encode())

        content = content if encoding == "" else content.encode(encoding=encoding)
        conn.sendall(content)
        conn.close()


    def start_proxy(self):
        while self.running:
            conn, addr = self.soc.accept()
            worker = threading.Thread(target=self.run_worker,
                                        args=(conn, addr))
            worker.start()
            self.workers.append(worker)

    def print_harvest(self):
        print(self.harvester)

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
