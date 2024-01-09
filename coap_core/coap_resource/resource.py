import os
from abc import ABC, abstractmethod

from coap_core.coap_packet.coap_packet import CoapPacket


class Resource(ABC):
    """
    This abstract class is designed to achieve loose coupling between the CoAP core component and the
    concrete implementation for specific use cases.
    In simpler terms, it serves as a placeholder for the potentially tightly coupled logic associated with the use case.
    """

    def __init__(self, name: str, root_path: str):
        """
        Constructor to initialize a Resource object with a name and root path.
        It creates a directory based on the concatenation of the root path and the name.

        :param name: Name of the resource.
        :param root_path: Root path where the resource directory will be created.
        """
        self.__name = name
        self.__path = os.path.join(root_path, name)

        try:
            os.makedirs(self.__path)
        except FileExistsError:
            # If the directory already exists, ignore the error.
            pass

    def get_name(self) -> str:
        """
        Get the name of the resource.

        :return: Name of the resource.
        """
        return self.__name

    def get_path(self) -> str:
        """
        Get the full path of the resource directory.

        :return: Full path of the resource directory.
        """
        return self.__path

    @abstractmethod
    def handle_get(self, request: CoapPacket):
        """
        Abstract method to handle CoAP GET requests.

        :param request: CoAP GET a request packet.
        """
        pass

    @abstractmethod
    def handle_put(self, request: CoapPacket):
        """
        Abstract method to handle CoAP PUT requests.

        :param request: CoAP PUT a request packet.
        """
        pass

    @abstractmethod
    def handle_post(self, request: CoapPacket):
        """
        Abstract method to handle CoAP POST requests.

        :param request: CoAP POST request packet.
        """
        pass

    @abstractmethod
    def handle_delete(self, request: CoapPacket):
        """
        Abstract method to handle CoAP DELETE requests.

        :param request: CoAP DELETE request packet.
        """
        pass

    @abstractmethod
    def handle_fetch(self, request: CoapPacket):
        """
        Abstract method to handle CoAP FETCH requests.

        :param request: CoAP FETCH request packet.
        """
        pass

    @abstractmethod
    def handle_internal(self, request: CoapPacket):
        """
        Abstract method to handle internal CoAP requests.

        :param request: Internal CoAP request packet.
        """
        pass

    @abstractmethod
    def handle_response(self, request: CoapPacket):
        """
        Abstract method to handle CoAP responses.

        :param request: CoAP's response packet.
        """
        pass
