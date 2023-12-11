from source.Packet.CoapTransaction import CoapTransactionsPool
from source.Utilities.Logger import logger
from source.Core.AbstractWorker import AbstractWorker


class ClientWorker(AbstractWorker):
    def __init__(self, shared_in_working: list[tuple[int, str]], owner):
        super().__init__(shared_in_working)
        self.name = f"ClientWorker[{self.name}]"
        self.__owner = owner

    def _solve_task(self):
        pass
        #        logger.log(f"{self.name} Solving task: \n {self._task}")
