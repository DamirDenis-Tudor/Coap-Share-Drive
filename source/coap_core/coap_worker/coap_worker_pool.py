import queue
import sys
import threading
import time
from abc import ABC
from select import select
from socket import socket

from source.coap_core.coap_packet.coap_config import CoapType, CoapCodeFormat, CoapOptionDelta
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_resource.resource import Resource
from source.coap_core.coap_resource.resource_manager import ResourceManager
from source.coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from source.coap_core.coap_utilities.coap_logger import logger, LogColor
from source.coap_core.coap_worker.coap_worker import CoapWorker


class CoapWorkerPool(ABC):
    CURRENT_TOKEN = -1

    @staticmethod
    def __gen_token() -> bytes:
        CoapWorkerPool.CURRENT_TOKEN += 1
        CoapWorkerPool.CURRENT_TOKEN = CoapWorkerPool.CURRENT_TOKEN
        return int(CoapWorkerPool.CURRENT_TOKEN).to_bytes()

    @staticmethod
    def __verify_format(task) -> bool:
        if (task.version != 1
                or not CoapType.is_valid(task.message_type)
                or not CoapCodeFormat.is_valid(task.code)
                or not CoapOptionDelta.is_valid(task.options)):
            return False

        return True

    def __init__(self, skt: socket, resource: Resource, receive_queue=None):
        self.name = f"WorkerPoll"
        self.__is_running = True
        self._short_term_shared_work = {}
        self._long_term_shared_work = {}
        self._failed_requests = {}

        self._socket = skt

        self.__workers: list[CoapWorker] = []

        self.__valid_coap_packets = queue.Queue()
        if receive_queue:
            self._received_packets = receive_queue
        else:
            self._received_packets = queue.Queue()

        self.__idle_event = threading.Event()
        self.__transaction_event = threading.Event()

        self.__stop_event = threading.Event()

        self.__max_queue_size = 20000
        self.__allowed_idle_time = 60

        self.__background_threads: list[threading.Thread] = [
            threading.Thread(target=self.__coap_format_filter),
            threading.Thread(target=self.__deduplication_filter),
            threading.Thread(target=self.__handle_transactions),
            threading.Thread(target=self.__handle_workers),
            threading.Thread(target=self.__stop_safety)
        ]

        self.__transaction_pool = CoapTransactionPool()
        ResourceManager().add_default_resource(resource)

    def _add_background_thread(self, thread: threading.Thread):
        self.__background_threads.append(thread)

    def remove_short_term_work(self, work_data: tuple):
        if work_data in self._short_term_shared_work:
            self._short_term_shared_work.pop(work_data)

    def remove_long_term_work(self, work_data: tuple):
        if work_data in self._long_term_shared_work:
            self._long_term_shared_work.pop(work_data)

    @logger
    def __create_worker(self) -> CoapWorker:
        chosen_worker = CoapWorker(self)
        chosen_worker.start()

        self.__workers.append(chosen_worker)

        return chosen_worker

    def __choose_worker(self) -> CoapWorker:
        light_loaded_workers = filter(lambda worker: not worker.is_heavily_loaded(), self.__workers)
        available_workers = filter(lambda worker: worker.get_queue_size() < self.__max_queue_size, light_loaded_workers)
        chosen_worker = min(available_workers, default=None, key=lambda x: x.get_queue_size())

        if not chosen_worker:
            new_worker = self.__create_worker()
            return new_worker

        return chosen_worker

    @logger
    def __handle_transactions(self):
        while self.__is_running:
            self.__transaction_event.wait(timeout=1)
            CoapTransactionPool().solve_transactions()
            self.__transaction_event.clear()

    @logger
    def __handle_workers(self):
        while self.__is_running:
            self.__idle_event.wait(timeout=60)
            for worker in self.__workers:
                if worker.get_idle_time() > self.__allowed_idle_time and len(self.__workers) > 1:
                    self.__workers.remove(worker)
                    worker.stop()
            self.__idle_event.clear()

    @logger
    def __deduplication_filter(self):
        while self.__is_running:
            try:
                packet: CoapPacket = self.__valid_coap_packets.get()

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

                    self.__choose_worker().submit_task(packet)

                    if long_term_work:
                        self._long_term_shared_work[long_term_work] = time.time()
                    else:
                        self._short_term_shared_work[work] = time.time()
                else:
                    logger.debug(f"{self.name} Packet duplicated: \n {packet.__repr__()}")
            except Exception as e:
                logger.debug(e)

    @logger
    def __coap_format_filter(self):

        while self.__is_running:
            data: tuple[bytes, tuple] = self._received_packets.get()
            packet = CoapPacket.decode(data[0], data[1], self._socket)
            # verifying the integrity of the packet
            if CoapWorkerPool.__verify_format(packet):
                match packet.message_type:

                    case CoapType.CON.value:
                        if not self.__transaction_pool.is_overall_transaction_failed(packet):
                            if CoapCodeFormat.is_method(packet.code):  # GET PUT POST DELETE FETCH
                                ack = CoapTemplates.EMPTY_ACK.value_with(packet.token, packet.message_id)
                            elif packet.code == CoapCodeFormat.SUCCESS_CONTENT.value():  # CONTENT
                                ack = CoapTemplates.SUCCESS_VALID_ACK.value_with(packet.token, packet.message_id)
                                block_id = packet.get_block_id()
                                ack.payload = str(block_id)
                            else:
                                ack = CoapTemplates.EMPTY_ACK.value_with(packet.token, packet.message_id)

                            self._socket.sendto(ack.encode(), packet.sender_ip_port)
                            self.__valid_coap_packets.put(packet)

                    case CoapType.ACK.value:
                        CoapTransactionPool().finish_transaction(packet)

                    case CoapType.RST.value:
                        self._failed_requests[packet.general_work_id()] = time.time()
                        self.__transaction_pool.set_overall_transaction_failure(packet)
                        self.__transaction_pool.finish_overall_transaction(packet)
                        logger.log(f"! Warning: {CoapCodeFormat.get_field_name(packet.code)}", LogColor.YELLOW)

                    case _:
                        pass
            else:
                logger.debug(f"{self.name} Invalid coap format: \n {packet.__repr__()}")

                invalid_format = CoapTemplates.NON_COAP_FORMAT.value_with(packet.token, packet.message_id)
                invalid_format.code = CoapCodeFormat.SERVER_ERROR_INTERNAL_SERVER_ERROR.value()

                self._socket.sendto(invalid_format.encode(), packet.sender_ip_port)

    def listen(self):
        self.start()

        while self.__is_running:
            try:
                active_socket, _, _ = select([self._socket], [], [], 1)

                if active_socket:
                    data, address = self._socket.recvfrom(1152)
                    self._received_packets.put((data, address))
            except Exception:
                pass

        self.stop()

    def _handle_internal_task(self, task: CoapPacket):
        # give unique token
        task.token = CoapWorkerPool.__gen_token()
        if task.needs_internal_computation:
            self.__create_worker().submit_task(task)
        self.__transaction_pool.add_transaction(task)

    def start(self):
        for thread in self.__background_threads:
            thread.start()

    def stop(self):
        self.__stop_event.set()

    @logger
    def __stop_safety(self):
        self.__stop_event.wait()  # Set the event to signal threads to stop

        self.__is_running = False

        for worker in self.__workers:
            if worker != threading.current_thread():
                worker.stop()

        for worker in self.__workers:
            if worker != threading.current_thread():
                worker.join()

        self._socket.close()

        sys.exit(0)
