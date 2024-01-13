from contextlib import contextmanager
from queue import Queue
from threading import Thread

from coap_core.coap_packet.coap_config import CoapOptionDelta, CoapCodeFormat
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_packet.coap_templates import CoapTemplates
from coap_core.coap_resource.resource_manager import ResourceManager
from coap_core.coap_utilities.coap_logger import logger
from coap_core.coap_utilities.coap_timer import CoapTimer


class CoapWorker(Thread):
    """
    Represents a worker thread for handling CoAP tasks asynchronously.
    """

    def __init__(self, shared_work: dict):
        """
        Initializes the CoapWorker instance.

        Args:
            shared_work (dict): A dictionary for shared work data among threads.
        """
        super().__init__()

        # Rename the thread for better identification
        self.name = self.name.replace("Thread", "CoapWorkerThread")

        self.__is_running = True
        self._heavy_work = False

        # Queue for managing CoAP tasks
        self._request_queue = Queue()

        self._shared_work = shared_work

        # Timer for tracking idle time
        self._timer = CoapTimer()
        self._timer.reset()

    def get_queue_size(self):
        """
        Gets the current size of the CoAP task queue.

        Returns:
            int: The size of the task queue.
        """
        return self._request_queue.qsize()

    def get_idle_time(self):
        """
        Gets the elapsed time since the last task was processed.

        Returns:
            float: The elapsed time in seconds.
        """
        return self._timer.elapsed_time()

    def run(self):
        """
        The main execution loop of the CoapWorker thread.
        """
        while self.__is_running:
            task: CoapPacket = self._request_queue.get()
            if not self.__is_running:
                break

            self._timer.reset()

            self._solve_task(task)

            if task.work_id() in self._shared_work:
                self._shared_work.pop(task.work_id())

    def stop(self):
        """
        Stops the CoapWorker thread.

        Notes:
            Stops the thread, submits a dummy task, and waits for the thread to join.
        """
        self.__is_running = False
        self.submit_task(CoapPacket())
        self.join()

    def submit_task(self, packet: CoapPacket):
        """
        Submits a CoAP task to the worker thread for processing.

        Args:
            packet (CoapPacket): The CoAP packet representing the task.
        """
        self._request_queue.put(packet)

    @contextmanager
    def heavy_work(self):
        """
        Context manager for marking a task as heavy work.

        Notes:
            The worker will be marked as heavily loaded within the context.
        """
        self._heavy_work = True
        yield
        self._heavy_work = False

    def is_heavily_loaded(self):
        """
        Checks if the worker is currently handling a heavy workload.

        Returns:
            bool: True if heavily loaded; False otherwise.
        """
        return self._heavy_work

    def _solve_task(self, task: CoapPacket):
        """
        Processes a CoAP task and delegates to the appropriate resource handler.

        Args:
            task (CoapPacket): The CoAP packet representing the task.
        """
        if not task.options.get(CoapOptionDelta.URI_PATH.value) and CoapCodeFormat.is_method(task.code):
            # Handle the case where URI PATH is not specified for a method
            logger.log("URI PATH not specified")
            reset = CoapTemplates.BAD_REQUEST.value_with(task.token, task.message_id)
            task.skt.sendto(reset.encode(), task.sender_ip_port)
            return

        # Obtain a resource based on URI PATH
        resource = ResourceManager().get_default_resource()
        if not resource:
            resource = ResourceManager().get_resource(task.options[CoapOptionDelta.URI_PATH.value].split("/")[0])

        if not resource:
            # Handle the case where URI PATH does not exist
            logger.log("URI PATH does not exist")
            reset = CoapTemplates.BAD_REQUEST.value_with(task.token, task.message_id)
            task.skt.sendto(reset.encode(), task.sender_ip_port)
            return

        if task.needs_internal_computation:
            # Handle internal computation
            resource.handle_internal(task)
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
                resource.handle_response(task)

