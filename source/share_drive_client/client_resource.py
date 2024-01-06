import threading

from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_utilities.coap_logger import logger
from source.coap_core.coap_packet.coap_config import CoapCodeFormat, CoapOptionDelta
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_resource.resource import Resource
from source.coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from source.share_drive_helpers.file_handler import FileHandler


class ClientResource(Resource):
    def __init__(self, name: str, path):
        super().__init__(name, path)
        self.__file_handler = FileHandler()

    def handle_get(self, request):
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_post(self, request):
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_put(self, request):
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_delete(self, request):
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_fetch(self, request: CoapPacket):
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def internal_handling(self, request: CoapPacket):
        path = request.options[CoapOptionDelta.LOCATION_PATH.value]
        if not FileHandler.file_exists(path) and not FileHandler.folder_exists(path):
            print("Invalid_PATH")
        else:
            while not CoapTransactionPool().is_transaction_finished(request):
                pass
            self.__file_handler.split_on_bytes_and_send(request, path)

    def non_method(self, request: CoapPacket):
        if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
            if CoapOptionDelta.LOCATION_PATH.value in request.options:
                path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
                self.__file_handler.handle_packets(request, path)
            else:
                self.__file_handler.handle_paths(request)

