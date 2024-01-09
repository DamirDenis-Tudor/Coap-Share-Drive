import os
import datetime
import threading
from enum import Enum
from multiprocessing import current_process

from coap_core.coap_utilities.coap_singleton import CoapSingletonBase


class LogDestination(Enum):
    CONSOLE = 1
    FILE = 2


class LogColor(Enum):
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'


class CoapLogger(CoapSingletonBase):
    """
    A Singleton Thread-Safe Logger class that allows logging to the console or a log file.

    This class can be used to log messages to the console or a log file based on
    the selected LogDestination (CONSOLE or FILE). It implements the Singleton
    pattern to ensure a single instance of the logger for each destination.

    Args:
        destination (LogDestination): The destination for logging (CONSOLE or FILE).
    """

    def __init__(self, destination):
        """
        Initialize the Logger instance with the specified destination.

        Args:
            destination (LogDestination): The destination for logging (CONSOLE or FILE).
        """
        self.destination = destination
        self.log_file = None
        self.log_directory = "logs"
        self.debug_mode = False
        self._lock = threading.Lock()

        if self.destination == LogDestination.FILE:
            self.initialize_logger()

    def initialize_logger(self):
        """
        Initialize the logger for FILE destination.

        This method creates a log directory, removes previous log files,
        and creates a new log file with a timestamp.
        """
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
        else:
            self.remove_previous_logs()
        current_time = datetime.datetime.now().strftime("%H-%M-%S")
        self.log_file = os.path.join(self.log_directory, f"log_{current_time}.log")

    def remove_previous_logs(self):
        """
        Remove previous log files in the log directory.
        """
        for log_file in os.listdir(self.log_directory):
            file_path = os.path.join(self.log_directory, log_file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def log(self, message, color=LogColor.GREEN):
        """
        Log a message to the console or the log file.

        Args:
            message (str): The message to log.
            color (LogColor, optional): The color for console output.

        Note:
            The color argument is only used for console logging.
            :param color:
            :param message:
            :param time:
        """
        if not self.debug_mode:
            log_message = message
            with self._lock:
                if self.destination == LogDestination.CONSOLE:
                    if color is not None:
                        log_message = f"{color.value}{log_message}{LogColor.RESET.value}"
                    print(log_message)

    def debug(self, message, color=LogColor.GREEN, stamp= True):
        if self.debug_mode:
            process_name = current_process().name
            thread_name = threading.current_thread().name
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            if stamp:
                log_message = f"{current_time} {process_name} -> {thread_name}:  {message}"
            else:
                log_message = message
            with self._lock:
                if self.destination == LogDestination.CONSOLE:
                    if color is not None:
                        log_message = f"{color.value} {log_message} {LogColor.RESET.value}"
                    print(log_message)
                elif self.destination == LogDestination.FILE:
                    with open(self.log_file, 'a') as log_file:
                        log_file.write(log_message + "\n")

    def __call__(self, func) -> object:
        """
        Decorator function to log function calls and results.

        This decorator logs information about function calls and their results.

        Args:
            func (callable): The function to be decorated.

        Returns:
            callable: The wrapped function that includes logging.
        """

        def wrapper(*args, **kwargs):
            self.debug(f"Calling function: {func.__name__} \n {args}", LogColor.MAGENTA)
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    self.debug(f"Result of {func.__name__}: {result}", LogColor.BLUE)
                    return result
            except Exception as e:
                self.debug(f"Function {func.__name__} encountered an exception: {e}", LogColor.YELLOW)

        return wrapper


logger = CoapLogger(LogDestination.CONSOLE)
