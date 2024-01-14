import os
import shutil

from share_drive.share_drive_helpers.drive_assembler import DriveAssembler
from share_drive.share_drive_helpers.drive_spliter import DriveSpliter
from share_drive.share_drive_helpers.drive_utils import DriveUtilities
from coap_core.coap_packet.coap_config import CoapOptionDelta, CoapCodeFormat
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_packet.coap_templates import CoapTemplates
from coap_core.coap_resource.resource import Resource
from coap_core.coap_utilities.coap_logger import logger, LogColor


class ServerResource(Resource):
    """
    Represents a CoAP server resource for handling various operations on a shared drive.
    The logic will be tight coupled with the logic from the client/proxy side.
    """

    def __init__(self, name: str, path):
        """
        Initializes a new instance of the ServerResource class.

        Args:
            name (str): The name of the resource.
            path: The path to the resource on the server.
        """
        super().__init__(name, path)

    @logger
    def handle_get(self, request):
        """
        Handles CoAP GET requests.

        Args:
            request: The CoAP request object.

        Raises:
            Exception: If an error occurs during handling.
        """
        try:
            # Handling GET requests
            if request.options.get(CoapOptionDelta.LOCATION_PATH.value) and request.has_option_block():
                os.chdir(self.get_path())
                path = request.options[CoapOptionDelta.LOCATION_PATH.value]
                if not DriveUtilities.file_exists(path) and not DriveUtilities.folder_exists(path):
                    # If the file or folder doesn't exist, send a NOT FOUND response
                    invalid_request = CoapTemplates.NOT_FOUND.value_with(request.token, request.message_id)
                    request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
                else:
                    # If the file or folder exists, split on bytes and send the content
                    DriveSpliter().split_on_bytes_and_send(request, path)
            else:
                # If options are missing, send a BAD REQUEST response
                invalid_request = CoapTemplates.BAD_REQUEST.value()
                invalid_request.token = request.token
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        except Exception as e:
            # If an exception occurs, send an INTERNAL ERROR response and raise the exception
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_post(self, request):
        """
        Handles CoAP POST requests.

        Args:
            request: The CoAP request object.

        Raises:
            Exception: If an error occurs during handling.
        """
        try:
            os.chdir(self.get_path())
            path = request.options[CoapOptionDelta.LOCATION_PATH.value]
            if DriveUtilities.file_exists(path) or DriveUtilities.folder_exists(path):
                if request.payload.get("rename"):
                    dirs = os.path.dirname(path)
                    if dirs:
                        os.chdir(os.path.dirname(path))
                    name = os.path.basename(path)
                    new_name = request.payload["rename"]
                    os.rename(src=name, dst=new_name)
                    coap_response = CoapTemplates.SUCCESS_CHANGED.value_with(request.token, request.message_id)
                    request.skt.sendto(coap_response.encode(), request.sender_ip_port)
                elif request.payload.get("move"):
                    new_path = request.payload["move"]
                    shutil.move(src=path, dst=new_path)
                    coap_response = CoapTemplates.SUCCESS_CHANGED.value_with(request.token, request.message_id)
                    request.skt.sendto(coap_response.encode(), request.sender_ip_port)
                else:
                    invalid_request = CoapTemplates.BAD_REQUEST.value_with(request.token, request.message_id)
                    request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
            else:
                invalid_request = CoapTemplates.BAD_REQUEST.value_with(request.token, request.message_id)
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        except Exception as e:
            # If an exception occurs, send an INTERNAL ERROR response and raise the exception
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_put(self, request):
        """
        Handles CoAP PUT requests.

        Args:
            request: The CoAP request object.

        Raises:
            Exception: If an error occurs during handling.
        """
        try:
            if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                    request.options.get(CoapOptionDelta.BLOCK1.value)):
                os.chdir(self.get_path())
                DriveAssembler().set_save_path(request.payload["upload_path"], False)
                relative_path = request.payload["upload_path"] + \
                                request.options[CoapOptionDelta.LOCATION_PATH.value].split('/')[-1]
                if DriveUtilities.file_exists(relative_path) or DriveUtilities.folder_exists(relative_path):
                    invalid_request = CoapTemplates.CONFLICT.value_with(request.token, request.message_id)
                    request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
            else:
                invalid_request = CoapTemplates.BAD_REQUEST.value_with(request.token, request.message_id)
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        except Exception as e:
            # If an exception occurs, reset the save path, send an INTERNAL ERROR response, and raise the exception
            DriveAssembler().reset_save_path()
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_delete(self, request):
        """
        Handles CoAP DELETE requests.

        Args:
            request: The CoAP request object.

        Raises:
            Exception: If an error occurs during handling.
        """
        try:
            os.chdir(self.get_path())
            path = request.options[CoapOptionDelta.LOCATION_PATH.value]
            if DriveUtilities.file_exists(path):
                os.remove(path)
                coap_response = CoapTemplates.SUCCESS_DELETED.value_with(request.token, request.message_id)
                request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            elif DriveUtilities.folder_exists(path):
                shutil.rmtree(path)
                coap_response = CoapTemplates.SUCCESS_DELETED.value_with(request.token, request.message_id)
                request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            else:
                invalid_request = CoapTemplates.BAD_REQUEST.value_with(request.token, request.message_id)
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        except Exception as e:
            # If an exception occurs, send an INTERNAL ERROR response and raise the exception
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_fetch(self, request: CoapPacket):
        """
        Handles CoAP FETCH requests.

        Args:
            request: The CoAP request object.

        Raises:
            Exception: If an error occurs during handling.
        """
        try:
            os.chdir(self.get_path())
            DriveSpliter().split_on_paths_and_send(request, self.get_path(), self.get_name())
        except Exception as e:
            # If an exception occurs, send an INTERNAL ERROR response and raise the exception
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    def handle_internal(self, request: CoapPacket):
        """
        Handles internal CoAP requests.

        Args:
            request: The internal CoAP request object.
        """
        pass

    def handle_response(self, request: CoapPacket):
        """
        Handles CoAP responses.

        Args:
            request: The CoAP response object.

        Raises:
            Exception: If an error occurs during handling.
        """
        try:
            if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
                if CoapOptionDelta.LOCATION_PATH.value in request.options:  # response of upload
                    os.chdir(self.get_path())
                    path = request.options[CoapOptionDelta.LOCATION_PATH.value]
                    DriveAssembler().handle_packets(request, path)
        except Exception as e:
            # If an exception occurs, send an INTERNAL ERROR response and log the exception
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            logger.debug(e, LogColor.YELLOW)
