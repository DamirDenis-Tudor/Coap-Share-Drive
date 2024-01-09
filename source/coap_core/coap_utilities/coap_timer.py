import time

from source.coap_core.coap_utilities.coap_logger import logger


class CoapTimer:
    def __init__(self, operation_name: str = None):
        self.__start_time = None
        self.__end_time = None
        self.__operation_name = operation_name

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, *args):
        if self.__operation_name:
            print(f"<{self.__operation_name}> -> Execution time <{self.elapsed_time()}>")
        self.reset()

    def reset(self):
        """Start the timer."""
        self.__start_time = time.time()
        return self

    def stop(self):
        """Stop the timer."""
        self.__end_time = time.time()

    def elapsed_time(self):
        """Get the elapsed time in seconds."""
        if self.__start_time is None:
            raise ValueError("Timer has not been started.")
        return time.time() - self.__start_time
