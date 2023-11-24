import socket

from abc import ABC, abstractmethod
from source.Logger.Logger import logger
from threading import Thread, Event

from source.PacketManager.Packet import Packet
from source.Timer.Timer import Timer


class CustomThread(Thread, ABC):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__()

        self.__is_running = True
        self.__task_event = Event()

        self._request_queue: list[Packet] = []
        self._shared_in_working = shared_in_working
        self._task = Packet.empty_packet()

        self._timer = Timer()
        self._timer.reset()

    def get_queue_size(self):
        return len(self._request_queue)

    def get_idle_time(self):
        return self._timer.elapsed_time()

    @logger
    def run(self):
        while self.__is_running:
            self.__task_event.wait()

            while self._request_queue:
                self._timer.reset()
                self._task = self._request_queue.pop(0)
                self._solve_task()

            self.__task_event.clear()

            if not self.__is_running:
                break

    @logger
    def stop(self):
        self.__is_running = False
        self.__task_event.set()
        self.join()

    def submit_task(self, packet: Packet):
        self._request_queue.append(packet)
        self.__task_event.set()

    @abstractmethod
    def _solve_task(self):
        pass
