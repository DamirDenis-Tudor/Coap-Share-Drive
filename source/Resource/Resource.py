from abc import ABC, abstractmethod

from source.Packet.CoapPacket import CoapPacket


class Resource(ABC):

    def __init__(self, name: str):
        self.__root_path = '/home/damir/coap/resources/'
        self.__name = name
        self.__path = self.__root_path + name

    def set_root_path(self, path: str):
        self.__root_path = path

    def get_path(self):
        return self.__path

    def get_name(self):
        return self.__name

    @abstractmethod
    def get(self, request: CoapPacket):
        pass

    @abstractmethod
    def put(self, request: CoapPacket):
        pass

    @abstractmethod
    def post(self, request: CoapPacket):
        pass

    @abstractmethod
    def delete(self, request: CoapPacket):
        pass
