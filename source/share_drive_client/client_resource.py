import threading

from share_drive_helpers.file_assembler import FileAssembler
from share_drive_helpers.file_spliter import FileSpliter
from coap_core.coap_packet.coap_templates import CoapTemplates
from coap_core.coap_utilities.coap_logger import logger
from coap_core.coap_packet.coap_config import CoapCodeFormat, CoapOptionDelta
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_resource.resource import Resource
from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool


class ClientResource(Resource):
    def __init__(self, name: str, path):
        super().__init__(name, path)

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
        if not FileSpliter.file_exists(path) and not FileSpliter.folder_exists(path):
            logger.debug("Invalid_PATH")
        else:
            while not CoapTransactionPool().is_transaction_finished(request):
                pass
            FileSpliter().split_on_bytes_and_send(request, path)

    def non_method(self, request: CoapPacket):
        if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
            if CoapOptionDelta.LOCATION_PATH.value in request.options:
                path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
                FileAssembler().handle_packets(request, path)
            else:
                FileAssembler().handle_paths(request)

