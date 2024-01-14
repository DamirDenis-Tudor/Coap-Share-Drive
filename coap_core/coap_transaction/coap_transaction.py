from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_packet.coap_templates import CoapTemplates
from coap_core.coap_transaction import ACK_TIMEOUT, MAX_RETRANSMISSION_SPAN, MAX_RETRANSMIT
from coap_core.coap_utilities.coap_logger import logger
from coap_core.coap_utilities.coap_timer import CoapTimer


class CoapTransaction:
    """
    The `CoapTransaction` class represents a CoAP transaction and handles retransmission logic.

    Note:
    - This class assumes the presence of the `CoapPacket`, `CoapTimer`, `CoapTemplates`, and `logger` entities.
    - The `run_transaction` method implements the retransmission logic based on CoAP specifications.
    """

    # Transaction States
    NO_ACTION = 0
    RETRANSMISSION = 1
    FAILED_TRANSACTION = 2

    # Constructor
    def __init__(self, request: CoapPacket, parent_msg_id: int):
        """
        Initializes a CoapTransaction instance.

        :param request: The CoAP request packet.
        :param parent_msg_id: The parent message ID.
        """
        self.__request: CoapPacket = request
        self.__parent_msg_id = parent_msg_id
        self.__timer: CoapTimer = CoapTimer().reset()
        self.__ack_timeout = ACK_TIMEOUT
        self.__transmit_time_span = 0
        self.__retransmission_counter = 0

    # Properties
    @property
    def request(self) -> CoapPacket:
        return self.__request

    @property
    def parent_msg_id(self) -> int:
        return self.__parent_msg_id

    @property
    def timer(self) -> CoapTimer:
        return self.__timer

    @property
    def ack_timeout(self) -> float:
        return self.__ack_timeout

    @ack_timeout.setter
    def ack_timeout(self, value: float):
        self.__ack_timeout = value

    @property
    def transmit_time_span(self) -> int:
        return self.__transmit_time_span

    @transmit_time_span.setter
    def transmit_time_span(self, value: int):
        self.__transmit_time_span = value

    @property
    def retransmission_counter(self) -> int:
        return self.__retransmission_counter

    @retransmission_counter.setter
    def retransmission_counter(self, value: int):
        self.__retransmission_counter = value

    # Methods
    def run_transaction(self) -> int:
        """
        Runs the CoAP transaction, handling retransmissions and checking for failure.

        :return: Transaction state (NO_ACTION, RETRANSMISSION, FAILED_TRANSACTION).
        """
        if self.__timer.elapsed_time() > self.__ack_timeout:
            self.__transmit_time_span += self.__timer.elapsed_time()

            # Update ACK timeout and retransmission counter
            self.__ack_timeout *= 2
            self.__retransmission_counter += 1

            # Reset the timer for the next iteration
            self.__timer.reset()

            # Check if retransmission limits are reached
            if (self.__transmit_time_span > MAX_RETRANSMISSION_SPAN or
                    self.__retransmission_counter > MAX_RETRANSMIT):
                reset_response = CoapTemplates.FAILED_REQUEST.value_with(self.__request.token, self.parent_msg_id)
                self.__request.skt.sendto(reset_response.encode(), self.__request.sender_ip_port)

                logger.log(f"Transaction failed: {self.__request}")
                return CoapTransaction.FAILED_TRANSACTION

            self.__request.skt.sendto(self.__request.encode(), self.__request.sender_ip_port)
            logger.debug(f"Retransmission of {self.__request}")
            return CoapTransaction.RETRANSMISSION

        return CoapTransaction.NO_ACTION
