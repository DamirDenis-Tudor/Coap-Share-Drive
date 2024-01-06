import argparse
import threading
from _socket import IPPROTO_UDP
from socket import socket, AF_INET, SOCK_DGRAM

import questionary
from pyfiglet import Figlet

from source.coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from source.coap_core.coap_packet.coap_config import CoapOptionDelta
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.share_drive_helpers.file_handler import FileHandler
from source.coap_core.coap_resource.resource_manager import ResourceManager
from source.coap_core.coap_utilities.coap_logger import logger, LogColor
from source.coap_core.coap_worker.coap_worker_pool import CoapWorkerPool
from source.share_drive_client.client_resource import ClientResource


class TestClient(CoapWorkerPool):
    def __init__(self, server_ip, server_port, ip_address, port):
        skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        skt.bind((ip_address, port))
        super().__init__(skt, ClientResource("downloads", "/home/damir/coap/client/resources/"))

        self._add_background_thread(threading.Thread(target=self.client_cli))

        self.__server_ip = server_ip
        self.__server_port = server_port


    @logger
    def client_cli(self):
        logger.log(Figlet(font="slant").renderText("COaP Drive"), color=LogColor.BLUE)

        while True:
            # command = questionary.select(
            #     "Select an action:",
            #     choices=[
            #         "Download",
            #         "Upload",
            #         "Rename",
            #         "Move",
            #         "Delete",
            #         "List",
            #         "Exit"
            #     ]
            # ).ask()

            command = "Download"

            if command == "Download":
                #file_name = questionary.path("Enter the file name to download: ").ask()
                #local_path = questionary.text("Enter the local path to save the file: ").ask()
                #self.download_file(file_name, local_path)
                coap_message = CoapTemplates.DOWNLOAD.value()
                coap_message.options[
                    CoapOptionDelta.LOCATION_PATH.value] = "/test (copy).webm"
                coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
                coap_message.skt = self._socket
                coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
                self._handle_internal_task(coap_message)
                logger.log("Seeend")
                break
            elif command == "Upload":
                # local_file_path = questionary.text("Enter the local file path to upload: ").ask()
                # remote_path = questionary.text("Enter the remote path to upload the file[default: file_name]: ").ask()
                # self.upload_file(local_file_path, remote_path)
                coap_message = CoapTemplates.UPLOAD.value()
                coap_message.options[
                    CoapOptionDelta.LOCATION_PATH.value] = "/home/damir/coap/client/resources/downloads/test.webm"
                coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
                coap_message.skt = self._socket
                coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
                coap_message.needs_internal_computation = True
                self._handle_internal_task(coap_message)
                logger.log("Seeend")
                break
            elif command == "Rename":
                # Add prompts for renaming
                pass
            elif command == "Move":
                # Add prompts for moving
                pass
            elif command == "Delete":
                # Add prompts for deleting
                pass
            elif command == "List files":
                self.fetch_server_data()
                break
            elif command == "Exit":
                break

    def download_file(self):
        # Implement code for downloading a file from source.the server
        pass

    def upload_file(self, file_path, file_name):
        # Implement code for uploading a file to the server
        pass

    def rename_file(self):
        # Implement code for renaming a file on the server
        pass

    def move_file(self):
        # Implement code for moving a file on the server
        pass

    def delete_file(self):
        # Implement code for deleting a file on the server
        pass

    def fetch_server_data(self):
        coap_message = CoapTemplates.FETCH.value()
        coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
        coap_message.skt = self._socket
        coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
        self._handle_internal_task(coap_message)
        CoapTransactionPool().wait_util_finish(coap_message)
        h = FileHandler()
        logger.log(h.get_files_list())


def main():
    parser = argparse.ArgumentParser(description='Client script with address and port arguments')

    # Server arguments
    parser.add_argument('--server_address', '-sa', type=str, default='127.0.0.1', help='Server address')
    parser.add_argument('--server_port', '-sp', type=int, default=5683, help='Server port')

    # Client arguments
    parser.add_argument('--client_address', '-ca', type=str, default='127.0.0.4', help='Client address')
    parser.add_argument('--client_port', '-cp', type=int, default=5683, help='Client port')

    args = parser.parse_args()

    logger.is_enabled = True
    TestClient(
        args.server_address,
        args.server_port,
        args.client_address,
        args.client_port
    ).listen()


if __name__ == "__main__":
    main()
