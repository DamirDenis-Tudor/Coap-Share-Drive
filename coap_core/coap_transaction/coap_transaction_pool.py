import time

from coap_core.coap_transaction import COAP_CONCURRENT_TRANSACTIONS
from coap_core.coap_packet.coap_packet import CoapPacket
from coap_core.coap_transaction.coap_transaction import CoapTransaction
from coap_core.coap_utilities.coap_singleton import CoapSingletonBase
from coap_core.coap_utilities.coap_timer import CoapTimer


class CoapTransactionPool(CoapSingletonBase):
    """
    Represents a pool of CoAP transactions, managing their execution, completion, and retransmissions.
    """

    def __init__(self):
        """
        Initializes the CoapTransactionPool instance with necessary attributes.
        """
        self.__is_running = True

        # Dictionaries to track various transaction states
        self.__overall_finished_transactions: dict = {}
        self.__finished_transactions: dict[tuple] = {}
        self.__failed_transactions: dict[tuple] = {}
        self.__transaction_dict: dict[tuple, CoapTransaction] = {}
        self.__retransmissions: dict = {}

    def handle_congestions(self, packet: CoapPacket, last_packet: bool = False):
        """
        Handles congestion by checking overall transaction failure and managing concurrent transactions.

        Args:
            packet (CoapPacket): The CoAP packet to handle.
            last_packet (bool): Whether this is the last packet in a series.

        Returns:
            bool: True if overall transaction failed; False otherwise.
        """
        if self.is_overall_transaction_failed(packet):
            return True

        # Wait until there's room for a new transaction
        while len(self.__transaction_dict) >= COAP_CONCURRENT_TRANSACTIONS:
            pass

        if last_packet:
            # Wait until all transactions are finished
            while len(self.__transaction_dict) != 0:
                pass

        return False

    def add_transaction(self, packet: CoapPacket, parent_msg_id=0):
        """
        Adds a new CoAP transaction to the pool.

        Args:
            packet (CoapPacket): The CoAP packet to initiate the transaction.
            parent_msg_id (int): The parent message ID for the transaction.

        Notes:
            Initiates the request and adds the transaction to the pool.
        """
        # Make the initial request
        packet.send()

        transaction = CoapTransaction(packet, parent_msg_id)

        key = packet.work_id()

        # An acknowledgment for a packet might be received earlier
        # than the moment when the transaction is added to the pool.
        if key not in self.__finished_transactions:
            self.__transaction_dict[key] = transaction

    def solve_transactions(self):
        """
        Processes and solves pending CoAP transactions.

        Notes:
            Uses CoapTimer for timing purposes and handles failed transactions and retransmissions.
        """
        with CoapTimer():
            if len(self.__transaction_dict) > 0:
                keys_copy = list(self.__transaction_dict.keys())

                for key in keys_copy:
                    if ((key[0], key[1]) not in self.__failed_transactions and
                            key not in self.__finished_transactions):

                        match self.__transaction_dict[key].run_transaction():
                            case CoapTransaction.FAILED_TRANSACTION:
                                self.set_overall_transaction_failure(self.__transaction_dict[key].request)
                                self.clean_failed_transactions(self.__transaction_dict[key].request)
                                break

                            case CoapTransaction.RETRANSMISSION:
                                identifier = (key[0], key[1])
                                if identifier not in self.__retransmissions:
                                    self.__retransmissions[identifier] = 1
                                else:
                                    self.__retransmissions[identifier] += 1

                self.__finished_transactions.clear()

    def finish_transaction(self, packet: CoapPacket):
        """
        Marks a CoAP transaction as finished.

        Args:
            packet (CoapPacket): The CoAP packet associated with the finished transaction.
        """
        key = packet.work_id()

        self.__finished_transactions[key] = time.time()

        # There is no need to delete the transaction if it has already finished.
        if key in self.__transaction_dict:
            del self.__transaction_dict[key]

    def is_transaction_finished(self, packet: CoapPacket):
        """
        Checks if a specific CoAP transaction is finished.

        Args:
            packet (CoapPacket): The CoAP packet associated with the transaction.

        Returns:
            bool: True if the transaction is finished; False otherwise.
        """
        key = packet.work_id()
        return key in self.__finished_transactions

    def finish_overall_transaction(self, packet: CoapPacket):
        """
        Marks the overall CoAP transaction as finished.

        Args:
            packet (CoapPacket): The CoAP packet associated with the overall finished transaction.
        """
        if packet.general_work_id() not in self.__overall_finished_transactions:
            self.__overall_finished_transactions[packet.general_work_id()] = time.time()

    def wait_util_finish(self, packet: CoapPacket):
        """
        Waits until the overall CoAP transaction is finished.

        Args:
            packet (CoapPacket): The CoAP packet associated with the overall transaction.
        """
        while packet.general_work_id() not in self.__overall_finished_transactions:
            time.sleep(0.5)

    def is_overall_transaction_failed(self, packet: CoapPacket):
        """
        Checks if the overall CoAP transaction has failed.

        Args:
            packet (CoapPacket): The CoAP packet associated with the overall transaction.

        Returns:
            bool: True if the overall transaction has failed; False otherwise.
        """
        return packet.general_work_id() in self.__failed_transactions

    def set_overall_transaction_failure(self, packet: CoapPacket):
        """
        Marks the overall CoAP transaction as failed.

        Args:
            packet (CoapPacket): The CoAP packet associated with the overall failed transaction.
        """
        self.__failed_transactions[packet.general_work_id()] = time.time()

    def clean_failed_transactions(self, packet: CoapPacket):
        """
        Cleans up failed transactions associated with a specific CoAP packet.

        Args:
            packet (CoapPacket): The CoAP packet used to filter and remove failed transactions.

        Notes:
            Removes transactions from the transaction dictionary based on the provided packet's general work ID.
        """
        # Create a new transaction dictionary excluding failed transactions related to the specified packet
        self.__transaction_dict = {
            t.request.work_id(): time.time() for t in self.__transaction_dict.values()
            if t.request.general_work_id() != packet.general_work_id()
        }

    def get_number_of_retransmissions(self, packet: CoapPacket):
        """
        Retrieves the number of retransmissions for a specific CoAP packet.

        Args:
            packet (CoapPacket): The CoAP packet associated with the transaction.

        Returns:
            int: The number of retransmissions for the given packet.
        """
        general_id = packet.general_work_id()

        if general_id in self.__retransmissions:
            return self.__retransmissions[general_id]
        return 0
