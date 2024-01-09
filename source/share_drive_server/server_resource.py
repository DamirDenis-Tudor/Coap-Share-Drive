import os
import shutil

from source.share_drive_helpers.drive_utils import DriveUtilities
from source.share_drive_helpers.drive_assembler import DriveAssembler
from source.share_drive_helpers.drive_spliter import DriveSpliter
from source.coap_core.coap_packet.coap_config import CoapOptionDelta, CoapCodeFormat
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_resource.resource import Resource
from source.coap_core.coap_utilities.coap_logger import logger, LogColor


class ServerResource(Resource):
    def __init__(self, name: str, path):
        super().__init__(name, path)

    @logger
    def handle_get(self, request):
        try:
            if request.options.get(CoapOptionDelta.LOCATION_PATH.value) and request.has_option_block():
                os.chdir(self.get_path())
                path = request.options[CoapOptionDelta.LOCATION_PATH.value]
                if not DriveUtilities.file_exists(path) and not DriveUtilities.folder_exists(path):
                    invalid_request = CoapTemplates.NOT_FOUND.value_with(request.token, request.message_id)
                    request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
                else:
                    DriveSpliter().split_on_bytes_and_send(request, path)
            else:
                invalid_request = CoapTemplates.BAD_REQUEST.value()
                invalid_request.token = request.token
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        except Exception as e:
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_post(self, request):
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
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_put(self, request):
        try:
            if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                    request.options.get(CoapOptionDelta.BLOCK1.value)):
                os.chdir(self.get_path())
                DriveAssembler().set_save_path(request.payload["upload_path"], False)
                relative_path = request.payload["upload_path"] + request.options[CoapOptionDelta.LOCATION_PATH.value].split('/')[-1]
                if DriveUtilities.file_exists(relative_path) or DriveUtilities.folder_exists(relative_path):
                    invalid_request = CoapTemplates.CONFLICT.value_with(request.token, request.message_id)
                    request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
            else:
                invalid_request = CoapTemplates.BAD_REQUEST.value_with(request.token, request.message_id)
                request.skt.sendto(invalid_request.encode(), request.sender_ip_port)
        except Exception as e:
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_delete(self, request):
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
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    @logger
    def handle_fetch(self, request: CoapPacket):
        try:
            os.chdir(self.get_path())
            DriveSpliter().split_on_paths_and_send(request, self.get_path(), self.get_name())
        except Exception as e:
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            raise e

    def internal_handling(self, request: CoapPacket):
        pass

    def non_method(self, request: CoapPacket):
        try:
            if request.code == CoapCodeFormat.SUCCESS_CONTENT.value():
                if CoapOptionDelta.LOCATION_PATH.value in request.options:  # response of upload
                    os.chdir(self.get_path())
                    path = request.options[CoapOptionDelta.LOCATION_PATH.value]
                    DriveAssembler().handle_packets(request, path)
        except Exception as e:
            coap_response = CoapTemplates.INTERNAL_ERROR.value_with(request.token, request.message_id)
            request.skt.sendto(coap_response.encode(), request.sender_ip_port)
            logger.debug(e, LogColor.YELLOW)
