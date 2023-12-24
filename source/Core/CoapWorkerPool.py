import abc
import random
import threading
from _socket import IPPROTO_UDP
from abc import ABC
from enum import Enum, auto
from queue import Queue
from select import select
from socket import socket, AF_INET, SOCK_DGRAM

from source.Core.AbstractWorker import AbstractWorker, WorkerType
from source.Core.ClientWorker import ClientWorker
from source.Core.ServerWorker import ServerWorker
from source.Packet.CoapConfig import CoapType, CoapCodeFormat, CoapOptionDelta
from source.Packet.CoapTemplates import CoapTemplates
from source.Packet.CoapTransaction import CoapTransactionPool
from source.Utilities.Logger import logger
from threading import Event

from source.Packet.CoapPacket import CoapPacket


class CoapWorkerPool(ABC):
    @staticmethod
    def __verify_format(task) -> bool:
        if (task.version != 1
                or not CoapType.is_valid(task.message_type)
                or not CoapCodeFormat.is_valid(task.code)
                or not CoapOptionDelta.is_valid(task.options)):
            return False

        return True

    def __init__(self, worker_type: WorkerType, ip_address: str, port: int):

        self.name = f"WorkerPoll[{worker_type}]"
        self.__worker_type = worker_type

        self._short_term_shared_work = []
        self._long_term_shared_work = []
        self._failed_requests = []

        self._socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self._socket.bind((ip_address, port))

        self.__workers: list[AbstractWorker] = []

        self.__received_packets = Queue()
        self.__valid_coap_packets = Queue()

        self.__event_check_idle = Event()

        self.__max_queue_size = 2000000
        self.__allowed_idle_time = 5

        self.__background_threads: list[threading.Thread] = [
            threading.Thread(target=self.check_idle_workers),
            threading.Thread(target=self.coap_format_filter),
            threading.Thread(target=self.deduplication_filter),
        ]

        CoapTransactionPool()

        self.__is_running = True

    def add_background_thread(self, thread: threading.Thread):
        self.__background_threads.append(thread)

    def remove_short_term_work(self, work_data: tuple):
        self._short_term_shared_work.remove(work_data)

    def remove_long_term_work(self, token):
        self._long_term_shared_work = {t: t for t in self._long_term_shared_work if not (t[0] == token)}

    @logger
    def _create_worker(self) -> AbstractWorker:
        chosen_worker = None
        if self.__worker_type == WorkerType.SERVER_WORKER:
            chosen_worker = ServerWorker(self)
        elif self.__worker_type == WorkerType.CLIENT_WORKER:
            chosen_worker = ClientWorker(self)

        self.__workers.append(chosen_worker)
        chosen_worker.start()

        return chosen_worker

    def _choose_worker(self) -> AbstractWorker:
        available_workers = filter(lambda worker: worker.get_queue_size() < self.__max_queue_size, self.__workers)
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
    def deduplication_filter(self):
        while True:
            packet: CoapPacket = self.__valid_coap_packets.get()

            if not self.__is_running:
                break

            work = (packet.token, packet.message_id, packet.sender_ip_port)
            if (work not in self._short_term_shared_work and
                    work not in self._long_term_shared_work):
                self._short_term_shared_work.append(work)
                self._choose_worker().submit_task(packet)

                # When a content response is received, the initial request may not have received the
                # acknowledgment, but it's clear that the client/server got the request.
                # The initial transaction related to the request must be finished.
                if CoapCodeFormat.is_success(packet.code):
                    if packet.options.get(CoapOptionDelta.BLOCK2.value):
                        # if a block 2/1 option is included, it's clear that this is
                        # a long-term request, and it must be handled properly
                        self._long_term_shared_work.append(work)

                        # now based on the block_id, message_id we can search for parent transaction
                        # that waits for an ACk with the formula:<parent_t_msg_id=task.msg_id-block_id-1>
                        block2 = packet.options.get(CoapOptionDelta.BLOCK2.value)
                        block_id = CoapPacket.decode_option_block(block2)["NUM"]
                        parent_msg_id = packet.message_id - block_id - 1
                    else:
                        # response may come in one piece with no block2 option
                        parent_msg_id = packet.message_id - 1

                    CoapTransactionPool().finish_transaction(packet.token, parent_msg_id)
            else:
                logger.log(f"{self.name} Packet duplicated: \n {packet.__repr__()}")

    @logger
    def coap_format_filter(self):

        while self.__is_running:
            data: tuple[bytes, tuple] = self.__received_packets.get()
            packet = CoapPacket.decode(data[0], data[1], self._socket)

            if not self.__is_running:
                break

            if not packet.is_dummy:

                # verifying the integrity of the packet
                if CoapWorkerPool.__verify_format(packet):

                    match packet.message_type:

                        case CoapType.CON.value:
                            if (packet.token, packet.sender_ip_port) not in self._failed_requests:
                                if CoapCodeFormat.is_method(packet.code):  # request -> EMPTY ACK & PROCES REQUEST
                                    ack = CoapTemplates.EMPTY_ACK.value_with(packet.token, packet.message_id)
                                else:  # content -> SUCCESS ACK
                                    ack = CoapTemplates.SUCCESS_ACK.value_with(packet.token, packet.message_id)
                                self._socket.sendto(ack.encode(), packet.sender_ip_port)
                                self.__valid_coap_packets.put(packet)

                        case CoapType.ACK.value:
                            CoapTransactionPool().finish_transaction(packet.token, packet.message_id)

                        case CoapType.RST.value:
                            logger.log("Failed")
                            self._failed_requests.append((packet.token, packet.sender_ip_port))

                        case _:
                            pass
                else:
                    logger.log(f"{self.name} Invalid coap format: \n {packet.__repr__()}")

                    invalid_format = CoapTemplates.NON_COAP_FORMAT.value_with(packet.token, packet.message_id)
                    invalid_format.code = CoapCodeFormat.SERVER_ERROR_INTERNAL_SERVER_ERROR.value()

                    self._socket.sendto(invalid_format.encode(), packet.sender_ip_port)

            CoapTransactionPool().solve_transactions()

    @logger
    def listen(self):
        for thread in self.__background_threads:
            thread.start()

        while self.__is_running:
            try:
                active_socket, _, _ = select([self._socket], [], [], 0.01)

                if active_socket:
                    data, address = self._socket.recvfrom(1152)
                    self.__received_packets.put((data, address))
                else:
                    self.__received_packets.put((CoapTemplates.DUMMY_PACKET.value().encode(), None))

                self.__event_check_idle.set()
            except KeyboardInterrupt as e:

                self.__is_running = False

                # Wake up threads to finish their tasks
                self.__received_packets.put(CoapPacket())
                self.__valid_coap_packets.put(CoapPacket())
                self.__event_check_idle.set()

        for worker in self.__workers:
            worker.stop()

        for thread in self.__background_threads:
            thread.join()

    @abc.abstractmethod
    def get_resource(self, path):
        pass
