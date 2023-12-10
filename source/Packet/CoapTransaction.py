import threading
from socket import socket
from threading import Thread
from source.Packet.CoapPacket import CoapPacket
from source.Utilities.Timer import Timer


class CoapTransaction:
    """
    This class wraps a CON type request and ensure that the request was received. An intersection must be made to
    update the transaction status( see: finish_transaction(), force_finish_transaction() )

    A separate task for coap transaction integrity is started and this thing can lead to a self finish_transaction.
    Moreover, transactions are related by the token of the request; it's obviously that when a transaction fail all
    related transactions must fail too.

    In a simplified manner a CoapTransaction can be seen as a Subscriber as well as CoapTransactionsPool can be seen
    as an Observer.
    """

    # for more details about those parameters visit: https://datatracker.ietf.org/doc/html/rfc7252#autoid-20
    ACK_TIMEOUT = 2
    ACK_RANDOM_FACTOR = 1.5
    MAX_RETRANSMIT = 4
    MAX_RETRANSMISSION_SPAN = (ACK_TIMEOUT * ((2 ** MAX_RETRANSMIT) - 1) * ACK_RANDOM_FACTOR)
    MAX_RETRANSMISSION_WAIT = (ACK_TIMEOUT * ((2 ** (MAX_RETRANSMIT + 1)) - 1) * ACK_RANDOM_FACTOR)

    def __init__(self, request):
        """
        Constructor for CoapTransaction.

        Args:
        - request: CoapPacket - The CoAP packet representing the request.
        """
        # Store the CoAP request packet and initialize transaction flags
        self._request: CoapPacket = request
        self.__transaction_over = False
        self.__transaction_failed = False

        # Notify the TransactionsPool about the start of a new transaction
        CoapTransactionsPool().notify(self, "APPEND")

        # Start a new thread to run the timer for transaction handling
        Thread(target=self.__run_timer).start()

    def __run_timer(self):
        """
        Internal method to handle the timer and retransmission logic for the transaction.
        """
        # Extract socket and destination information from the CoAP request
        skt: socket = self._request.skt
        dest = self._request.sender_ip_port

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
                    # Mark the transaction as failed and notify the TransactionsPool to remove all related transactions
                    self.__transaction_over = True
                    self.__transaction_failed = True
                    CoapTransactionsPool().notify(self, "REMOVE_ALL")
                    break

                # Reset the timer for the next iteration
                timer.reset()

                # Resend the request
                skt.sendto(self._request.encode(), dest)

        # Handle the end of the transaction
        if not self.__transaction_failed:
            # Notify the TransactionsPool to remove the current transaction
            CoapTransactionsPool().notify(self, "REMOVE")

    def finish_transaction(self):
        """
        Finish the transaction gracefully.
        """
        self.__transaction_over = True

    def force_finish_transaction(self):
        """
        Forcefully finish the transaction.
        """
        self.__transaction_over = True
        self.__transaction_failed = True

    def is_transaction_finished(self):
        """
        Check if the transaction is finished.

        Returns:
        - bool - True if the transaction is finished, False otherwise.
        """
        return self.__transaction_over

    def get_request(self):
        """
        Get the associated CoapPacket request.

        Returns:
        - CoapPacket - The CoAP packet representing the request.
        """
        return self._request


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
                self.__transactions = []
                self.initialized = True

    def notify(self, transaction, msg):
        """
        Notify the TransactionsPool about transactions.

        Args:
        - transaction: CoapTransaction - The CoAP transaction.
        - msg: str - The notification message (e.g., "APPEND", "REMOVE", "REMOVE_ALL").
        """
        with self._lock:
            # Print the notification message for debugging purposes
            print(msg)
            if msg == "APPEND":
                # Append the transaction to the pool
                self.__transactions.append(transaction)
            elif msg == "REMOVE":
                if transaction in self.__transactions:
                    # Remove the specified transaction from the pool
                    self.__transactions.remove(transaction)
            elif msg == "REMOVE_ALL":
                if transaction in self.__transactions:
                    # Remove all transactions related to the specified transaction
                    related_transaction = [x for x in self.__transactions
                                           if x.get_request().token == transaction.get_request().token]
                    for trt in related_transaction:
                        print(trt)
                        if not trt.is_transaction_finished():
                            trt.force_finish_transaction()

                    # Update the TransactionsPool with the remaining transactions
                    self.__transactions = [x for x in self.__transactions
                                           if x.get_request().token != transaction.get_request().token]
