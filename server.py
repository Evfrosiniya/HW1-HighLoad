import os
import socket

from extensions import Request


class Worker:
    def __init__(self, pid, pipe):
        self.pid = pid
        self.working = False
        self.pipe = pipe


class HttpServer:
    workers = []

    def start(self, root_dir, RequestHandlerClass, host, port, workers=1, listeners=100, recv_msg_size=1024):
        self.host = host
        self.port = port
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.workers_num = workers
        self.listeners = listeners
        self.recv_msg_size = recv_msg_size
        self.RequstHandlerClass = RequestHandlerClass
        self.root_dir = root_dir
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.listeners)
        for _ in range(self.workers_num - 1):
            pid = os.fork()
            if pid:
                self.workers.append(pid)
            else:
                print("Running worker on PID: {}".format(os.getpid()))
                while True:
                    client_sock, client_addr = self.sock.accept()
                    data = client_sock.recv(self.recv_msg_size)
                    if len(data.strip()) == 0:
                        client_sock.close()
                        continue
                    req = Request(data)
                    handler = self.RequstHandlerClass(req, self.root_dir)
                    resp = handler.handle()
                    client_sock.sendall(resp.build())
                    client_sock.close()
        self.sock.close()

        for pid in self.workers:
            os.waitpid(pid, 0)
