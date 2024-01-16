import queue
import sys
import threading
import time
from abc import ABC
from select import select
from socket import socket

from coap_core.coap_worker import COAP_WORKER_QUEUE_SIZE, COAP_ALLOWED_WORKER_IDLE
from coap_core.coap_packet.coap_config import CoapType, CoapCodeFormat, CoapOptionDelta, verify_format, gen_token
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_packet.coap_templates import CoapTemplates
from coap_core.coap_resource.resource import Resource
from coap_core.coap_resource.resource_manager import ResourceManager
from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from coap_core.coap_utilities.coap_logger import logger, LogColor
from coap_core.coap_worker.coap_worker import CoapWorker


class CoapWorkerPool(ABC):
    """
    Abstract class representing a pool of CoAP workers for handling incoming CoAP packets.

    CoapWorkerPool can be utilized on both the server and client sides.
    For instance, on the server side, it may be necessary to replicate the pool across multiple processes
    to handle a high volume of incoming CoAP packets.
    On the client side, users can extend this class to customize behavior for their specific use case,
    to add UI threads or other kinds of stuff.
    """

    def __init__(self, skt: socket, resource: Resource, receive_queue=None):
        """
        Initializes the CoapWorkerPool instance.

        Args:
            skt (socket): The socket for communication.
            resource (Resource): The default resource for the worker pool.
            receive_queue (Queue): Optional queue for receiving CoAP packets.
        """
        self.name = f"WorkerPoll"

        self.__is_running = True

        self._shared_work = {}
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

        self.__max_queue_size = COAP_WORKER_QUEUE_SIZE
        self.__allowed_idle_time = COAP_ALLOWED_WORKER_IDLE

        self.__background_threads: list[threading.Thread] = [
            threading.Thread(target=self.__coap_format_filter, name="PoolThread"),
            threading.Thread(target=self.__handle_transactions, name="PoolThread"),
            threading.Thread(target=self.__handle_workers, name="PoolThread")
        ]

        self.__transaction_pool = CoapTransactionPool()
        ResourceManager().add_default_resource(resource)

    def _add_background_thread(self, thread: threading.Thread):
        """
        Adds a background thread to the list of background threads.

        Args:
            thread (threading.Thread): The thread to be added.
        """
        self.__background_threads.append(thread)

    def __choose_worker(self) -> CoapWorker:
        """
        Chooses a worker to handle a CoAP packet based on task that they have and queue size.

        Returns:
            CoapWorker: The selected worker.
        """
        light_loaded_workers = filter(lambda worker: not worker.is_heavily_loaded(), self.__workers)
        available_workers = filter(lambda worker: worker.get_queue_size() < self.__max_queue_size, light_loaded_workers)
        chosen_worker = min(available_workers, default=None, key=lambda x: x.get_queue_size())

        if not chosen_worker:
            chosen_worker = CoapWorker(self._shared_work)
            chosen_worker.start()

            self.__workers.append(chosen_worker)

        return chosen_worker

    @logger
    def __handle_transactions(self):
        """
        Handles CoAP transactions in a background thread.
        """
        while self.__is_running:
            self.__transaction_event.wait(timeout=1)
            CoapTransactionPool().solve_transactions()
            self.__transaction_event.clear()

    @logger
    def __handle_workers(self):
        """
        Manages CoAP workers in a background thread.
        """
        while self.__is_running:
            self.__idle_event.wait(timeout=60)
            for worker in self.__workers:
                if worker.get_idle_time() > self.__allowed_idle_time and len(self.__workers) > 1:
                    self.__workers.remove(worker)
                    worker.stop()
            self.__idle_event.clear()

    @logger
    def __coap_format_filter(self):
        """
        Filters and processes incoming CoAP packets based on their format.

        The received packet can have the following types:
        - CON: An acknowledgment must be sent accordingly with the additional related fields.
        - NON: It is clear that no operation must be done.
        - ACK: The transaction that waited for it must be finished.
        - RST: An error occurred, and all related transactions must be stopped.
        """
        while self.__is_running:
            data: tuple[bytes, tuple] = self._received_packets.get()
            packet = CoapPacket.decode(data[0], data[1], self._socket)
            if verify_format(packet):
                match packet.message_type:
                    case CoapType.CON.value:
                        if not self.__transaction_pool.is_overall_transaction_failed(packet):
                            if CoapCodeFormat.is_method(packet.code):  # GET PUT POST DELETE FETCH
                                ack = CoapTemplates.EMPTY_ACK.value_with(
                                    packet.token, packet.message_id,
                                    self._socket,
                                    data[1]
                                )
                                if packet.get_option_code():
                                    ack.options[packet.get_option_code()] = packet.options[packet.get_option_code()]
                            elif packet.code == CoapCodeFormat.SUCCESS_CONTENT.value():  # CONTENT
                                ack = CoapTemplates.SUCCESS_CONTINUE_ACK.value_with(
                                    packet.token, packet.message_id,
                                    self._socket, data[1]
                                )
                                if packet.get_option_code():
                                    ack.options[packet.get_option_code()] = packet.options[packet.get_option_code()]
                            else:
                                ack = CoapTemplates.EMPTY_ACK.value_with(
                                    packet.token, packet.message_id,
                                    self._socket, data[1]
                                )
                            ack.skt = self._socket
                            ack.sender_ip_port = packet.sender_ip_port
                            ack.send()

                            if packet.work_id() not in self._shared_work:
                                self.__choose_worker().submit_task(packet)
                                self._shared_work[packet.work_id()] = time.time()

                    case CoapType.NON.value:
                        if packet.work_id() not in self._shared_work:
                            self.__choose_worker().submit_task(packet)
                            self._shared_work[packet.work_id()] = time.time()

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

                invalid_format = CoapTemplates.INTERNAL_ERROR.value_with(
                    packet.token, packet.message_id,
                    self._socket, data[1]
                )
                invalid_format.code = CoapCodeFormat.SERVER_ERROR_INTERNAL_SERVER_ERROR.value()
                invalid_format.send()
                self._socket.sendto(invalid_format.encode(), packet.sender_ip_port)

    @logger
    def listen(self):
        """
        Listens for incoming CoAP packets and starts processing in the background.
        """
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
        """
        Handles internal CoAP tasks, distributing them to workers.

        Args:
            task (CoapPacket): The internal CoAP task.
        """
        task.token = gen_token()
        if task.needs_internal_computation:
            chosen_worker = CoapWorker(self._shared_work)
            chosen_worker.start()
            chosen_worker.submit_task(task)

            self.__workers.append(chosen_worker)
        self._shared_work[task.work_id()] = time.time()
        self.__transaction_pool.add_transaction(task)

    def start(self):
        """
        Starts the background threads for handling CoAP packets.
        """
        for thread in self.__background_threads:
            thread.start()

    def stop(self):
        """
        Stops the CoapWorkerPool and its associated threads.
        """
        self.__is_running = False

        for worker in self.__workers:
            if worker != threading.current_thread():
                worker.stop()

        for worker in self.__workers:
            if worker != threading.current_thread():
                worker.join()

        self._socket.close()

        sys.exit(0)
