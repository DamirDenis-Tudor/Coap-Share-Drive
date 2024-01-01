import os
import random
import threading

from source.coap_core.coap_packet.coap_config import CoapOptionDelta
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_packet.coap_templates import CoapTemplates
from source.coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from source.coap_core.coap_utilities.coap_logger import logger
from source.coap_core.coap_utilities.coap_timer import CoapTimer


class FileHandler:
    _instance = None
    _lock = threading.Lock()

    @staticmethod
    def file_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isdir(file_path)

    @staticmethod
    def iterate_folder(source: str) -> list[str]:
        f = []
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                f.append(file_path)

        return f

    @staticmethod
    def split_file_on_packets(file_path: str, block_size: int):
        with open(file_path, 'rb') as file:
            while True:
                file_data = file.read(block_size)
                if not file_data:
                    break
                yield file_data

    @staticmethod
    def get_total_packets(file_path: str, block_size: int) -> int:
        file_size = os.path.getsize(file_path)
        total_packets = (file_size + block_size - 1) // block_size
        return total_packets

    FINISH_ASSEMBLY = 0
    CONTINUE_ASSEMBLY = 1
    ALREADY_ASSEMBLED = 2

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        with self._lock:
            if not hasattr(self, 'initialized'):
                self.initialized = True
                self.__transaction_pool = CoapTransactionPool()
                self.__in_assembly: dict[tuple, dict] = {}
                self.__assembled: list[tuple] = []

    def handle_packets(self, packet: CoapPacket, path: str) -> int:
        with FileHandler._lock:
            # path
            # add conditions
            option = CoapPacket().decode_option_block(packet.options[CoapOptionDelta.BLOCK2.value])

            if packet.general_work_id() not in self.__in_assembly:  # register file operation-related packets
                self.__in_assembly[packet.general_work_id()] = {
                    "TOTAL_RESPONSES": 0,
                    "WRITE_INDEX": 0,
                    "RECEIVED_PACKETS": {}
                }

            operation_dict = self.__in_assembly[packet.general_work_id()]

            logger.log(f"Handle {operation_dict['WRITE_INDEX']} -> {packet} .")

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

            if packet.general_work_id() in self.__assembled:
                return FileHandler.ALREADY_ASSEMBLED

            if operation_dict["TOTAL_RESPONSES"] != 0:
                if operation_dict["WRITE_INDEX"] - 1 == operation_dict["TOTAL_RESPONSES"]:
                    self.__in_assembly.pop(packet.general_work_id())
                    self.__assembled.append(packet.general_work_id())

                    logger.log(f"Assembly of {packet.general_work_id()} finished.")

                    return FileHandler.FINISH_ASSEMBLY

            return FileHandler.CONTINUE_ASSEMBLY

    def get_sender(self):
        def split_and_send(request: CoapPacket, path: str):
            with CoapTimer(f"<{request.sender_ip_port}->{request.token}> get_request"):
                block_fields = CoapPacket.decode_option_block(request.options[CoapOptionDelta.BLOCK1.value])

                total_packets = FileHandler.get_total_packets(path, block_fields["BLOCK_SIZE"])
                generator = FileHandler.split_file_on_packets(path, block_fields["BLOCK_SIZE"])

                logger.log(f"<{request.sender_ip_port}->{request.token}> Total packets: {total_packets}")
                if generator:

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

                        status = self.__transaction_pool.handle_congestions(
                                response,
                                index == total_packets
                        )

                        if status == CoapTransactionPool.FAIL_TO_ADD:
                            logger.log("Transmission failed.")
                            generator.close()

                        self.__transaction_pool.add_transaction(
                            response,
                            request.message_id
                        )

                        index += 1

                    retransmissions = CoapTransactionPool().get_number_of_retransmissions(request)
                    logger.log(f"<{request.sender_ip_port}->{request.token}> Retransmissions : {retransmissions}")
                else:
                    pass

        return split_and_send

