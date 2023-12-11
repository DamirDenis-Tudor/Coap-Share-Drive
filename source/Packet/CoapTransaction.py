import threading
from asyncio import sleep
from socket import socket
from threading import Thread
from source.Packet.CoapPacket import CoapPacket
from source.Packet.CoapTemplates import CoapTemplates
from source.Utilities.Logger import logger
from source.Utilities.Timer import Timer


class CoapTransaction(Thread):
    """
    This class wraps a CON-type request and ensures that the request is received. An intersection must be made to
    update the transaction status (see: finish_transaction(), force_finish_transaction()).

    A separate task for CoAP transaction integrity is started, and this can lead to a self finish_transaction.
    Moreover, transactions are related by the token of the request; it's obvious that when a transaction fails, all
    related transactions must also fail.

    In a simplified manner, a CoapTransaction can be seen as a Subscriber, and CoapTransactionsPool can be seen
    as an Observer.
    """

    # for more details about those parameters visit: https://datatracker.ietf.org/doc/html/rfc7252#autoid-20
    ACK_TIMEOUT = 2
    ACK_RANDOM_FACTOR = 1.5
    MAX_RETRANSMIT = 4
    MAX_RETRANSMISSION_SPAN = (ACK_TIMEOUT * ((2 ** MAX_RETRANSMIT) - 1) * ACK_RANDOM_FACTOR)
    MAX_RETRANSMISSION_WAIT = (ACK_TIMEOUT * ((2 ** (MAX_RETRANSMIT + 1)) - 1) * ACK_RANDOM_FACTOR)

    def __init__(self, request: CoapPacket, initial_request_msg_id: int = None):
        """
        Constructor for CoapTransaction.

        Args:
        - request: CoapPacket - The CoAP packet representing the request.
        """
        # Store the CoAP request packet and initialize transaction flags
        super().__init__()
        self._request: CoapPacket = request
        self.__initial_request_msg_id = initial_request_msg_id

        self.__transaction_over = False
        self.__transaction_failed = False

        self.__skt: socket = self._request.skt
        self.__dest = self._request.sender_ip_port

        # Notify the TransactionsPool about the start of a new transaction
        CoapTransactionsPool().notify(self, "APPEND")

        # send the initial request
        self.__skt.sendto(self._request.encode(), self.__dest)

    def run(self):
        """
        Internal method to handle the timer and retransmission logic for the transaction.
        """

        # Initialize timer and timeout variables
        timer = Timer()
        timer.reset()

        ack_timeout = CoapTransaction.ACK_TIMEOUT
        transmit_time_span = 0
        retransmission_counter = 0

        while not self.__transaction_over:
            # Check if the timer has exceeded the ACK timeout
            if timer.elapsed_time() > ack_timeout:
                transmit_time_span += timer.elapsed_time()

                # Update ACK timeout and retransmission counter
                ack_timeout *= 2
                retransmission_counter += 1

                # Check if retransmission limits are reached
                if (transmit_time_span > CoapTransaction.MAX_RETRANSMISSION_SPAN or
                        retransmission_counter > CoapTransaction.MAX_RETRANSMIT):
                    self.force_finish_transaction()
                    return

                # Reset the timer for the next iteration
                timer.reset()

                # Resend the request
                self.__skt.sendto(self._request.encode(), self.__dest)
        self.finish_transaction()

    def finish_transaction(self):
        """
        Finish the transaction gracefully.
        """
        self.__transaction_over = True
        CoapTransactionsPool().notify(self, "REMOVE")

    def force_finish_transaction(self):
        """
        Forcefully finish the transaction.
        """
        self.__transaction_over = True
        self.__transaction_failed = True

        CoapTransactionsPool().notify(self, "REMOVE_ALL")

    def stop(self):
        self.__transaction_over = True

    def is_transaction_finished(self):
        """
        Check if the transaction is finished.

        Returns:
        - bool - True if the transaction is finished, False otherwise.
        """
        return self.__transaction_over

    def get_request(self) -> CoapPacket:
        """
        Get the associated CoapPacket request.

        Returns:
        - CoapPacket - The CoAP packet representing the request.
        """
        return self._request

    def get_initial_request_msg_id(self):
        return self.__initial_request_msg_id


class CoapTransactionsPool:
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
        with cls._lock:
            # Create a single instance of TransactionsPool if it doesn't exist
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        """
        Initialize TransactionsPool attributes only once.
        """
        with self._lock:
            # Initialize TransactionsPool attributes only if not previously initialized
            if not hasattr(self, 'initialized'):
                self.__transactions: list[CoapTransaction] = []
                self.__failed_transactions: list[int] = []
                self.initialized = True

    def failed_transmission(self, token):
        return token in self.__failed_transactions

    def has_transaction(self, token, message_id):
        for transaction in self.__transactions:
            if (transaction.get_request().token == token and
                    transaction.get_request().message_id == message_id):
                return True
        return False

    def get_transaction(self, token, message_id):
        for transaction in self.__transactions:
            if transaction.get_request().token == token and transaction.get_request().message_id == message_id:
                return transaction
        return None

    def finish_all_transactions(self, token):
        for transaction in self.__transactions:
            if transaction.get_request().token == token:
                transaction.finish_transaction()

    def notify(self, transaction, msg):
        """
        Notify the TransactionsPool about transactions.

        Args:
        - transaction: CoapTransaction - The CoAP transaction.
        - msg: str - The notification message (e.g., "APPEND", "REMOVE", "REMOVE_ALL").
        """
        with self._lock:
            # Print the notification message for debugging purposes
            if msg == "APPEND":
                if not self.failed_transmission(transaction.get_request().token):
                    self.__transactions.append(transaction)
                    transaction.start()
            elif msg == "REMOVE":
                if transaction in self.__transactions:
                    self.__transactions.remove(transaction)
            elif msg == "REMOVE_ALL":
                # add to failed transactions
                self.__failed_transactions.append(transaction.get_request().token)
                logger.log(f"REMOVE_ALL {self.__failed_transactions}")

                # Remove all transactions related to the specified transaction
                related_transaction = [x for x in self.__transactions
                                       if x.get_request().token == transaction.get_request().token]
                for trt in related_transaction:
                    if not trt.is_transaction_finished():
                        trt.stop()

                # Update the TransactionsPool with the remaining transactions
                self.__transactions = [x for x in self.__transactions
                                       if x.get_request().token != transaction.get_request().token]

                # send a reset message
                failed_global_transaction = CoapTemplates.FAILED_REQUEST.value_with(
                    transaction.get_request().token,
                    transaction.get_initial_request_msg_id()
                )

                transaction.get_request().skt.sendto(
                    failed_global_transaction.encode(),
                    transaction.get_request().sender_ip_port
                )
