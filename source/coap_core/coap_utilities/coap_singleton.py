import threading


class CoapSingleton(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """
    _lock = threading.Lock()
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in CoapSingleton._instances:
            instance = super().__call__(*args, **kwargs)
            with CoapSingleton._lock:
                cls._instances[cls] = instance
        return cls._instances[cls]


class CoapSingletonBase(metaclass=CoapSingleton):
    pass
