from source.coap_core.coap_packet.coap_config import CoapCodeFormat, CoapOptionDelta
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_resource.resource import Resource
from source.coap_core.coap_utilities.coap_logger import logger
from source.share_drive.share_drive_helpers.file_handler import FileHandler


class ClientResource(Resource):
    def __init__(self, path: str):
        super().__init__(path)
        self.__file_handler = FileHandler()

    @logger
    def handle_get(self, request):
        pass

    def handle_post(self, request):
        pass

    def handle_put(self, request):
        self.__file_handler.get_sender()(
            request,
            request.options[CoapOptionDelta.LOCATION_PATH.value]
        )

    def handle_delete(self, request):
        pass

    def handle_fetch(self, request: CoapPacket):
        pass

    def non_method(self, request: CoapPacket):
        if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]
            self.__file_handler.handle_packets(request, path)
