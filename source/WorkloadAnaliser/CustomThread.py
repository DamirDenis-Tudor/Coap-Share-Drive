import socket

from abc import ABC, abstractmethod
from source.Logger.Logger import logger, LogColor
from threading import Thread, Event

from source.PacketManager.Packet import Packet
from source.Timer.Timer import Timer


class CustomThread(Thread, ABC):
    def __init__(self):
        super().__init__()

        self.__is_running = True
        self.__task_event = Event()
        self._socket: socket = None
        self._request_queue: list[Packet] = []

        self._timer = Timer()
        self._timer.reset()

    def run(self):
        logger.log(f"{self.name} started.")

        while self.__is_running:
            self.__task_event.wait()
            self._solve_task()
            self.__task_event.clear()

            if not self.__is_running:
                break

    @logger
    def stop(self):
        self.__is_running = False
        self.__task_event.set()
        self.join()

        logger.log(f"{self.name} stopped successfully.")

    def submit_task(self, packet: Packet, skt: socket):

        self._socket = skt
        self._request_queue.append(packet)
        self.__task_event.set()

    @logger
    @abstractmethod
    def _solve_task(self):
        pass
