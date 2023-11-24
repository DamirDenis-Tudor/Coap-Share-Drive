import threading
from select import select
from _socket import IPPROTO_UDP
from socket import socket, AF_INET, SOCK_DGRAM

from source.Logger.Logger import logger
from source.PacketManager.Packet import Packet
from source.WorkloadAnaliser.WorkerPool import WorkerPool


class Server:
    def __init__(self, ip_addr: str, ports: list[int]):
        threading.current_thread().name = f"Server[{threading.current_thread().name}]"

        self.__sockets = []
        for port in ports:
            skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
            skt.bind((ip_addr, port))
            self.__sockets.append(skt)

        self.__worker_pool = WorkerPool()
        self.__worker_pool.start()

    @logger
    def start_loop(self):
        while True:
            active_sockets, _, _ = select(self.__sockets, [], [], 0.01)

            if active_sockets:
                for active_socket in active_sockets:
                    data, address = active_socket.recvfrom(1032)
                    self.__worker_pool.submit_task(Packet(data, active_socket, address))

            self.__worker_pool.check_idle_workers()


if __name__ == '__main__':
    SERVER_PORTS = [i for i in range(6600, 6605)]
    Server('127.0.0.1', SERVER_PORTS).start_loop()
