import random
import threading
import time
from _socket import IPPROTO_UDP
from socket import socket, AF_INET, SOCK_DGRAM

from source.Packet.CoapPacket import CoapPacket
from source.Transaction.CoapTransaction import CoapTransaction
from source.Utilities.Logger import logger
from source.Utilities.Timer import Timer


class CoapTransactionPool:
    SUCCESSFULLY_ADDED = 1
    FAIL_TO_ADD = 2

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
                self.initialized = True

                self.__is_running = True

                self.__finished_transactions: dict[tuple] = {}
                self.__failed_transactions: dict[tuple] = {}
                self.__transaction_dict: dict[tuple, CoapTransaction] = {}
                self.__retransmissions: dict = {}

    def handle_congestions(self, packet: CoapPacket, last_packet: bool):
        if self.transaction_previously_failed(packet):
            return CoapTransactionPool.FAIL_TO_ADD

        while len(self.__transaction_dict) >= 100:
            pass

        if last_packet:
            while len(self.__transaction_dict) != 0:
                pass

        return CoapTransactionPool.SUCCESSFULLY_ADDED

    def add_transaction(self, packet: CoapPacket, parent_msg_id=None):
        transaction = CoapTransaction(packet, parent_msg_id)
        # make the initial request
        transaction.request.skt.sendto(transaction.request.encode(), transaction.request.sender_ip_port)

        key = packet.short_term_work_id(packet.get_block_id())

        # An acknowledgment for a packet might be received earlier
        # than the moment when the transaction is added to the pool.
        if key not in self.__finished_transactions:
            self.__transaction_dict[key] = transaction

    def solve_transactions(self):
        with Timer():
            if len(self.__transaction_dict) > 0:
                keys_copy = list(self.__transaction_dict.keys())

                for key in keys_copy:
                    if ((key[0], key[1]) not in self.__failed_transactions and
                            key not in self.__finished_transactions):

                        match self.__transaction_dict[key].run_transaction():
                            case CoapTransaction.FAILED_TRANSACTION:
                                self.__failed_transactions[(key[0], key[1])] = time.time()

                                self.__transaction_dict = {
                                    (t.request.sender_ip_port, t.request.token, t.request.message_id): t
                                    for t in self.__transaction_dict.values() if
                                    t.request.token != key[1] and t.request.sender_ip_port != key[0]
                                }
                                break

                            case CoapTransaction.RETRANSMISSION:
                                identifier = (key[0], key[1])
                                if identifier not in self.__retransmissions:
                                    self.__retransmissions[identifier] = 1
                                else:
                                    self.__retransmissions[identifier] += 1

                self.__finished_transactions.clear()

    def finish_transaction(self, packet: CoapPacket):
        if packet.payload == b'':
            key = packet.short_term_work_id()
        else:
            key = packet.short_term_work_id(int(packet.payload))

        self.__finished_transactions[key] = time.time()

        # there is no need to delete the transaction if it has already finished.
        if key in self.__transaction_dict:
            del self.__transaction_dict[key]

    def transaction_previously_failed(self, packet: CoapPacket):
        key = packet.general_work_id()
        if key in self.__failed_transactions:
            self.__failed_transactions.pop(key)
            return True
        return False

    def get_number_of_retransmissions(self, packet: CoapPacket):
        general_id = packet.general_work_id()
        if general_id in self.__retransmissions:
            return self.__retransmissions[general_id]
        return 0
