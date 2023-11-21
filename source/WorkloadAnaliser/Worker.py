from time import sleep

from source.Logger.Logger import logger
from source.PacketManager.Packet import Packet
from source.WorkloadAnaliser.CustomThread import CustomThread


class Worker(CustomThread):
    def __init__(self):
        super().__init__()
        self.name = f"Worker[{self.name}]"

    def get_queue_size(self):
        return len(self._request_queue)

    def get_idle_time(self):
        return self._timer.elapsed_time()

    @logger
    def _solve_task(self):
        while self._request_queue:
            self._timer.reset()
            packet = self._request_queue.pop(0)
            logger.log(f"{self.name} Solving the packet {packet.__repr__()}")
            packet.payload = "Ti am rapuns"
            print(packet)
            print(packet.to_dict())
            self._socket.sendto(Packet.encode(packet.to_dict()), packet.extern_ip)

        logger.log(f"{self.name} is free.")
