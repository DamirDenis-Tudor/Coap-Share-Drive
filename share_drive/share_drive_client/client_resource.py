import os

from share_drive.share_drive_helpers.drive_utils import DriveUtilities
from share_drive.share_drive_helpers.drive_assembler import DriveAssembler
from share_drive.share_drive_helpers.drive_spliter import DriveSpliter
from coap_core.coap_packet.coap_templates import CoapTemplates
from coap_core.coap_utilities.coap_logger import logger
from coap_core.coap_packet.coap_config import CoapCodeFormat, CoapOptionDelta
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_resource.resource import Resource
from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool


class ClientResource(Resource):
    """
    Represents a client-side CoAP resource.

    The logic will be tight coupled with the logic from the sever/proxy side.
    """

    def __init__(self, name: str, path):
        """
        Initializes the ClientResource instance.

        Args:
            name (str): The name of the resource.
            path: The path associated with the resource.
        """
        super().__init__(name, path)

    def handle_get(self, request):
        """
        Handles GET requests on the client-side resource.

        Args:
            request (CoapPacket): The CoAP packet representing the incoming request.
        """
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_post(self, request):
        """
        Handles POST requests on the client-side resource.

        Args:
            request (CoapPacket): The CoAP packet representing the incoming request.
        """
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_put(self, request):
        """
        Handles PUT requests on the client-side resource.

        Args:
            request (CoapPacket): The CoAP packet representing the incoming request.
        """
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_delete(self, request):
        """
        Handles DELETE requests on the client-side resource.

        Args:
            request (CoapPacket): The CoAP packet representing the incoming request.
        """
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_fetch(self, request: CoapPacket):
        """
        Handles FETCH requests on the client-side resource.

        Args:
            request (CoapPacket): The CoAP packet representing the incoming request.
        """
        invalid_request = CoapTemplates.NOT_IMPLEMENTED.value_with(request.token, request.message_id)
        request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def handle_internal(self, request: CoapPacket):
        """
        Handles internal operations on the client-side resource.

        Args:
            request (CoapPacket): The CoAP packet representing the internal operation request.
        """
        path = request.options[CoapOptionDelta.LOCATION_PATH.value]
        if not DriveUtilities.file_exists(path) and not DriveUtilities.folder_exists(path):
            logger.debug("Invalid_PATH")
        else:
            while not CoapTransactionPool().is_transaction_finished(request):
                pass
            DriveSpliter().split_on_bytes_and_send(request, path)

    def handle_response(self, request: CoapPacket):
        """
        Handles responses on the client-side resource.

        Args:
            request (CoapPacket): The CoAP packet representing the response.
        """
        os.chdir(self.get_path())
        if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
            if CoapOptionDelta.LOCATION_PATH.value in request.options:
                path = request.options[CoapOptionDelta.LOCATION_PATH.value]
                DriveAssembler().handle_packets(request, path)
            else:
                DriveAssembler().handle_paths(request)


