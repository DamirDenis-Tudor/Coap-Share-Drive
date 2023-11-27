import threading

from select import select
from _socket import IPPROTO_UDP
from socket import socket, AF_INET, SOCK_DGRAM

from source.Logger.Logger import logger
from source.Packet.CoapPacket import CoapPacket
from source.Workload.WorkerPool import WorkerPool


class Server:
    def __init__(self, ip_addr: str, port: int):
        threading.current_thread().name = f"Server[{threading.current_thread().name}]"

        self.__socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self.__socket.bind((ip_addr, port))

        self.__worker_pool = WorkerPool()
        self.__worker_pool.start()

    @logger
    def start_loop(self):
        while True:
            active_socket, _, _ = select([self.__socket], [], [], 0.01)

            if active_socket:
                data, address = self.__socket.recvfrom(1032)
                self.__worker_pool.submit_task(CoapPacket.decode(data, address, self.__socket))

            self.__worker_pool.check_idle_workers()


if __name__ == '__main__':
    Server('127.0.0.2', int(5683)).start_loop()
