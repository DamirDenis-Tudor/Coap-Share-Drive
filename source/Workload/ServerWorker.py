import json

from source.Logger.Logger import logger
from source.Workload.Core.AbstractWorker import CustomThread
from source.Workload.Core.Assembler import Assembler


class ServerWorker(CustomThread):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ServerWorker[{self.name}]"
        self._file_worker = Assembler()

    @logger
    def _solve_task(self):
        task_payload = json.loads(self._task.payload.decode('utf-8'))

        print(task_payload)

        in_working = (self._task.token, self._task.sender_ip_port)
        self._shared_in_working.remove(in_working)
