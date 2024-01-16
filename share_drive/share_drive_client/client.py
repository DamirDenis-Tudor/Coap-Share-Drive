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

from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from coap_core.coap_packet.coap_config import CoapOptionDelta
from coap_core.coap_utilities.coap_logger import logger, LogColor
from coap_core.coap_worker.coap_worker_pool import CoapWorkerPool
from share_drive.share_drive_client.client_resource import ClientResource
from share_drive.share_drive_helpers.drive_assembler import DriveAssembler
from share_drive.share_drive_helpers.drive_templates import DriveTemplates


def clean_terminal():
    """
    Clears the terminal screen and displays the CoAP Drive Client banner.
    """
    os.system('clear')
    os.chdir('/home')
    logger.log(Figlet(font="standard", width=400).renderText("Coap Drive Client"), color=LogColor.BLUE)


class Client(CoapWorkerPool):
    """
    Represents the CoAP Drive Client.

    Args:
        server_ip (str): The IP address of the CoAP server.
        server_port (int): The port of the CoAP server.
        ip_address (str): The IP address of the client.
        port (int): The port of the client.
    """

    def __init__(self, server_ip, server_port, ip_address, port):
        """
        Initializes the CoAP Drive Client.

        Args:
            server_ip (str): The IP address of the CoAP server.
            server_port (int): The port of the CoAP server.
            ip_address (str): The IP address of the client.
            port (int): The port of the client.
        """
        skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        skt.bind((ip_address, port))
        super().__init__(skt, ClientResource("downloads", f"{os.path.expanduser('~')}/coap/client/resources/"))

        self._add_background_thread(threading.Thread(target=self.client_cli))

        self.__server_ip = server_ip
        self.__server_port = server_port
        self.__style = Style(
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

    def download_file(self):
        """
        Initiates the process of downloading a file from the CoAP server.
        """
        os.chdir(os.path.expanduser("~"))
        content = DriveAssembler().get_content()
        if content:
            file_name = questionary.autocomplete(
                "Enter the file name to download: ",
                style=self.__style,
                choices=DriveAssembler().get_content(),
            ).ask()

            local_path = questionary.path(
                "Enter the local path to save the file: ",
                style=self.__style,
                complete_style=CompleteStyle.COLUMN
            ).ask()

            coap_message = DriveTemplates.DOWNLOAD.value()
            coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = file_name
            coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
            coap_message.skt = self._socket
            coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))

            DriveAssembler().set_save_path(local_path)
            self._handle_internal_task(coap_message)

            CoapTransactionPool().wait_util_finish(coap_message)
        else:
            logger.log("> There is nothing to be downloaded.", LogColor.YELLOW)

    def upload_file(self):
        """
        Initiates the process of uploading a file to the CoAP server.
        """
        os.chdir(os.path.expanduser("~"))
        local_file_path = questionary.path(
            "Enter the local file path to upload: ",
            style=self.__style,
            complete_style=CompleteStyle.COLUMN
        ).ask()

        remote_path = questionary.autocomplete(
            "Enter the remote path to upload the file: ",
            ["/"] + DriveAssembler().get_folders_list(),
            style=self.__style
        ).ask()

        coap_message = DriveTemplates.UPLOAD.value()
        coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = local_file_path
        coap_message.options[CoapOptionDelta.URI_PATH.value] = f"share_drive"
        coap_message.payload = {'upload_path': remote_path}
        coap_message.skt = self._socket
        coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
        coap_message.needs_internal_computation = True

        self._handle_internal_task(coap_message)

        CoapTransactionPool().wait_util_finish(coap_message)

    def rename_file(self):
        """
        Initiates the process of renaming a file on the CoAP server.
        """
        content = DriveAssembler().get_content()
        if content:
            file_name = questionary.autocomplete(
                "Enter the file name to rename: ",
                style=self.__style,
                choices=DriveAssembler().get_content(),
            ).ask()

            new_name = questionary.text(
                "Enter the new name: ",
                style=self.__style,
                complete_style=CompleteStyle.COLUMN
            ).ask()

            coap_message = DriveTemplates.CHANGE.value()
            coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = file_name
            coap_message.options[CoapOptionDelta.URI_PATH.value] = f"share_drive"
            coap_message.skt = self._socket
            coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
            coap_message.payload = {'rename': new_name}
            self._handle_internal_task(coap_message)

        else:
            logger.log("> There is nothing to be renamed.", LogColor.YELLOW)

    def move_file(self):
        """
        Initiates the process of moving a file on the CoAP server.
        """
        content = DriveAssembler().get_content()
        if content:
            file_path = questionary.autocomplete(
                "Enter the file/folder to be moved: ",
                style=self.__style,
                choices=DriveAssembler().get_content(),
            ).ask()

            new_location = questionary.autocomplete(
                "Enter the new path: ",
                style=self.__style,
                choices=["."] + DriveAssembler().get_folders_list(),
                complete_style=CompleteStyle.COLUMN
            ).ask()

            coap_message = (DriveTemplates.CHANGE.value())
            coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = file_path
            coap_message.options[CoapOptionDelta.URI_PATH.value] = f"share_drive"
            coap_message.skt = self._socket
            coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
            coap_message.payload = {'move': new_location}
            self._handle_internal_task(coap_message)

        else:
            logger.log("> There is nothing to be moved.", LogColor.YELLOW)

    def delete_file(self):
        """
        Initiates the process of deleting a file on the CoAP server.
        """
        content = DriveAssembler().get_content()
        if content:
            file_path = questionary.autocomplete(
                "Enter the remote path that you want to delete: ",
                DriveAssembler().get_content(),
                style=self.__style
            ).ask()
            coap_message = DriveTemplates.DELETE.value()
            coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = file_path
            coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
            coap_message.skt = self._socket
            coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
            self._handle_internal_task(coap_message)

        else:
            logger.log("> There is nothing to be deleted.", LogColor.YELLOW)

    def fetch_server_data(self):
        """
        Fetches data from the CoAP server and updates the client's local representation.
        """
        DriveAssembler().clear_content()

        coap_message = DriveTemplates.FETCH.value()
        coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
        coap_message.skt = self._socket
        coap_message.sender_ip_port = (self.__server_ip, int(self.__server_port))
        self._handle_internal_task(coap_message)

        CoapTransactionPool().wait_util_finish(coap_message)

    def client_cli(self):
        """
        Implements the command-line interface (CLI) for the CoAP Drive Client.
        """
        clean_terminal()
        try:
            choices = ["Download", "Upload", "Rename", "Move", "Delete", "Exit"]

            while True:
                self.fetch_server_data()
                command = questionary.select("Select an operation:", choices=choices, style=self.__style).ask()
                match command:
                    case "Download":
                        self.download_file()
                    case "Upload":
                        self.upload_file()
                    case "Rename":
                        self.rename_file()
                    case "Move":
                        self.move_file()
                    case "Delete":
                        self.delete_file()
                    case "Exit":
                        self.stop()
                        break
                logger.log("> Press any key to continue...", LogColor.GREEN)
                readchar.readchar()
                clean_terminal()

        except KeyboardInterrupt:
            logger.log("Keyboard interruption")


def main():
    """
    Main function to parse command-line arguments and start the CoAP Drive Client.
    """
    parser = argparse.ArgumentParser(description='Client script with address and port arguments')

    # Server arguments
    parser.add_argument('--server_address', '-sa', type=str, default='127.0.0.1', help='Server address')
    parser.add_argument('--server_port', '-sp', type=int, default=5683, help='Server port')

    # Client arguments
    parser.add_argument('--client_address', '-ca', type=str, default='127.0.0.2', help='Client address')
    parser.add_argument('--client_port', '-cp', type=int, default=5683, help='Client port')

    args = parser.parse_args()

    Client(args.server_address, args.server_port, args.client_address, args.client_port).listen()


if __name__ == "__main__":
    main()
