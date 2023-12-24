import threading

from source.Packet.CoapPacket import CoapPacket
from source.Packet.CoapTemplates import CoapTemplates
from source.Utilities.Logger import logger
from source.Utilities.Timer import Timer


class CoapTransaction:
    ACK_TIMEOUT = 2
    ACK_RANDOM_FACTOR = 1.5
    MAX_RETRANSMIT = 2
    MAX_RETRANSMISSION_SPAN = (ACK_TIMEOUT * ((2 ** MAX_RETRANSMIT) - 1) * ACK_RANDOM_FACTOR)
    MAX_RETRANSMISSION_WAIT = (ACK_TIMEOUT * ((2 ** (MAX_RETRANSMIT + 1)) - 1) * ACK_RANDOM_FACTOR)

    NO_ACTION = 0
    RETRANSMISSION = 1
    FAILED_TRANSACTION = 2

    RETRANSMISSIONS= 0

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
                reset_response = CoapTemplates.FAILED_REQUEST.value_with(self.request.token, self.parent_msg_id)
                self.__request.skt.sendto(reset_response.encode(), self.__request.sender_ip_port)
                return CoapTransaction.FAILED_TRANSACTION

            CoapTransaction.RETRANSMISSIONS += 1
            logger.log(f"RETRANSMISSIONS {CoapTransaction.RETRANSMISSIONS}")
            self.__request.skt.sendto(self.__request.encode(), self.__request.sender_ip_port)

            return CoapTransaction.RETRANSMISSION

        return CoapTransaction.NO_ACTION


class CoapTransactionPool:
    """
    Singleton class the work as an Observer to all transactions, more than that it gives flexibility
    to access a certain transactions in any context.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Create a single instance of TransactionsPool using the singleton pattern.

        Returns:
        - TransactionsPool - The instance of TransactionsPool.
        """
        # with cls._lock:
        # Create a single instance of TransactionsPool if it doesn't exist
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self._lock:
            if not hasattr(self, 'initialized'):
                self.__transaction_dict: dict[tuple[bytes, int], CoapTransaction] = {}
                self.__new_added: dict[tuple[bytes, int], CoapTransaction] = {}
                self.__finished_transactions: dict[tuple[bytes, int]] = {}
                self.__failed_transactions: list[bytes] = []
                self.__is_running = True
                self.initialized = True

    def add_transaction(self, transaction: CoapTransaction):
        key = (transaction.request.token, transaction.request.message_id)

        # An acknowledgment for a packet might be received earlier
        # than the moment when the transaction is added to the pool.
        if key not in self.__finished_transactions:
            self.__transaction_dict[key] = transaction
            # logger.log(f"Added transaction: {key[1]}")
            self.__new_added[key] = transaction

    def finish_transaction(self, token: bytes, msg_id: int):
        # todo add ip too
        key = (token, msg_id)
        self.__finished_transactions[key] = msg_id

        # there is no need to delete the transaction if it has already finished.
        if key in self.__transaction_dict:
            del self.__transaction_dict[key]

    def finish_all_transactions(self, token: bytes):
        self.__failed_transactions.append(token)
        self.__transaction_dict = {(t.request.token, t.request.message_id):
                                       t for t in self.__transaction_dict.values() if not (t.request.token == token)}

    def transaction_previously_failed(self, token: bytes):
        if token in self.__failed_transactions:
            self.__failed_transactions.remove(token)
            return True
        return False

    def solve_transactions(self):
        if len(self.__transaction_dict) > 0:
            keys_copy = list(self.__transaction_dict.keys())

            for key in keys_copy:
                if key[0] not in self.__failed_transactions and key not in self.__finished_transactions:
                    match self.__transaction_dict[key].run_transaction():
                        case CoapTransaction.FAILED_TRANSACTION:
                            self.finish_all_transactions(key[0])
                        case _:
                            pass

            self.__finished_transactions.clear()

    def get_number_of_transactions(self):
        return len(self.__transaction_dict)
