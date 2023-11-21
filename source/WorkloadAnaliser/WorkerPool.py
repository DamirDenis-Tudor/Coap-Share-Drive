from source.Logger.Logger import logger
from source.Timer.Timer import Timer
from source.WorkloadAnaliser.CustomThread import CustomThread
from source.WorkloadAnaliser.Worker import Worker


class WorkerPool(CustomThread):
    def __init__(self):
        super().__init__()
        self.name = f"Pool[{self.name}]"

        self.__workers: list[Worker] = []
        self.__max_queue_size = 10
        self.__allowed_idle_time = 15

    @logger
    def __create_worker(self):
        new_worker = Worker()
        self.__workers.append(new_worker)
        new_worker.start()

        return new_worker

    def __choose_worker(self):
        available_workers = filter(lambda worker: worker.get_queue_size() < self.__max_queue_size, self.__workers)
        chosen_worker = min(available_workers, default=None, key=lambda x: x.get_queue_size())
        if chosen_worker:
            return chosen_worker
        return self.__create_worker()

    @logger
    def _solve_task(self):
        while self._request_queue:
            self.__choose_worker().submit_task(self._request_queue.pop(0), self._socket)

    def check_idle_workers(self):
        workers_list_modified = False
        for worker in self.__workers:
            if worker.get_idle_time() > self.__allowed_idle_time and len(self.__workers) > 1:
                self.__workers.remove(worker)
                worker.stop()
                workers_list_modified = True
        if workers_list_modified:
            logger.log(self.__workers)

