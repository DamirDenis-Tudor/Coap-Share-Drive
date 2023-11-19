import socket

from abc import ABC, abstractmethod
from source.Logger.Logger import logger
from threading import Thread, Event

from source.PacketManager.Packet import Packet


class CustomThread(Thread, ABC):
    def __init__(self):
        super().__init__()

        self.__is_running = True
        self.__task_event = Event()
        self._socket = None
        self._current_packet: Packet = Packet.empty_packet()

    @logger
    def run(self):
        logger.log(f"{self.name} started.")
        while self.__is_running:
            self.__task_event.wait()
            if not self.__is_running:
                break
            self._solve_task()
            self.__task_event.clear()
        logger.log(f"{self.name} stopped.")

    @logger
    def stop(self):
        logger.log(f"Stopping {self.name}...")
        self.__is_running = False
        self.__task_event.set()  
        self.join()
        logger.log(f"{self.name} stopped successfully.")

    @logger
    def submit_task(self, packet: Packet, skt: socket):
        logger.log(f"Task submitted to {self.name}.")
        self._socket = skt
        self._current_packet = packet
        self.__task_event.set()

    @logger
    @abstractmethod
    def _solve_task(self):
        pass
