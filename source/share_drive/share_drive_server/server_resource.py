from time import sleep

from source.coap_core.coap_packet.coap_config import CoapOptionDelta, CoapCodeFormat
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_resource.resource import Resource
from source.coap_core.coap_utilities.coap_logger import logger
from source.share_drive.share_drive_helpers.file_handler import FileHandler


class ServerResource(Resource):
    def __init__(self, path: str):
        super().__init__(path)
        self.__file_handler = FileHandler()

    @logger
    def handle_get(self, request):
        sleep(5)
        if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                request.options.get(CoapOptionDelta.BLOCK1.value)):
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
            self.__file_handler.get_sender()(request, path)
        else:
            invalid_request = CoapTemplates.BAD_REQUEST.value()
            invalid_request.token = request.token
            request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_post(self, request):
        pass

    def handle_put(self, request):
        if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                request.options.get(CoapOptionDelta.BLOCK1.value)):
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
            if FileHandler.file_exists(path) or FileHandler.folder_exists(path):
                invalid_request = CoapTemplates.CONFLICT.value_with(request.token, request.message_id)
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        else:
            invalid_request = CoapTemplates.BAD_REQUEST.value_with(request.token, request.message_id)
            request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_delete(self, request):
        pass

    def handle_fetch(self, request: CoapPacket):
        pass

    def non_method(self, request: CoapPacket):
        if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
            self.__file_handler.handle_packets(request, path)
