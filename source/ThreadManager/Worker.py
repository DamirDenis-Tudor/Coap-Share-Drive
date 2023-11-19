from socket import socket

from source.Logger.Logger import logger
from source.PacketManager.Packet import Packet
from source.ThreadManager.CustomThread import CustomThread


class Worker(CustomThread):
    def __init__(self):
        super().__init__()

    @logger
    def _solve_task(self):
        if not self._current_packet.is_empty():
            logger.log(f"Solving the packet {self._current_packet.__repr__()}")
            # self._current_packet = Packet.empty_packet()
            return self._current_packet
