import time


class Timer:
    def __init__(self):
        self.__start_time = None
        self.__end_time = None

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
