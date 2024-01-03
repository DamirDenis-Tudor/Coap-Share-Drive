import json
import os
import random
import threading
from copy import deepcopy
from functools import singledispatchmethod

from tqdm import tqdm

from source.coap_core.coap_utilities.coap_singleton import CoapSingleton
from source.coap_core.coap_packet.coap_config import CoapOptionDelta
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from source.coap_core.coap_utilities.coap_logger import logger, LogColor
from source.coap_core.coap_utilities.coap_timer import CoapTimer


class FileHandler(metaclass=CoapSingleton):

    @staticmethod
    def file_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isdir(file_path)

    @staticmethod
    def split_on_paths(source: str, relative_to: str):
        paths = []
        for root, dirs, files in os.walk(source):
            for d in dirs:
                dir_path = os.path.join(root, d)
                dir_path = dir_path.split(relative_to)[1]
                paths.append({"folder": dir_path})
            for file in files:
                file_path = os.path.join(root, file)
                file_path = file_path.split(relative_to)[1]
                paths.append({"file": file_path})
        return paths

    @staticmethod
    def split_on_packets(file_path: str, block_size: int):
        with open(file_path, 'rb') as file:
            while True:
                file_data = file.read(block_size)
                if not file_data:
                    break
                yield file_data

    @staticmethod
    def get_total_paths(source: str):
        index = 0
        for root, dirs, files in os.walk(source):
            for _ in dirs:
                index += 1
            for _ in files:
                index += 1
        return index

    @staticmethod
    def get_total_packets(file_path: str, block_size: int) -> int:
        file_size = os.path.getsize(file_path)
        total_packets = (file_size + block_size - 1) // block_size
        return total_packets

    def __init__(self):
        self.__transaction_pool = CoapTransactionPool()

        self.__in_assembly: dict[tuple, dict] = {}
        self.__assembled: list[tuple] = []

        self.__work_timer = CoapTimer()
        self.__lock = threading.Lock()

        self.__content_dict = {"folder": [], "file": []}

    def handle_packets(self, packet: CoapPacket, path: str):
        with self.__lock:

            option = CoapPacket().decode_option_block(packet.options[CoapOptionDelta.BLOCK2.value])

            if packet.general_work_id() not in self.__in_assembly:  # register file operation-related packets
                self.__in_assembly[packet.general_work_id()] = {
                    "TOTAL_RESPONSES": 0,
                    "WRITE_INDEX": 0,
                    "RECEIVED_PACKETS": {}
                }
                self.__work_timer.reset()

            operation_dict = self.__in_assembly[packet.general_work_id()]
            logger.debug(f"Write Index : {operation_dict['WRITE_INDEX']} -> Handle the packet: {packet}")

            if not option["M"]:
                operation_dict["TOTAL_RESPONSES"] = option["NUM"]

            if operation_dict["WRITE_INDEX"] == option["NUM"]:
                operation_dict["RECEIVED_PACKETS"][option["NUM"]] = packet.payload
                index = operation_dict["WRITE_INDEX"]

                while operation_dict["WRITE_INDEX"] + 1 in operation_dict["RECEIVED_PACKETS"]:
                    operation_dict["WRITE_INDEX"] += 1

                for i in range(index, operation_dict["WRITE_INDEX"] + 1):
                    with open(path, 'ab') as file:
                        file.write(operation_dict["RECEIVED_PACKETS"][i])
                        operation_dict["RECEIVED_PACKETS"].pop(i)
                operation_dict["WRITE_INDEX"] += 1
            else:
                operation_dict["RECEIVED_PACKETS"][option["NUM"]] = packet.payload

            if operation_dict["TOTAL_RESPONSES"] != 0:
                if operation_dict["WRITE_INDEX"] - 1 == operation_dict["TOTAL_RESPONSES"]:
                    self.__in_assembly.pop(packet.general_work_id())
                    self.__assembled.append(packet.general_work_id())
                    self.__transaction_pool.finish_overall_transaction(packet)

                    logger.debug(f"Assembly of {packet.general_work_id()} finished.")
                    logger.log(f"> Download finished in {self.__work_timer.elapsed_time()}", LogColor.CYAN)

    def handle_paths(self, response: CoapPacket):
        with self.__lock:
            if "folder" in response.payload:
                self.__content_dict["folder"].append(response.payload["folder"])
            elif "file" in response.payload:
                self.__content_dict["file"].append(response.payload["file"])
            if not CoapPacket.decode_option_block(response.options[CoapOptionDelta.BLOCK2.value])["M"]:
                self.__transaction_pool.finish_overall_transaction(response)

    def split_on_bytes_and_send(self, request: CoapPacket, path: str):
        block_fields = CoapPacket.decode_option_block(request.options[CoapOptionDelta.BLOCK1.value])
        total_packets = FileHandler.get_total_packets(path, block_fields["BLOCK_SIZE"])
        logger.debug(f"<{request.sender_ip_port}->{request.token}> Total packets: {total_packets}")

        generator = FileHandler.split_on_packets(path, block_fields["BLOCK_SIZE"])
        if generator:

            if self.__transaction_pool.handle_congestions(request):
                generator.close()
                return
            self.__work_timer.reset()
            index = 1
            for payload in generator:
                response = CoapTemplates.BYTES_RESPONSE.value_with(request.token, request.message_id + index)
                response.payload = payload
                response.skt = request.skt
                response.sender_ip_port = request.sender_ip_port
                response.options[CoapOptionDelta.BLOCK2.value] = (
                    CoapPacket.encode_option_block(index - 1, int(index != total_packets), block_fields["SZX"])
                )
                response.options[CoapOptionDelta.LOCATION_PATH.value] = '/' + path.split('/')[-1]

                if self.__transaction_pool.handle_congestions(response, index == total_packets):
                    generator.close()
                    break

                self.__transaction_pool.add_transaction(
                    response,
                    request.message_id
                )

                logger.debug(f"Send -> {response}")

                index += 1

            logger.log(f"> Upload of the file completed in {self.__work_timer.elapsed_time()}", LogColor.CYAN)
            retransmissions = self.__transaction_pool.get_number_of_retransmissions(request)
            logger.debug(f"<{request.sender_ip_port}->{request.token}> Retransmissions : {retransmissions}")

            self.__transaction_pool.finish_overall_transaction(request)
        else:
            pass

    def split_on_paths_and_send(self, request: CoapPacket, path: str, relative_to: str):
        with CoapTimer("TOTAL_PATHS"):
            paths = FileHandler.split_on_paths(path, relative_to)
        if paths:
            index = 1
            for path in paths:
                response = CoapTemplates.STR_PATH_RESPONSE.value_with(request.token, index)
                response.payload = path
                response.skt = request.skt
                response.sender_ip_port = request.sender_ip_port
                response.options[CoapOptionDelta.BLOCK2.value] = (
                    CoapPacket.encode_option_block(index - 1, int(index != len(paths)))
                )

                if self.__transaction_pool.handle_congestions(response, index == len(paths)):
                    break

                self.__transaction_pool.add_transaction(
                    response,
                    request.message_id,
                )
                index += 1
        else:
            pass

    def get_files_list(self) -> list:
        return self.__content_dict["file"]

    def get_folders_list(self) -> list:
        return self.__content_dict["folder"]

    def clear_content(self):
        self.__content_dict = {"folder": [], "file": []}
