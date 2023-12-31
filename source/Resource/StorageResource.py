from time import sleep

from source.File.FileHandler import FileHandler
from source.Packet.CoapConfig import CoapOptionDelta
from source.Packet.CoapTemplates import CoapTemplates
from source.Resource.Resource import Resource
from source.Utilities.Logger import logger


class StorageResource(Resource):
    def __init__(self, path: str):
        super().__init__(path)
        self.__file_handler = FileHandler()

    @logger
    def get(self, request):
        sleep(5)
        if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                request.options.get(CoapOptionDelta.BLOCK1.value)):
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
            self.__file_handler.get_sender()(request, path)
        else:
            invalid_request = CoapTemplates.BAD_REQUEST.value()
            invalid_request.token = request.token
            request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def post(self, request):
        pass

    def put(self, request):
        pass

    def delete(self, request):
        pass
