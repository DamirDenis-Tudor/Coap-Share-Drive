from source.Packet.CoapPacket import CoapPacket
from source.Packet.CoapTemplates import CoapTemplates
from source.Utilities.Logger import logger
from source.Utilities.Timer import Timer


class CoapTransaction:
    ACK_TIMEOUT = 2
    ACK_RANDOM_FACTOR = 1.5
    MAX_RETRANSMIT = 4
    MAX_RETRANSMISSION_SPAN = (ACK_TIMEOUT * ((2 ** MAX_RETRANSMIT) - 1) * ACK_RANDOM_FACTOR)
    MAX_RETRANSMISSION_WAIT = (ACK_TIMEOUT * ((2 ** (MAX_RETRANSMIT + 1)) - 1) * ACK_RANDOM_FACTOR)

    NO_ACTION = 0
    RETRANSMISSION = 1
    FAILED_TRANSACTION = 2

    def __init__(self, request: CoapPacket, parent_msg_id: int):
        self.__request: CoapPacket = request
        self.__parent_msg_id = parent_msg_id
        self.__timer: Timer = Timer().reset()
        self.__ack_timeout = CoapTransaction.ACK_TIMEOUT
        self.__transmit_time_span = 0
        self.__retransmission_counter = 0

    @property
    def request(self) -> CoapPacket:
        return self.__request

    @property
    def parent_msg_id(self) -> int:
        return self.__parent_msg_id

    @property
    def timer(self) -> Timer:
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

    def run_transaction(self) -> int:
        if self.__timer.elapsed_time() > self.__ack_timeout:
            self.__transmit_time_span += self.__timer.elapsed_time()

            # Update ACK timeout and retransmission counter
            self.__ack_timeout *= 2
            self.__retransmission_counter += 1

            # Reset the timer for the next iteration
            self.__timer.reset()

            # Check if retransmission limits are reached
            if (self.__transmit_time_span > CoapTransaction.MAX_RETRANSMISSION_SPAN or
                    self.__retransmission_counter > CoapTransaction.MAX_RETRANSMIT):
                reset_response = CoapTemplates.FAILED_REQUEST.value_with(self.__request.token, self.parent_msg_id)
                self.__request.skt.sendto(reset_response.encode(), self.__request.sender_ip_port)

                logger.log(f"Transaction failed: {self.__request}")
                return CoapTransaction.FAILED_TRANSACTION

            self.__request.skt.sendto(self.__request.encode(), self.__request.sender_ip_port)

            return CoapTransaction.RETRANSMISSION

        return CoapTransaction.NO_ACTION
