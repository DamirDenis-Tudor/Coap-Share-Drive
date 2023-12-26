import threading

from source.Transaction.CoapTransaction import CoapTransaction


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

    def solve_transactions(self):
        if len(self.__transaction_dict) > 0:
            keys_copy = list(self.__transaction_dict.keys())

            for key in keys_copy:
                if key[0] not in self.__failed_transactions and key not in self.__finished_transactions:
                    match self.__transaction_dict[key].run_transaction():
                        case CoapTransaction.FAILED_TRANSACTION:
                            token = key[0]
                            self.__failed_transactions.append(token)
                            self.__transaction_dict = {
                                (t.request.token, t.request.message_id):
                                    t for t in self.__transaction_dict.values()
                                if not (t.request.token == token)
                            }
                            break
                        case _:
                            pass

            self.__finished_transactions.clear()

    def finish_transaction(self, token: bytes, msg_id: int):
        # todo add ip too
        key = (token, msg_id)
        self.__finished_transactions[key] = msg_id

        # there is no need to delete the transaction if it has already finished.
        if key in self.__transaction_dict:
            del self.__transaction_dict[key]

    def transaction_previously_failed(self, token: bytes):
        if token in self.__failed_transactions:
            self.__failed_transactions.remove(token)
            return True
        return False

    def get_number_of_transactions(self):
        return len(self.__transaction_dict)
