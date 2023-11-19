from source.Logger.Logger import logger
from source.ThreadManager.CustomThread import CustomThread
from source.ThreadManager.Worker import Worker


class WorkerPool(CustomThread):
    def __init__(self):
        super().__init__()
        self.name = "WorkerPool"
        self.__workers: list[Worker] = []

    @logger
    def _solve_task(self):
        logger.log("Solving the task")
        if not self.__workers:
            self.__workers.append(Worker())
            self.__workers[0].start()
        self.__workers[0].submit_task(self._current_packet, self._socket)
