import os
import threading

from share_drive.share_drive_helpers.drive_utils import DriveUtilities
from coap_core.coap_packet.coap_config import CoapOptionDelta
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from coap_core.coap_utilities.coap_logger import logger, LogColor
from coap_core.coap_utilities.coap_singleton import CoapSingletonBase
from coap_core.coap_utilities.coap_timer import CoapTimer


class DriveAssembler(CoapSingletonBase):
    """
    DriveAssembler is a class responsible for assembling CoAP responses received in packets.
    It manages both file operations and path responses during the communication process.
    Its main usage is within the share_drive context.

    Author: Damir Denis-Tudor
    """

    def __init__(self):
        """
        Constructor for DriveAssembler.

        Initializes the necessary attributes for handling CoAP response assembly,
        including the transaction pool, assembly dictionaries, timer, lock, and content-related attributes.
        """
        self.__transaction_pool = CoapTransactionPool()

        # Dictionary to store in-progress file assembly
        self.__in_assembly: dict[tuple, dict] = {}

        # List to store assembled operations
        self.__assembled: list[tuple] = []

        self.__work_timer = CoapTimer()
        self.__lock = threading.Lock()

        # Dictionary to store content details (folders and files)
        self.__content_dict = {"folder": [], "file": []}

        self.__save_path = None

    def set_save_path(self, path: str, home_root=True):
        """
        Set the save path for downloaded files.

        Parameters:
        - path (str): The base path for saving files.
        - home_root (bool): Whether to use the home directory as the root for saving files.
        """
        if DriveUtilities.folder_exists(path):
            print(home_root)
            if home_root:
                self.__save_path = f"{os.path.expanduser('~')}/{path}/"
            else:
                self.__save_path = f"{path}/"

    def reset_save_path(self):
        self.__save_path = None

    def handle_paths(self, response: CoapPacket):
        """
        Handle CoAP responses containing path information.

        Parameters:
        - response (CoapPacket): The CoAP packet containing path information.
        """
        with self.__lock:
            # Extract and store folder and file information from the response
            if "folder" in response.payload:
                self.__content_dict["folder"].append(response.payload["folder"])
            elif "file" in response.payload:
                self.__content_dict["file"].append(response.payload["file"])
            # Finish the overall transaction if it's the last response in the sequence
            if not CoapPacket.decode_option_block(response.options[response.get_option_code()])["M"]:
                self.__transaction_pool.finish_overall_transaction(response)

    def handle_packets(self, packet: CoapPacket, path: str):
        """
        Handle CoAP packets for assembling file content in a thread safe manner.
        When the handling is finished, it's important to actualize the overall
        transaction status.

        Parameters:
        - packet (CoapPacket): The CoAP packet containing file content.
        - path (str): The path for saving the file.
        """
        with self.__lock:
            # Decode the block-related options from the CoAP packet
            option = CoapPacket.decode_option_block(packet.options[packet.get_option_code()])

            # Register file operation-related packets
            if packet.general_work_id() not in self.__in_assembly:
                self.__in_assembly[packet.general_work_id()] = {
                    "TOTAL_RESPONSES": -1,
                    "WRITE_INDEX": 0,
                    "RECEIVED_PACKETS": {}
                }
                self.__work_timer.reset()

                # If the file already exists, delete it before downloading
                if DriveUtilities.file_exists(path):
                    DriveUtilities.delete_file(path)

            # Log download progress
            if packet.get_block_id() == 0:
                logger.log(f"> Downloading {packet.options[packet.get_size_code()]} packets...", LogColor.CYAN)

            operation_dict = self.__in_assembly[packet.general_work_id()]

            # Register the total number of responses if not already set
            if not option["M"]:
                operation_dict["TOTAL_RESPONSES"] = option["NUM"]

            # Process received packets and write to the file
            if operation_dict["WRITE_INDEX"] == option["NUM"]:
                operation_dict["RECEIVED_PACKETS"][option["NUM"]] = packet.payload
                index = operation_dict["WRITE_INDEX"]

                while operation_dict["WRITE_INDEX"] + 1 in operation_dict["RECEIVED_PACKETS"]:
                    operation_dict["WRITE_INDEX"] += 1

                # Set the full path for saving the file
                if self.__save_path:
                    path = self.__save_path + packet.options[CoapOptionDelta.LOCATION_PATH.value]

                # Write received packets to the file
                for i in range(index, operation_dict["WRITE_INDEX"] + 1):
                    with open(path, 'ab') as file:
                        file.write(operation_dict["RECEIVED_PACKETS"][i])
                        operation_dict["RECEIVED_PACKETS"].pop(i)
                operation_dict["WRITE_INDEX"] += 1
            else:
                operation_dict["RECEIVED_PACKETS"][option["NUM"]] = packet.payload

            # Finish the overall transaction when all packets are received
            if operation_dict["TOTAL_RESPONSES"] != -1:
                if operation_dict["WRITE_INDEX"] - 1 == operation_dict["TOTAL_RESPONSES"]:

                    # Cleanup and finish the transaction
                    del self.__in_assembly[packet.general_work_id()]
                    self.__assembled.append(packet.general_work_id())
                    self.__transaction_pool.finish_overall_transaction(packet)

                    # If the file has a ".zip" extension, unzip it and delete the original compressed file
                    if path.__contains__(".zip"):
                        logger.debug(f"<{packet.token}> Unzipping the folder: {path}")
                        logger.log(f"> Unzipping the folder: {path}")
                        DriveUtilities.decompress_folder(path)
                        DriveUtilities.delete_file(path)
                    self.__save_path = None

                    # Log completion time
                    logger.log(f"> Download finished in {self.__work_timer.elapsed_time()}", LogColor.CYAN)
                    logger.debug(f"<{packet.token}> Request finished in {self.__work_timer.elapsed_time()}",
                                 LogColor.CYAN)

    def get_files_list(self) -> list:
        """
        Get the list of files in the content dictionary.

        Returns:
        - list: List of files.
        """
        return sorted(self.__content_dict["file"], key=len)

    def get_folders_list(self) -> list:
        """
        Get the list of folders in the content dictionary.

        Returns:
        - list: List of folders.
        """
        return sorted(self.__content_dict["folder"], key=len)

    def get_content(self):
        """
        Get the combined list of files and folders in the content dictionary.

        Returns:
        - list: Combined list of files and folders.
        """
        return sorted(self.__content_dict["file"] + self.__content_dict["folder"], key=len)

    def clear_content(self):
        """
        Clear the content dictionary.
        """
        self.__content_dict = {"folder": [], "file": []}

