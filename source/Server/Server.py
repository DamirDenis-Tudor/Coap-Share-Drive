from select import select
from _socket import IPPROTO_UDP
from socket import socket, AF_INET, SOCK_DGRAM

from source.Logger.Logger import logger
from source.PacketManager.Packet import Packet
from source.ThreadManager.WorkerPool import WorkerPool


class Server:
    def __init__(self, ip_addr: str, port: int):
        self.__socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self.__socket.bind((ip_addr, port))
        self.__worker_pool = None

    @logger
    def start_loop(self):
        while True:
            response, _, _ = select([self.__socket], [], [], 1)
            if response:
                data, address = self.__socket.recvfrom(1032)
                if self.__worker_pool is None:
                    self.__worker_pool = WorkerPool()
                    self.__worker_pool.start()
                self.__worker_pool.submit_task(Packet(data, address), self.__socket)


if __name__ == '__main__':
    Server('127.0.0.1', 8730).start_loop()
