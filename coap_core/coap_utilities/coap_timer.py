import time


class CoapTimer:
    def __init__(self, operation_name: str = None):
        """
        Initialize CoapTimer.

        Args:
            operation_name (str, optional): Name of the operation being timed.
        """
        self.__start_time = None
        self.__end_time = None
        self.__operation_name = operation_name

    def __enter__(self):
        """
        Enter method for context management. Resets the timer when entering a 'with' block.

        Returns:
            CoapTimer: The CoapTimer instance.
        """
        self.reset()
        return self

    def __exit__(self, *args):
        """
        Exit method for context management. Prints the elapsed time when exiting a 'with' block.

        Args:
            *args: Variable arguments (not used).
        """
        if self.__operation_name:
            print(f"<{self.__operation_name}> -> Execution time <{self.elapsed_time()}>")
        self.reset()

    def reset(self):
        """
        Start the timer.

        Returns:
            CoapTimer: The CoapTimer instance.
        """
        self.__start_time = time.time()
        return self

    def stop(self):
        """Stop the timer."""
        self.__end_time = time.time()

    def elapsed_time(self):
        """
        Get the elapsed time in seconds.

        Returns:
            float: Elapsed time in seconds.

        Raises:
            ValueError: If the timer has not been started.
        """
        if self.__start_time is None:
            raise ValueError("Timer has not been started.")
        return time.time() - self.__start_time

