from time import sleep

from source.Packet.CoapConfig import CoapOptionDelta, CoapCodeFormat
from source.Resource.StorageResource import StorageResource
from source.Utilities.Logger import logger
from source.Core.AbstractWorker import AbstractWorker


class ServerWorker(AbstractWorker):
    def __init__(self, owner):
        super().__init__(owner)
        self.name = f"ServerWorker[{self.name}]"

    @logger
    def _solve_task(self):
        task = self._task

        if CoapCodeFormat.is_method(task.code):  # request
            """
                In this case it's clear that a request must be solved by 
                forwarding to a specific resource
            """
            if task.options.get(CoapOptionDelta.URI_PATH.value):
                resource = self._owner.get_resource(task.options[CoapOptionDelta.URI_PATH.value])
                if resource:
                    if task.code == CoapCodeFormat.GET.value():
                        resource.get(task)
                    elif task.code == CoapCodeFormat.POST.value():
                        resource.post(task)
                    elif task.code == CoapCodeFormat.PUT.value():
                        resource.put(task)
                    elif task.code == CoapCodeFormat.DELETE.value():
                        resource.delete(task)
                    elif task.code == CoapCodeFormat.FETCH.value():
                        resource.get(task)
                else:
                    logger.log(f"{self.name} Resource does not exists \n {task}")
            else:
                logger.log(f"{self.name} Resource not specified \n {task}")
