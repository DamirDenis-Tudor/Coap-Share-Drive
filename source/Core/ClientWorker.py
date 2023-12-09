from source.Utilities.Logger import logger
from source.Core.AbstractWorker import AbstractWorker


class ClientWorker(AbstractWorker):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ClientWorker[{self.name}]"

    @logger
    def _solve_task(self):

        self.finish_task()
