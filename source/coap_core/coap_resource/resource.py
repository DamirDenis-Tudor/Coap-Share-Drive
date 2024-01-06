import os
from abc import ABC, abstractmethod

from source.coap_core.coap_packet.coap_packet import CoapPacket


class Resource(ABC):

    def __init__(self, name: str):
        self.__name = name
        self.__path = name

    def set_root_path(self, path: str):
        if path:
            self.__path = path + self.__path
            try:
                os.makedirs(self.__path)
            except FileExistsError:
                pass

    def get_name(self):
        return self.__name

    def get_path(self):
        return self.__path

    @abstractmethod
    def handle_get(self, request: CoapPacket):
        pass

    @abstractmethod
    def handle_put(self, request: CoapPacket):
        pass

    @abstractmethod
    def handle_post(self, request: CoapPacket):
        pass

    @abstractmethod
    def handle_delete(self, request: CoapPacket):
        pass

    @abstractmethod
    def handle_fetch(self, request: CoapPacket):
        pass

    @abstractmethod
    def internal_handling(self, request: CoapPacket):
        pass

    @abstractmethod
    def non_method(self, request: CoapPacket):
        pass
