import time


class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start the timer."""
        self.start_time = time.time()

    def stop(self):
        """Stop the timer."""
        self.end_time = time.time()

    def elapsed_time(self):
        """Get the elapsed time in seconds."""
        if self.start_time is None:
            raise ValueError("Timer has not been started.")
        elif self.end_time is None:
            raise ValueError("Timer has not been stopped.")
        return self.end_time - self.start_time

    def reset(self):
        """Reset the timer."""
        self.start_time = None
        self.end_time = None
