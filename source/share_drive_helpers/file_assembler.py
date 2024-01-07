import threading

from coap_core.coap_packet.coap_config import CoapOptionDelta
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from coap_core.coap_utilities.coap_logger import logger, LogColor
from coap_core.coap_utilities.coap_singleton import CoapSingletonBase
from coap_core.coap_utilities.coap_timer import CoapTimer
from share_drive_helpers.file_spliter import FileSpliter


class FileAssembler(CoapSingletonBase):
    def __init__(self):
        self.__transaction_pool = CoapTransactionPool()

        self.__in_assembly: dict[tuple, dict] = {}
        self.__assembled: list[tuple] = []

        self.__work_timer = CoapTimer()
        self.__lock = threading.Lock()

        self.__content_dict = {"folder": [], "file": []}

        self.__save_path = None

    def set_save_path(self, path: str):
        if FileSpliter.folder_exists(path):
            self.__save_path = f"/home/{path}"

    def handle_paths(self, response: CoapPacket):
        with self.__lock:
            if "folder" in response.payload:
                self.__content_dict["folder"].append(response.payload["folder"])
            elif "file" in response.payload:
                self.__content_dict["file"].append(response.payload["file"])
            if not CoapPacket.decode_option_block(response.options[response.get_option_code()])["M"]:
                self.__transaction_pool.finish_overall_transaction(response)

    def handle_packets(self, packet: CoapPacket, path: str):
        with self.__lock:

            option = CoapPacket.decode_option_block(packet.options[packet.get_option_code()])

            if packet.general_work_id() not in self.__in_assembly:  # register file operation-related packets
                self.__in_assembly[packet.general_work_id()] = {
                    "TOTAL_RESPONSES": 0,
                    "WRITE_INDEX": 0,
                    "RECEIVED_PACKETS": {}
                }
                self.__work_timer.reset()
                if FileSpliter.file_exists(path):
                    FileSpliter.delete_file(path)

            if packet.get_block_id() == 0:
                logger.log(f"> Downloading {packet.options[packet.get_size_code()]} packets...", LogColor.CYAN)

            operation_dict = self.__in_assembly[packet.general_work_id()]

            if not option["M"]:
                operation_dict["TOTAL_RESPONSES"] = option["NUM"]

            if operation_dict["WRITE_INDEX"] == option["NUM"]:
                operation_dict["RECEIVED_PACKETS"][option["NUM"]] = packet.payload
                index = operation_dict["WRITE_INDEX"]

                while operation_dict["WRITE_INDEX"] + 1 in operation_dict["RECEIVED_PACKETS"]:
                    operation_dict["WRITE_INDEX"] += 1

                if self.__save_path:
                    path = self.__save_path + packet.options[CoapOptionDelta.LOCATION_PATH.value]
                for i in range(index, operation_dict["WRITE_INDEX"] + 1):
                    with open(path, 'ab') as file:
                        file.write(operation_dict["RECEIVED_PACKETS"][i])
                        operation_dict["RECEIVED_PACKETS"].pop(i)
                operation_dict["WRITE_INDEX"] += 1
            else:
                operation_dict["RECEIVED_PACKETS"][option["NUM"]] = packet.payload

            if operation_dict["TOTAL_RESPONSES"] != 0:
                if operation_dict["WRITE_INDEX"] - 1 == operation_dict["TOTAL_RESPONSES"]:
                    del self.__in_assembly[packet.general_work_id()]
                    self.__assembled.append(packet.general_work_id())
                    self.__transaction_pool.finish_overall_transaction(packet)
                    if path.__contains__(".zip"):
                        logger.debug(f"<{packet.token}> Unzipping the folder: {path}")
                        logger.log(f"> Unzipping the folder: {path}")
                        FileSpliter.decompress_folder(path)
                        FileSpliter.delete_file(path)
                    self.__save_path = None
                    logger.log(f"> Download finished in {self.__work_timer.elapsed_time()}", LogColor.CYAN)
                    logger.debug(f"<{packet.token}> Request finished in {self.__work_timer.elapsed_time()}",
                                 LogColor.CYAN)

    def get_files_list(self) -> list:
        return self.__content_dict["file"]

    def get_folders_list(self) -> list:
        return self.__content_dict["folder"]

    def get_content(self):
        return self.__content_dict["file"] + self.__content_dict["folder"]

    def clear_content(self):
        self.__content_dict = {"folder": [], "file": []}
