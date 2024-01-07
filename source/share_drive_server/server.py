import argparse

import queue
from _socket import IPPROTO_UDP
from multiprocessing import Process, Queue

from select import select
from socket import socket, AF_INET, SOCK_DGRAM
from time import sleep

from coap_core.coap_utilities.coap_logger import logger, LogColor
from share_drive_server.server_resource import ServerResource
from coap_core.coap_worker.coap_worker_pool import CoapWorkerPool


class Server:
    def __init__(self, ip_address, port):
        self._skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self._skt.bind((ip_address, port))

        self._resource = ServerResource("share_drive", "/home/damir/coap/server/resources/")
        self._processes_queues = {}
        self._recv_queue = queue.Queue()
        logger.debug_mode = True

    @logger
    def listen(self):
        try:
            while True:
                active_socket, _, _ = select([self._skt], [], [], 1)

                if active_socket:
                    data, address = self._skt.recvfrom(1152)
                    self._recv_queue.put((data, address))
                    if address not in self._processes_queues:
                        data_queue = Queue()

                        pool = CoapWorkerPool(self._skt, self._resource, data_queue)
                        client_process = Process(target=pool.start)
                        client_process.start()

                        self._processes_queues[address] = data_queue, client_process
                        logger.debug(f"Creating a new process {client_process} for {address}.", LogColor.CYAN)
                        sleep(0.5)

                    self._processes_queues[address][0].put((data, address))

        except Exception as e:
            for _, process in self._processes_queues.values():
                process[1].terminate()
                process[1].join()
            raise e


def main():
    parser = argparse.ArgumentParser(description='Server script with address and port arguments')

    parser.add_argument('--server_address', type=str, default='192.168.217.129', help='Server address')
    parser.add_argument('--server_port', type=int, default=5683, help='Server port')

    args = parser.parse_args()

    Server(args.server_address, args.server_port).listen()


main()
