from abc import ABC, abstractmethod
from enum import Enum, auto
from multiprocessing import Queue
from threading import Thread, Event

from source.Packet.CoapPacket import CoapPacket
from source.Utilities.CustomQueue import CustomQueue
from source.Utilities.Logger import logger
from source.Utilities.Timer import Timer


class WorkerType(Enum):
    SERVER_WORKER = auto(),
    CLIENT_WORKER = auto()


class AbstractWorker(Thread, ABC):
    def __init__(self, owner):
        super().__init__()

        self.__is_running = True

        self._request_queue = CustomQueue()
        self._task = CoapPacket()
        self._owner = owner
        self._heavy_work = False

        self._timer = Timer()
        self._timer.reset()

    def get_queue_size(self):
        return self._request_queue.size()

    def get_idle_time(self):
        return self._timer.elapsed_time()

    # @logger
    def run(self):
        while self.__is_running:
            task:CoapPacket = self._request_queue.get()
            if not self.__is_running:
                break

            self._timer.reset()

            self._solve_task(task)

            self._owner.remove_short_term_work(
                task.short_term_work_id()
            )

    # @logger
    def stop(self):
        self.__is_running = False
        self.submit_task(CoapPacket())
        self.join()

    # @logger
    def submit_task(self, packet: CoapPacket):
        self._request_queue.put(packet)

    def is_heavily_loaded(self):
        return self._heavy_work

    @abstractmethod
    def _solve_task(self, task: CoapPacket):
        pass
