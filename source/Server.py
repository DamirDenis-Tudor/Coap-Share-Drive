import threading

from select import select
from _socket import IPPROTO_UDP
from socket import socket, AF_INET, SOCK_DGRAM

from source.Core.AbstractWorker import WorkerType
from source.Core.WorkerPool import WorkerPool
from source.Logger.Logger import logger
from source.Packet.CoapPacket import CoapPacket
from source.Resource.Resource import Resource
from source.Resource.StorageResource import StorageResource


class Server:
    def __init__(self, ip_addr: str, port: int):
        threading.current_thread().name = f"Server[{threading.current_thread().name}]"

        self.__resource = []

        self.__socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self.__socket.bind((ip_addr, port))

        self.__worker_pool = WorkerPool(WorkerType.SERVER_WORKER)
        self.__worker_pool.start()

    @logger
    def listen(self):
        while True:
            active_socket, _, _ = select([self.__socket], [], [], 0.01)

            if active_socket:
                data, address = self.__socket.recvfrom(1032)
                self.__worker_pool.submit_task(CoapPacket.decode(data))

            self.__worker_pool.check_idle_workers()

    @logger
    def add_resource(self, resource: Resource):
        self.__resource.append(resource)


if __name__ == '__main__':
    server = Server('127.0.0.2', int(5683))
    server.add_resource(StorageResource("share_drive"))
    server.listen()
