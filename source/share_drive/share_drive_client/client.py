import threading

from source.coap_core.coap_worker.coap_worker_pool import CoapWorkerPool
from source.coap_core.coap_packet.coap_config import CoapOptionDelta
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_resource.resource_manager import ResourceManager
from source.coap_core.coap_utilities.coap_logger import logger
from source.share_drive.share_drive_client.client_resource import ClientResource

logger.is_enabled = False
class Client(CoapWorkerPool):
    def __init__(self, ip_address, port):
        super().__init__(ip_address, port)

        self.add_background_thread(threading.Thread(target=self.run_ui))

        ResourceManager().set_root_path("/home/damir/coap/client/")
        ResourceManager().discover_resources()
        ResourceManager().add_default_resource(ClientResource("downloads"))

    @logger
    def run_ui(self):
        while True:
            print("1 -> download\n2 -> upload\n3 -> rename/move\n4 -> delete\n5 -> sync")
            data = input("Option: ")
            path = input("Path: ")
            if data == "1":
                coap_message = CoapTemplates.DOWNLOAD.value_with(0, 0)
                coap_message.options[CoapOptionDelta.LOCATION_PATH.value] =path
                coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
                coap_message.skt = self._socket
                coap_message.sender_ip_port = ("127.0.0.2", int(5683))
                self.handle_internal_task(coap_message)
            elif data == "2":
                coap_message = CoapTemplates.UPLOAD.value()
                coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = path
                coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
                coap_message.skt = self._socket
                coap_message.sender_ip_port = ("127.0.0.2", int(5683))
                self.handle_internal_task(coap_message, internal_computation=True)
            elif data == "3":
                coap_message = CoapTemplates.MV.value()
            elif data == "4":
                coap_message = CoapTemplates.DELETE.value()
            elif data == "5":
                coap_message = CoapTemplates.SYNC.value()


if __name__ == "__main__":
    Client("127.0.0.4", int(5687)).listen()
