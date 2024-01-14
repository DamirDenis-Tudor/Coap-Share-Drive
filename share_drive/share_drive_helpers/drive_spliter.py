import os

from coap_core.coap_packet.coap_config import CoapOptionDelta
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_transaction.coap_transaction_pool import CoapTransactionPool
from coap_core.coap_utilities.coap_logger import logger, LogColor
from coap_core.coap_utilities.coap_singleton import CoapSingletonBase
from coap_core.coap_utilities.coap_timer import CoapTimer
from share_drive.share_drive_helpers.drive_templates import DriveTemplates
from share_drive.share_drive_helpers.drive_utils import DriveUtilities


class DriveSpliter(CoapSingletonBase):
    """
    DriveSpliter is a class responsible for splitting and sending CoAP packets based on certain conditions.
    It utilizes CoapTransactionPool and CoapTimer for managing transactions and timing, respectively.

    Author: Damir Denis-Tudor
    """

    def __init__(self):
        """
        Constructor for DriveSpliter.

        Initializes the transaction pool and work timer.
        """
        self.__transaction_pool = CoapTransactionPool()
        self.__work_timer = CoapTimer()

    def split_on_bytes_and_send(self, request: CoapPacket, path: str):
        """
        Split a file into packets and send them as CoAP responses.

        Parameters:
        - request (CoapPacket): The original CoAP packet that triggered the splitting and sending.
        - path (str): The path to the file or folder to be split and sent.
        """
        # Extract block-related options from the CoAP packet
        send_block_option = request.get_option_code()
        block_fields = CoapPacket.decode_option_block(request.options[send_block_option])

        # Check if the path is a folder and compress it
        to_be_deleted = None
        if DriveUtilities.folder_exists(path):
            logger.debug(f"<{request.token}> Zipping the folder: {path}")
            logger.log(f"> Zipping the folder: {path}")
            path = DriveUtilities.compress_folder(path)
            to_be_deleted = path

        # Get total packets based on block size
        total_packets = DriveUtilities.get_total_packets(path, block_fields["BLOCK_SIZE"])
        logger.debug(f"<{request.token}> Number of packets that will be sent: {total_packets}")
        logger.log(f"> Uploading the file with {total_packets} packets...", LogColor.CYAN)

        # Generate file data packets using a generator
        generator = DriveUtilities.split_on_packets(path, block_fields["BLOCK_SIZE"])
        if generator:
            self.__work_timer.reset()
            for index, payload in enumerate(generator, start=1):

                # Create a CoAP response packet with payload and necessary options
                response = DriveTemplates.CONTENT_RESPONSE.value_with(
                    request.token, request.message_id + index,
                    request.skt, request.sender_ip_port
                )
                response.payload = payload
                response.options[CoapOptionDelta.LOCATION_PATH.value] = os.path.basename(path)
                response.options[send_block_option] = (
                    CoapPacket.encode_option_block(index - 1, int(index != total_packets), block_fields["SZX"])
                )

                # For the first response send the total number of expected packets
                if index == 1:
                    response.options[request.get_size_code_based_on_option()] = total_packets

                response.encode()

                # Handle congestion and add the transaction to the pool
                if self.__transaction_pool.handle_congestions(response, index == total_packets):
                    generator.close()
                    return

                # add transaction
                self.__transaction_pool.add_transaction(response, request.message_id)

            del generator
            retransmissions = self.__transaction_pool.get_number_of_retransmissions(request)

            logger.debug(f"<{request.token}> Request finished in {self.__work_timer.elapsed_time()}"
                         f" with {retransmissions} retransmission.", LogColor.CYAN)

            logger.log(f"> Upload completed in {self.__work_timer.elapsed_time()} with {retransmissions}"
                       f" retransmission.", LogColor.CYAN)

            # Delete the compressed file if applicable
            if to_be_deleted:
                DriveUtilities.delete_file(to_be_deleted)

            # Finish the overall transaction in the transaction pool
            self.__transaction_pool.finish_overall_transaction(request)
        else:
            pass

    def split_on_paths_and_send(self, request: CoapPacket, path: str, relative_to: str):
        """
        Split a list of paths and send them as CoAP responses.

        Parameters:
        - request (CoapPacket): The original CoAP packet that triggered the splitting and sending.
        - path (str): The path to the source directory for path extraction.
        - relative_to (str): The common prefix to be removed from paths.
        """
        # Split paths based on the source directory and common prefix
        paths = DriveUtilities.split_on_paths(path, relative_to)

        self.__work_timer.reset()
        for index, path in enumerate(paths, start=1):

            # Create a CoAP response packet with payload and necessary options
            response = DriveTemplates.PATH_RESPONSE.value_with(request.token, index)
            response.payload = path
            response.skt = request.skt
            response.sender_ip_port = request.sender_ip_port
            response.options[request.get_option_code()] = (
                CoapPacket.encode_option_block(index - 1, int(index != len(paths)))
            )

            # Handle congestion and add the transaction to the pool
            if self.__transaction_pool.handle_congestions(response, index - 1 == len(paths)):
                break

            # register transaction
            self.__transaction_pool.add_transaction(response, request.message_id)

        retransmissions = self.__transaction_pool.get_number_of_retransmissions(request)
        logger.debug(f"Sync completed in {self.__work_timer.elapsed_time()} with {retransmissions}", LogColor.CYAN)
