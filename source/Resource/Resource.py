from abc import ABC, abstractmethod


class Resource(ABC):

    def __init__(self, path: str):
        self.__root_path = '/'
        self.__path = path

    def set_root_path(self, path: str):
        self.__root_path = path

    @abstractmethod
    def get(self, request):
        pass

    @abstractmethod
    def put(self, request):
        pass

    @abstractmethod
    def post(self, request):
        pass

    @abstractmethod
    def delete(self, request):
        pass
