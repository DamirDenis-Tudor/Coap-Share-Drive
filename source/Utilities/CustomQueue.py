from threading import Event, Thread
from time import sleep


class CustomQueue:
    """
        Class specially tailored for CoapWorkerPool
    """

    def __init__(self):
        self.__list = []
        self.__event = Event()

    def put(self, data):
        self.__event.set()
        self.__list.append(data)

    def get(self):
        self.__event.wait()
        data = self.__list.pop(0)
        if len(self.__list) == 0:
            self.__event.clear()
        return data

    def size(self):
        return len(self.__list)
