from source.Logger.Logger import logger
from source.Core.AbstractWorker import AbstractWorker


class ClientWorker(AbstractWorker):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ClientWorker[{self.name}]"

    @logger
    def _solve_task(self):
        # write the logic for client-side parket interpret
        in_working = (self._task.token, self._task.sender_ip_port)
        self._shared_in_working.remove(in_working)
