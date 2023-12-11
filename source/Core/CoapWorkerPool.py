import random
import threading
from _socket import IPPROTO_UDP
from abc import ABC
from queue import Queue
from select import select
from socket import socket, AF_INET, SOCK_DGRAM

from source.Core.AbstractWorker import AbstractWorker, WorkerType
from source.Core.ClientWorker import ClientWorker
from source.Core.ServerWorker import ServerWorker
from source.Packet.CoapConfig import CoapType, CoapCodeFormat, CoapOptionDelta
from source.Packet.CoapTemplates import CoapTemplates
from source.Packet.CoapTokenGen import CoapTokenGen
from source.Packet.CoapTransaction import CoapTransactionsPool
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
        self._shared_in_working = []

        self._socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self._socket.bind((ip_address, port))

        self.__workers: list[AbstractWorker] = []
        self.__to_be_solved = []
        self.__event_check_idle = Event()
        self.__event_submit_packet = Event()

        self.__max_queue_size = 5
        self.__allowed_idle_time = 5

        self.__background_threads: list[threading.Thread] = [
            threading.Thread(target=self.analise_task),
            threading.Thread(target=self.check_idle_workers)
        ]

        self.__is_running = True

    # @logger
    def add_background_thread(self, thread: threading.Thread):
        self.__background_threads.append(thread)

    @logger
    def add_task(self, task):
        self.__event_submit_packet.set()
        self.__to_be_solved.append(task)

    # @logger
    def _create_worker(self) -> AbstractWorker:
        chosen_worker = None
        if self.__worker_type == WorkerType.SERVER_WORKER:
            chosen_worker = ServerWorker(self._shared_in_working, self)
        elif self.__worker_type == WorkerType.CLIENT_WORKER:
            chosen_worker = ClientWorker(self._shared_in_working, self)

        self.__workers.append(chosen_worker)

        logger.log(f"{self.name} created a new worker {chosen_worker.name}")

        chosen_worker.start()

        return chosen_worker

    # @logger
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
                    logger.log(self.__workers)

            self.__event_check_idle.clear()

    @logger
    def analise_task(self):
        while True:
            self.__event_submit_packet.wait()

            if not self.__is_running:
                break

            packet: CoapPacket = self.__to_be_solved.pop(0)
            in_working = (packet.token, packet.sender_ip_port)
            if (not CoapTransactionsPool().has_transaction(packet.token, packet.message_id) and
                    in_working not in self._shared_in_working):
                self._shared_in_working.append(in_working)
                self._choose_worker().submit_task(packet)

                # When a content response is received, the initial request may not have received the
                # acknowledgment, but it's clear that the client/server got the request.
                # The initial transaction related to the request must be finished.
                if CoapCodeFormat.is_success(packet.code):
                    if packet.options.get(CoapOptionDelta.BLOCK2.value):
                        # now based on the block_id, message_id we can search for parent transaction
                        # that waits for an ACk with the formula:<parent_t_msg_id=task.msg_id-block_id-1>
                        block2 = packet.options.get(CoapOptionDelta.BLOCK2.value)
                        block_id = CoapPacket.decode_option_block(block2)["NUM"]
                        parent_msg_id = packet.message_id - block_id - 1
                    else:
                        # response may come in one piece with no block2 option
                        parent_msg_id = packet.message_id - 1

                    transaction = CoapTransactionsPool().get_transaction(packet.token, parent_msg_id)
                    if transaction:
                        transaction.finish_transaction()
            else:
                logger.log(f"{self.name} Packet duplicated: \n {packet.__repr__()}")

            self.__event_submit_packet.clear()

    @logger
    def listen(self):
        for thread in self.__background_threads:
            thread.start()

        while self.__is_running:
            try:
                active_socket, _, _ = select([self._socket], [], [], 0.01)

                if active_socket:
                    data, address = self._socket.recvfrom(1152)
                    packet = CoapPacket.decode(data, address, self._socket)
                    # verifying the integrity of the packet
                    if CoapWorkerPool.__verify_format(packet):

                        match packet.message_type:

                            case CoapType.CON.value:
                                if CoapCodeFormat.is_method(packet.code):  # request -> EMPTY ACK & PROCES REQUEST
                                    val = random.choice([1, 2])
                                    logger.log(val)
                                    if val == 0:
                                        logger.log(f"Not ACK: -> {packet}")
                                    else:
                                        ack = CoapTemplates.EMPTY_ACK.value_with(packet.token, packet.message_id)
                                        self._socket.sendto(ack.encode(), packet.sender_ip_port)
                                    self.add_task(packet)
                                else:  # content -> SUCCESS ACK
                                    val = random.choice([1, 2,3, 4])
                                    if val == 0:
                                        logger.log(f"Not ACK: -> {packet}")
                                    else:
                                        ack = CoapTemplates.SUCCESS_ACK.value_with(packet.token, packet.message_id)
                                        self._socket.sendto(ack.encode(), packet.sender_ip_port)
                                        self.add_task(packet)

                            case CoapType.ACK.value:
                                if CoapTransactionsPool().has_transaction(packet.token, packet.message_id):
                                    CoapTransactionsPool().get_transaction(packet.token,
                                                                           packet.message_id).finish_transaction()

                            case CoapType.RST.value:
                                CoapTransactionsPool().finish_all_transactions(packet.token)

                            case _:
                                pass
                    else:
                        logger.log(f"{self.name} Invalid coap format: \n {packet.__repr__()}")

                        invalid_format = CoapTemplates.NON_COAP_FORMAT.value_with(packet.token, packet.message_id)
                        invalid_format.code = CoapCodeFormat.SERVER_ERROR_INTERNAL_SERVER_ERROR.value()

                        self._socket.sendto(invalid_format.encode(), packet.sender_ip_port)

                self.__event_check_idle.set()
            except KeyboardInterrupt as e:
                # Wake up threads to finish their tasks
                self.__is_running = False
                self.__event_check_idle.set()
                self.__event_submit_packet.set()

        for worker in self.__workers:
            worker.stop()

        for thread in self.__background_threads:
            thread.join()
