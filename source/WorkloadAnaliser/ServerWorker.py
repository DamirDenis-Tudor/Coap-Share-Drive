from select import select
from time import sleep

from source.Logger.Logger import logger
from source.PacketManager.Packet import Packet
from source.WorkloadAnaliser.CustomThread import CustomThread


class ServerWorker(CustomThread):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ServerWorker[{self.name}]"

    @logger
    def _solve_task(self):
        logger.log(f"${self.name}Solving the task {self._task.__repr__()}")

        self._task.payload = "Vezi ca esti prost"

        logger.log("Simulating working time... Sleep for 1 sec")
        sleep(1)

        self._task.socket.sendto(Packet.encode(self._task.to_dict()), self._task.extern_ip)
        logger.log(f"${self.name} Task respose ok.")

        in_working = (self._task.token, self._task.extern_ip)
        self._shared_in_working.remove(in_working)
