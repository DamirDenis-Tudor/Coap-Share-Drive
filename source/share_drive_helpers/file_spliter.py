import os
import zipfile

from coap_core.coap_packet.coap_config import CoapOptionDelta
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_packet.coap_templates import CoapTemplates
from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from coap_core.coap_utilities.coap_logger import logger, LogColor
from coap_core.coap_utilities.coap_singleton import CoapSingletonBase
from coap_core.coap_utilities.coap_timer import CoapTimer


class FileSpliter(CoapSingletonBase):
    @staticmethod
    def file_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isdir(file_path)

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

    @staticmethod
    def compress_folder(input_folder):
        output_zip = f"{input_folder}.zip"
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_STORED) as zip_file:
            for folder, folders, filenames in os.walk(input_folder):
                for filename in filenames:
                    file_path = os.path.join(folder, filename)
                    arcname = os.path.relpath(file_path, input_folder)
                    zip_file.write(file_path, arcname)
        logger.log(output_zip)
        return output_zip

    @staticmethod
    def decompress_folder(zip_file_path: str):
        output_folder = zip_file_path.split(".zip")[0]
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)

    @staticmethod
    def delete_file(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.debug(f"Error deleting file '{file_path}': {e}")

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

    def __init__(self):
        self.__transaction_pool = CoapTransactionPool()
        self.__work_timer = CoapTimer()

    def split_on_bytes_and_send(self, request: CoapPacket, path: str):
        send_block_option = request.get_option_code()
        block_fields = CoapPacket.decode_option_block(request.options[send_block_option])

        try:
            remote_path = request.options[CoapOptionDelta.URI_PATH.value].split(":")[1] + '/' + path.split('/')[-1]
        except Exception:
            remote_path = '/' + path.split('/')[-1]

        to_be_deleted = None
        if FileSpliter.folder_exists(path):
            logger.debug(f"<{request.token}> Zipping the folder: {path}")
            logger.log(f"> Zipping the folder: {path}")
            path = FileSpliter.compress_folder(path)
            to_be_deleted = path

        total_packets = FileSpliter.get_total_packets(path, block_fields["BLOCK_SIZE"])
        logger.debug(f"<{request.token}> Number of packets the will be send: {total_packets}")
        logger.log(f" > Uploading the file with {total_packets} packets...", LogColor.CYAN)

        generator = FileSpliter.split_on_packets(path, block_fields["BLOCK_SIZE"])
        if generator:
            self.__work_timer.reset()
            index = 1

            for payload in generator:
                response = CoapTemplates.CONTENT_BYTES_RESPONSE.value_with(request.token, request.message_id + index)
                response.payload = payload
                response.skt = request.skt
                response.sender_ip_port = request.sender_ip_port
                response.options[CoapOptionDelta.LOCATION_PATH.value] = remote_path
                response.options[send_block_option] = (
                    CoapPacket.encode_option_block(index - 1, int(index != total_packets), block_fields["SZX"])
                )
                if index == 1:
                    response.options[request.get_size_code_based_on_option()] = total_packets

                if self.__transaction_pool.handle_congestions(response, index == total_packets):
                    generator.close()
                    return

                self.__transaction_pool.add_transaction(response, request.message_id)

                index += 1

            retransmissions = self.__transaction_pool.get_number_of_retransmissions(request)

            logger.debug(f"<{request.token}> Request finished in {self.__work_timer.elapsed_time()}"
                         f" with {retransmissions} retransmission.", LogColor.CYAN)

            logger.log(f"> Upload completed in {self.__work_timer.elapsed_time()} with {retransmissions}"
                       f" retransmission.", LogColor.CYAN)
            if to_be_deleted:
                FileSpliter.delete_file(to_be_deleted)
            self.__transaction_pool.finish_overall_transaction(request)
        else:
            pass

    def split_on_paths_and_send(self, request: CoapPacket, path: str, relative_to: str):
        paths = FileSpliter.split_on_paths(path, relative_to)
        if paths:
            index = 1
            self.__work_timer.reset()
            for path in paths:
                response = CoapTemplates.STR_PATH_RESPONSE.value_with(request.token, index)
                response.payload = path
                response.skt = request.skt
                response.sender_ip_port = request.sender_ip_port
                response.options[request.get_option_code()] = (
                    CoapPacket.encode_option_block(index - 1, int(index != len(paths)))
                )

                if self.__transaction_pool.handle_congestions(response, index == len(paths)):
                    break

                self.__transaction_pool.add_transaction(
                    response,
                    request.message_id,
                )

                index += 1
            retransmissions = self.__transaction_pool.get_number_of_retransmissions(request)
            logger.debug(f"Sync completed in {self.__work_timer.elapsed_time()} with {retransmissions}", LogColor.CYAN)
        else:
            pass
