from source.Logger.Logger import logger
from source.Packet.CoapPacket import CoapPacket
from source.Workload.Core.AbstractWorker import CustomThread
from source.Workload.ServerWorker import ServerWorker


class WorkerPool(CustomThread):
    def __init__(self):
        super().__init__([])
        self.name = f"SeverPool[{self.name}]"

        self.__workers: list[CustomThread] = []
        self.__in_working: list[int] = []

        self.__max_queue_size = 5
        self.__allowed_idle_time = 15

    def __create_worker(self):
        chosen_worker = ServerWorker(self._shared_in_working)
        self.__workers.append(chosen_worker)

        logger.log(f"{self.name} created a new worker {chosen_worker.name}")

        chosen_worker.start()

        return chosen_worker

    def __choose_worker(self):
        available_workers = filter(lambda worker: worker.get_queue_size() < self.__max_queue_size, self.__workers)
        chosen_worker = min(available_workers, default=None, key=lambda x: x.get_queue_size())

        if not chosen_worker:
            return self.__create_worker()

        return chosen_worker

    def _solve_task(self):
        in_working = (self._task.token, self._task.sender_ip_port)
        if in_working not in self._shared_in_working:
            self._shared_in_working.append(in_working)
            self.__choose_worker().submit_task(self._task)
        else:
            logger.log(f"{self.name} Packet duplicated {self._task.__repr__()}")
            self._current_task = CoapPacket()

    def check_idle_workers(self):
        workers_list_modified = False
        for worker in self.__workers:
            if worker.get_idle_time() > self.__allowed_idle_time and len(self.__workers) > 1:
                self.__workers.remove(worker)
                worker.stop()
                workers_list_modified = True
        if workers_list_modified:
            logger.log(self.__workers)
