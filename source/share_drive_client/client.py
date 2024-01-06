import argparse
import os
import threading
from _socket import IPPROTO_UDP
from socket import socket, AF_INET, SOCK_DGRAM

import questionary
import readchar
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.styles import Style
from pyfiglet import Figlet

from source.coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from source.coap_core.coap_packet.coap_config import CoapOptionDelta
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.share_drive_helpers.file_handler import FileHandler
from source.coap_core.coap_resource.resource_manager import ResourceManager
from source.coap_core.coap_utilities.coap_logger import logger, LogColor
from source.coap_core.coap_worker.coap_worker_pool import CoapWorkerPool
from source.share_drive_client.client_resource import ClientResource


class Client(CoapWorkerPool):
    def __init__(self, server_ip, server_port, ip_address, port):
        skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        skt.bind((ip_address, port))
        super().__init__(skt, ClientResource("downloads", "/home/damir/coap/client/resources/"))

        self._add_background_thread(threading.Thread(target=self.client_cli))

        self.__server_ip = server_ip
        self.__server_port = server_port

    def clean_terminal(self):
        os.system('clear')
        os.chdir('/home')
        logger.log(Figlet(font="standard").renderText("Coap Drive"), color=LogColor.BLUE)

    def client_cli(self):
        self.clean_terminal()
        try:
            custom_style_genius = Style(
                [
                    ("separator", "fg:#cc5454"),
                    ("qmark", "fg:#673ab7 bold"),
                    ("question", "fg:#5050f2 bold"),
                    ("selected", "fg:#cc5454"),
                    ("pointer", "fg:#673ab7 bold"),
                    ("highlighted", "fg:#4848fa bold"),
                    ("answer", "fg:#13752d bold"),
                    ("text", "fg:#acacfc"),
                    ("disabled", "fg:#858585 italic"),
                ]
            )
            choices = ["Download", "Upload", "Rename", "Move", "Delete", "Settings", "Exit"]

            while True:
                self.fetch_server_data()
                command = questionary.select(
                    "Select an operation:",
                    choices=choices,
                    use_arrow_keys=True,
                    style=custom_style_genius
                ).ask()

                command = command.replace(" ", "")

                if command == "Download":

                    file_name = questionary.autocomplete(
                        "Enter the file name to download: ",
                        style=custom_style_genius,
                        choices=FileHandler().get_files_list(),
                    ).ask()

                    local_path = questionary.path(
                        "Enter the local path to save the file: ",
                        style=custom_style_genius,
                        complete_style=CompleteStyle.COLUMN
                    ).ask()

                    self.download_file(file_name, str(local_path))
                elif command == "Upload":

                    local_file_path = questionary.path(
                        "Enter the local file path to upload: ",
                        style=custom_style_genius,
                        complete_style=CompleteStyle.COLUMN
                    ).ask()

                    remote_path = questionary.autocomplete(
                        "Enter the remote path to upload the file: ",
                        FileHandler().get_folders_list(),
                        style=custom_style_genius
                    ).ask()

                    self.upload_file(local_file_path, remote_path)
                elif command == "Rename":
                    # Add prompts for renaming
                    pass
                elif command == "Move":
                    # Add prompts for moving
                    pass
                elif command == "Delete":
                    # Add prompts for deleting
                    pass
                elif command == "Settings":
                    pass
                elif command == "Exit":
                    self.stop()
                    break

                logger.log("> Press any key to continue...", LogColor.GREEN)
                readchar.readchar()
                self.clean_terminal()

        except KeyboardInterrupt:
            logger.log("Keyboard interruption")

    def download_file(self, file_name, local_path):

        coap_message = CoapTemplates.DOWNLOAD.value()
        coap_message.options[
            CoapOptionDelta.LOCATION_PATH.value] = file_name
        coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
        coap_message.skt = self._socket
        coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
        self._handle_internal_task(coap_message)

        CoapTransactionPool().wait_util_finish(coap_message)

    def upload_file(self, file_path, file_name):
        coap_message = CoapTemplates.UPLOAD.value()
        coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = file_path
        coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
        coap_message.skt = self._socket
        coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
        coap_message.needs_internal_computation = True

        self._handle_internal_task(coap_message)

        CoapTransactionPool().wait_util_finish(coap_message)

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
        FileHandler().clear_content()

        coap_message = CoapTemplates.FETCH.value()
        coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
        coap_message.skt = self._socket
        coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
        self._handle_internal_task(coap_message)

        CoapTransactionPool().wait_util_finish(coap_message)


def main():
    parser = argparse.ArgumentParser(description='Client script with address and port arguments')

    # Server arguments
    parser.add_argument('--server_address', '-sa', type=str, default='127.0.0.1', help='Server address')
    parser.add_argument('--server_port', '-sp', type=int, default=5683, help='Server port')

    # Client arguments
    parser.add_argument('--client_address', '-ca', type=str, default='127.0.0.2', help='Client address')
    parser.add_argument('--client_port', '-cp', type=int, default=5683, help='Client port')

    args = parser.parse_args()

    logger.is_enabled = True
    Client(
        args.server_address,
        args.server_port,
        args.client_address,
        args.client_port
    ).listen()


if __name__ == "__main__":
    main()
