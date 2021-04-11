import sys
import socket
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import as_completed
from tools import Debuger
import urllib3

class Server:
    def __init__(self, hostname="0.0.0.0",
                       port=80,
                       connections=100,
                       verbosity=0,
                       timeout=250):
        self.timeout = timeout
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.settimeout(self.timeout)
        self.running = False
        self.workers = []
        self.debuger = Debuger(verbosity)
        self.timeout = timeout
        self.pool_manager = urllib3.PoolManager()
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

    def run_worker(self, conn, addr):
        self.debuger.v_print(1, f"Connected with {addr[0]}:{str(addr[1])}")
        raw_request = self._get_chunks(conn)
        request = raw_request.decode(encoding="utf-8").split()

        try:
            raw_url = request[1]
            host = raw_url.split("/")[2].split(":")
        except:
            print("\n\t request",raw_request)
            print("\n\t raw_url", raw_url)
            print("\n\t host", host)
        if len(host) >1:
            port = int(host[1])
            host = host[0]
        else:
            port = 80
            host = host[0]
        self.debuger.v_print(2, f"{addr[0]}:{addr[1]}->{host}:{port} {raw_url}")
        dest_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest_server.settimeout(self.timeout)
        try:
            dest_server.connect((host, port))
            dest_server.sendall(raw_request)

            response = self._get_chunks(dest_server)
        except:
            conn.close()
            self.debuger.v_print(1, "failed to connect to webserver")
            return;
        self.debuger.v_print(3, response)

        conn.sendall(real_request.read())

        conn.close()


    def start_proxy(self):
        while self.running:
            conn, addr = self.soc.accept()
            worker = threading.Thread(target=self.run_worker,
                                        args=(conn, addr))
            worker.start()
            self.workers.append(worker)
            print(len(self.workers))

    def __del__(self):
        self.running = False
        self.soc.close()

    def start(self):
        self.main_thread = threading.Thread(target=self.start_proxy)
        self.running = True
        self.main_thread.start()
