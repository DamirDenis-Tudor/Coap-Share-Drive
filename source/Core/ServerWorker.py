from time import sleep

from source.Utilities.Logger import logger
from source.Core.AbstractWorker import AbstractWorker


class ServerWorker(AbstractWorker):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ServerWorker[{self.name}]"

    @logger
    def _solve_task(self):
        logger.log(f"{self.name} Solving task {self._task.__repr__()}")
        sleep(10)
