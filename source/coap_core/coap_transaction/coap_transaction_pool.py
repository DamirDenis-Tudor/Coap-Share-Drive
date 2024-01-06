import threading
import time

from source.coap_core.coap_utilities.coap_singleton import CoapSingletonBase
from source.coap_core.coap_packet.coap_packet import CoapPacket
from source.coap_core.coap_transaction.coap_transaction import CoapTransaction
from source.coap_core.coap_utilities.coap_timer import CoapTimer


class CoapTransactionPool(CoapSingletonBase):
    SUCCESSFULLY_ADDED = 1
    FAIL_TO_ADD = 2

    def __init__(self):
        self.__is_running = True

        self.__overall_finished_transactions: dict = {}
        self.__finished_transactions: dict[tuple] = {}
        self.__failed_transactions: dict[tuple] = {}
        self.__transaction_dict: dict[tuple, CoapTransaction] = {}
        self.__retransmissions: dict = {}

    def handle_congestions(self, packet: CoapPacket, last_packet: bool = False):
        if self.is_overall_transaction_failed(packet):
            return True

        while len(self.__transaction_dict) >= 5000:
            pass

        if last_packet:
            while len(self.__transaction_dict) != 0:
                pass
            
        return False

    def add_transaction(self, packet: CoapPacket, parent_msg_id=0):
        # make the initial request
        packet.skt.sendto(packet.encode(), packet.sender_ip_port)

        transaction = CoapTransaction(packet, parent_msg_id)

        key = packet.short_term_work_id(packet.get_block_id())

        # An acknowledgment for a packet might be received earlier
        # than the moment when the transaction is added to the pool.
        if key not in self.__finished_transactions:
            self.__transaction_dict[key] = transaction

    def is_transaction_finished(self, packet: CoapPacket):
        key = packet.short_term_work_id(packet.get_block_id())
        return key in self.__finished_transactions

    def solve_transactions(self):
        with CoapTimer():
            if len(self.__transaction_dict) > 0:
                keys_copy = list(self.__transaction_dict.keys())

                for key in keys_copy:
                    if ((key[0], key[1]) not in self.__failed_transactions and
                            key not in self.__finished_transactions):

                        match self.__transaction_dict[key].run_transaction():
                            case CoapTransaction.FAILED_TRANSACTION:
                                self.set_overall_transaction_failure(self.__transaction_dict[key].request)

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

    def finish_overall_transaction(self, packet: CoapPacket):
        self.__overall_finished_transactions[packet.general_work_id()] = time.time()

    def wait_util_finish(self, packet: CoapPacket):
        while packet.general_work_id() not in self.__overall_finished_transactions:
            time.sleep(0.1)

    def is_overall_transaction_failed(self, packet: CoapPacket):
        return packet.general_work_id() in self.__failed_transactions

    def set_overall_transaction_failure(self, packet: CoapPacket):
        self.__failed_transactions[packet.general_work_id()] = time.time()

    def get_number_of_retransmissions(self, packet: CoapPacket):
        general_id = packet.general_work_id()

        if general_id in self.__retransmissions:
            return self.__retransmissions[general_id]
        return 0
