from abc import ABC, abstractmethod
from enum import Enum, auto
from multiprocessing import Queue
from threading import Thread, Event

from source.Packet.CoapPacket import CoapPacket
from source.Utilities.Timer import Timer


class WorkerType(Enum):
    SERVER_WORKER = auto(),
    CLIENT_WORKER = auto()


class AbstractWorker(Thread, ABC):
    def __init__(self, owner):
        super().__init__()

        self.__is_running = True

        self._request_queue = Queue()
        self._task = CoapPacket()
        self._owner = owner

        self._timer = Timer()
        self._timer.reset()

    def get_queue_size(self):
        return self._request_queue.qsize()

    def get_idle_time(self):
        return self._timer.elapsed_time()

    # @logger
    def run(self):
        while self.__is_running:

            self._task = self._request_queue.get()
            self._timer.reset()
            if not self.__is_running:
                break

            self._solve_task()
            self._finish_task()

    # @logger
    def stop(self):
        self.__is_running = False
        self.submit_task(CoapPacket())
        self.join()

    # @logger
    def submit_task(self, packet: CoapPacket):
        self._request_queue.put(packet)

    # @logger
    def _finish_task(self):
        in_working = (self._task.token, self._task.message_id, self._task.sender_ip_port)
        self._owner.remove_short_term_work(in_working)

    @abstractmethod
    def _solve_task(self):
        pass
