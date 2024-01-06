from source.coap_core.coap_packet.coap_config import CoapOptionDelta, CoapCodeFormat
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_resource.resource import Resource
from source.coap_core.coap_utilities.coap_logger import logger
from source.share_drive_helpers.file_handler import FileHandler


class ServerResource(Resource):
    def __init__(self, path: str):
        super().__init__(path)
        self.__file_handler = FileHandler()

    @logger
    def handle_get(self, request):
        if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                request.options.get(CoapOptionDelta.BLOCK1.value)):
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
            if not FileHandler.file_exists(path) and not FileHandler.folder_exists(path):
                invalid_request = CoapTemplates.NOT_FOUND.value_with(request.token, request.message_id)
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
            else:
                self.__file_handler.split_on_bytes_and_send(request, path)
        else:
            invalid_request = CoapTemplates.BAD_REQUEST.value()
            invalid_request.token = request.token
            request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_post(self, request):
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_put(self, request):
        if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                request.options.get(CoapOptionDelta.BLOCK1.value)):
            relative_path = '/' + request.options[CoapOptionDelta.LOCATION_PATH.value].split('/')[-1]
            if (FileHandler.file_exists(self.get_path() + relative_path)
                    or FileHandler.folder_exists(self.get_path() + relative_path)):
                invalid_request = CoapTemplates.CONFLICT.value_with(request.token, request.message_id)
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        else:
            invalid_request = CoapTemplates.BAD_REQUEST.value_with(request.token, request.message_id)
            request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_delete(self, request):
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_fetch(self, request: CoapPacket):
        self.__file_handler.split_on_paths_and_send(request, self.get_path(), self.get_name())

    def internal_handling(self, request: CoapPacket):
        pass

    def non_method(self, request: CoapPacket):
        if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
            if CoapOptionDelta.LOCATION_PATH.value in request.options:  # response of upload
                path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
                self.__file_handler.handle_packets(request, path)
