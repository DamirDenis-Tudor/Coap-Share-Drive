import multiprocessing

from source.Core.AbstractWorker import WorkerType
from source.Core.CoapWorkerPool import CoapWorkerPool
from source.Core.ServerWorker import ServerWorker
from source.Resource.Resource import Resource
from source.Resource.StorageResource import StorageResource


class CoapServer(CoapWorkerPool):
    def __init__(self, ip_address, port):
        super().__init__(ServerWorker, ip_address, port)
        self.__resources: list[Resource] = []

    def search_resources(self):
        pass

    def get_resource(self, path: str):
        for resource in self.__resources:
            if resource.get_name() == path:
                return resource
        return None

    def add_resource(self, resource: Resource):
        self.__resources.append(resource)

    def remove_resource(self, resource: Resource):
        self.__resources.remove(resource)


if __name__ == '__main__':
    server = CoapServer('127.0.0.2', int(5683))
    server.add_resource(StorageResource("share_drive"))
    server.listen()
