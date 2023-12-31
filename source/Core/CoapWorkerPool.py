import abc
import threading

import socket
import time
from _socket import *
from abc import ABC
from multiprocessing import Queue
from select import select
from socket import socket, AF_INET, SOCK_DGRAM
from source.Core.AbstractWorker import AbstractWorker, WorkerType
from source.Core.ClientWorker import ClientWorker
from source.Core.ServerWorker import ServerWorker
from source.Packet.CoapConfig import CoapType, CoapCodeFormat, CoapOptionDelta
from source.Packet.CoapTemplates import CoapTemplates
from source.Transaction.CoapTransactionPool import CoapTransactionPool
from source.Utilities.CustomQueue import CustomQueue
from source.Utilities.Logger import logger
from threading import Event
from source.Packet.CoapPacket import CoapPacket
from source.Utilities.Timer import Timer


class CoapWorkerPool(ABC):
    @staticmethod
    def __verify_format(task) -> bool:
        if (task.version != 1
                or not CoapType.is_valid(task.message_type)
                or not CoapCodeFormat.is_valid(task.code)
                or not CoapOptionDelta.is_valid(task.options)):
            return False

        return True

    def __init__(self, worker_class: type, ip_address: str, port: int):

        self.name = f"WorkerPoll[{worker_class}]"
        self.__worker_class = worker_class

        self._short_term_shared_work = {}
        self._long_term_shared_work = {}
        self._failed_requests = {}

        self._socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self._socket.bind((ip_address, port))

        self.__workers: list[AbstractWorker] = []

        self.__received_packets = CustomQueue()
        self.__valid_coap_packets = CustomQueue()

        self.__event_check_idle = Event()
        self.__event_handle_transactions = Event()
        self.__event_deduplication = Event()

        self.__max_queue_size = 50000
        self.__allowed_idle_time = 60

        self.__background_threads: list[threading.Thread] = [
            threading.Thread(target=self.check_idle_workers),
            threading.Thread(target=self.coap_format_filter),
            threading.Thread(target=self.deduplication_filter),
            threading.Thread(target=self.handle_transactions),
        ]
        self.__is_running = True

        CoapTransactionPool()

    def add_background_thread(self, thread: threading.Thread):
        self.__background_threads.append(thread)

    def remove_short_term_work(self, work_data: tuple):
        if work_data in self._short_term_shared_work:
            self._short_term_shared_work.pop(work_data)

    def remove_long_term_work(self, work_data: tuple):
        if work_data in self._long_term_shared_work:
            self._long_term_shared_work.pop(work_data)

    @logger
    def _create_worker(self) -> AbstractWorker:
        chosen_worker = self.__worker_class(self)
        chosen_worker.start()

        self.__workers.append(chosen_worker)

        return chosen_worker

    def _choose_worker(self) -> AbstractWorker:
        light_loaded_workers = filter(lambda worker: not worker.is_heavily_loaded(), self.__workers)
        available_workers = filter(lambda worker: worker.get_queue_size() < self.__max_queue_size, light_loaded_workers)
        chosen_worker = min(available_workers, default=None, key=lambda x: x.get_queue_size())

        if not chosen_worker:
            new_worker = self._create_worker()
            return new_worker

        return chosen_worker

    @logger
    def check_idle_workers(self):
        while True:
            self.__event_check_idle.wait()

            if not self.__is_running:
                break

            for worker in self.__workers:
                if worker.get_idle_time() > self.__allowed_idle_time and len(self.__workers) > 1:
                    self.__workers.remove(worker)
                    worker.stop()

            self.__event_check_idle.clear()

    @logger
    def handle_transactions(self):
        while True:
            self.__event_handle_transactions.wait()
            CoapTransactionPool().solve_transactions()
            self.__event_handle_transactions.clear()

    @logger
    def deduplication_filter(self):
        while self.__is_running:
            packet: CoapPacket = self.__valid_coap_packets.get()

            with (Timer()):

                work = packet.short_term_work_id()

                long_term_work = None
                # When a content response is received, the initial request may not have received the
                # acknowledgment, but it's clear that the client/server got the request.
                # The initial transaction related to the request must be finished.
                if CoapCodeFormat.is_success(packet.code) and packet.has_option_block():
                    # if a block 2/1 option is included, it's clear that this is
                    # a long-term request, and it must be handled properly
                    long_term_work = packet.long_term_work_id()

                if (work not in self._short_term_shared_work
                        and long_term_work not in self._long_term_shared_work):

                    self._choose_worker().submit_task(packet)

                    if long_term_work:
                        self._long_term_shared_work[long_term_work] = time.time()
                    else:
                        self._short_term_shared_work[work] = time.time()
                else:
                    logger.log(f"{self.name} Packet duplicated: \n {packet.__repr__()}")

    @logger
    def coap_format_filter(self):

        while self.__is_running:
            data: tuple[bytes, tuple] = self.__received_packets.get()
            packet = CoapPacket.decode(data[0], data[1], self._socket)

            # verifying the integrity of the packet
            if CoapWorkerPool.__verify_format(packet):

                match packet.message_type:

                    case CoapType.CON.value:
                        if (packet.token, packet.sender_ip_port) not in self._failed_requests:
                            if CoapCodeFormat.is_method(packet.code):  # request -> EMPTY ACK & PROCES REQUEST
                                ack = CoapTemplates.EMPTY_ACK.value_with(packet.token, packet.message_id)
                            else:  # content -> SUCCESS ACK
                                ack = CoapTemplates.SUCCESS_ACK.value_with(packet.token, packet.message_id)
                                ack.payload = str(packet.get_block_id()).encode('utf-8')
                            self._socket.sendto(ack.encode(), packet.sender_ip_port)

                            self.__valid_coap_packets.put(packet)

                    case CoapType.ACK.value:
                        CoapTransactionPool().finish_transaction(packet)

                    case CoapType.RST.value:
                        logger.log("Failed")
                        self._failed_requests[packet.token, packet.sender_ip_port] = time.time()

                    case _:
                        pass
            else:
                logger.log(f"{self.name} Invalid coap format: \n {packet.__repr__()}")

                invalid_format = CoapTemplates.NON_COAP_FORMAT.value_with(packet.token, packet.message_id)
                invalid_format.code = CoapCodeFormat.SERVER_ERROR_INTERNAL_SERVER_ERROR.value()

                self._socket.sendto(invalid_format.encode(), packet.sender_ip_port)

    @logger
    def listen(self):
        for thread in self.__background_threads:
            thread.start()

        while self.__is_running:
            try:
                active_socket, _, _ = select([self._socket], [], [], 1)

                if active_socket:
                    data, address = self._socket.recvfrom(1152)
                    self.__received_packets.put((data, address))

                self.__event_handle_transactions.set()
                self.__event_check_idle.set()
            except KeyboardInterrupt as e:

                self.__is_running = False
                self.__event_check_idle.set()

        for worker in self.__workers:
            worker.stop()

        for thread in self.__background_threads:
            thread.join()

    @abc.abstractmethod
    def get_resource(self, path):
        pass
