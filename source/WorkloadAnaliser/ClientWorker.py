from source.Logger.Logger import logger
from source.WorkloadAnaliser.CustomThread import CustomThread


class ClientWorker(CustomThread):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ClientWorker[{self.name}]"

    @logger
    def _solve_task(self):
        pass
