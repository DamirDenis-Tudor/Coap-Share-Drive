import queue

from contextlib import contextmanager
from threading import Thread

from source.coap_core.coap_packet.coap_config import CoapOptionDelta, CoapCodeFormat
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_resource.resource_manager import ResourceManager
from source.coap_core.coap_utilities.coap_logger import logger
from source.coap_core.coap_utilities.coap_timer import CoapTimer


class CoapWorker(Thread, ):
    def __init__(self, shared_work: dict):
        super().__init__()

        self.name = self.name.replace("Thread", "CoapWorkerThread")

        self.__is_running = True
        self._heavy_work = False

        self._request_queue = queue.Queue()

        self._shared_work = shared_work

        self._timer = CoapTimer()
        self._timer.reset()

    def get_queue_size(self):
        return self._request_queue.qsize()

    def get_idle_time(self):
        return self._timer.elapsed_time()

    # @logger
    def run(self):
        while self.__is_running:
            task: CoapPacket = self._request_queue.get()
            if not self.__is_running:
                break

            self._timer.reset()

            self._solve_task(task)

            self._shared_work.pop(task.work_id())

    # @logger
    def stop(self):
        self.__is_running = False
        self.submit_task(CoapPacket())
        self.join()

    # @logger
    def submit_task(self, packet: CoapPacket):
        self._request_queue.put(packet)

    @contextmanager
    def heavy_work(self):
        self._heavy_work = True
        yield
        self._heavy_work = False

    def is_heavily_loaded(self):
        return self._heavy_work

    def _solve_task(self, task: CoapPacket):

        if not task.options.get(CoapOptionDelta.URI_PATH.value) and CoapCodeFormat.is_method(task.code):
            logger.log("URI PATH not specified")
            reset = CoapTemplates.BAD_REQUEST.value_with(task.token, task.message_id)
            task.skt.sendto(reset.encode(), task.sender_ip_port)
            return

        resource = ResourceManager().get_default_resource()
        if not resource:
            resource = ResourceManager().get_resource(task.options[CoapOptionDelta.URI_PATH.value].split("/")[0])

        if not resource:
            logger.log("URI PATH does not exist")
            reset = CoapTemplates.BAD_REQUEST.value_with(task.token, task.message_id)
            task.skt.sendto(reset.encode(), task.sender_ip_port)
            return

        if task.needs_internal_computation:
            resource.internal_handling(task)
        else:
            task_code = task.code
            if task_code == CoapCodeFormat.GET.value():
                with self.heavy_work():
                    resource.handle_get(task)
            elif task_code == CoapCodeFormat.PUT.value():
                with self.heavy_work():
                    resource.handle_put(task)
            elif task_code == CoapCodeFormat.POST.value():
                resource.handle_post(task)
            elif task_code == CoapCodeFormat.DELETE.value():
                resource.handle_delete(task)
            elif task_code == CoapCodeFormat.FETCH.value():
                resource.handle_fetch(task)
            else:
                resource.non_method(task)
