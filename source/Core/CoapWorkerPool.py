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
from source.Utilities.Logger import logger
from threading import Event

from source.Packet.CoapPacket import CoapPacket


class CoapWorkerPool(ABC):
    @staticmethod
    def __verify_format(task):
        if (task.version != 1
                or not CoapType.is_valid(task.message_type)
                or not CoapCodeFormat.is_valid(task.code)
                or not CoapOptionDelta.is_valid(task.options)):
            return False

        return True

    def __init__(self, worker_type: WorkerType, ip_address: str, port: int, threads=None):
        if threads is None:
            threads = []

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

        self.__threads: list[threading.Thread] = threads
        self.__threads += [
            threading.Thread(target=self.analise_task),
            threading.Thread(target=self.check_idle_workers)
        ]

        self.__is_running = True

    @logger
    def _create_worker(self):
        chosen_worker = None
        if self.__worker_type == WorkerType.SERVER_WORKER:
            chosen_worker = ServerWorker(self._shared_in_working)
        elif self.__worker_type == WorkerType.CLIENT_WORKER:
            chosen_worker = ClientWorker(self._shared_in_working)

        self.__workers.append(chosen_worker)

        logger.log(f"{self.name} created a new worker {chosen_worker.name}")

        chosen_worker.start()

        return chosen_worker

    @logger
    def _choose_worker(self) -> AbstractWorker:
        available_workers = filter(lambda worker: worker.get_queue_size() < self.__max_queue_size, self.__workers)
        chosen_worker = min(available_workers, default=None, key=lambda x: x.get_queue_size())

        if not chosen_worker:
            new_worker = self._create_worker()
            return new_worker

        return chosen_worker

    @logger
    def add_task(self, task):
        self.__event_submit_packet.set()
        self.__to_be_solved.append(task)

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

            task = self.__to_be_solved.pop(0)
            in_working = (task.token, task.sender_ip_port)
            if in_working not in self._shared_in_working:
                self._shared_in_working.append(in_working)
                self._choose_worker().submit_task(task)
            else:
                logger.log(f"{self.name} Packet duplicated {task.__repr__()}")

            self.__event_submit_packet.clear()

    @logger
    def listen(self):
        for thread in self.__threads:
            thread.start()

        while self.__is_running:
            try:
                active_socket, _, _ = select([self._socket], [], [], 0.01)

                if active_socket:
                    data, address = self._socket.recvfrom(1152)
                    packet = CoapPacket.decode(data, address, self._socket)
                    if CoapWorkerPool.__verify_format(packet):
                        self.add_task(CoapPacket.decode(data, address, self._socket))
                    else:
                        logger.log(f"{self.name} Invalid coap format {packet.__repr__()}")

                        invalid_format: CoapPacket = CoapTemplates.NON_COAP_FORMAT.value()
                        invalid_format.message_id = packet.message_id
                        invalid_format.token = packet.token
                        invalid_format.code = CoapCodeFormat.SERVER_ERROR_INTERNAL_SERVER_ERROR.value()

                        self._socket.sendto(invalid_format.encode(), packet.sender_ip_port)

                self.__event_check_idle.set()
            except KeyboardInterrupt as e:
                self.__is_running = False
                self.__event_check_idle.set()
                self.__event_submit_packet.set()

        for worker in self.__workers:
            worker.stop()

        for thread in self.__threads:
            thread.join()

