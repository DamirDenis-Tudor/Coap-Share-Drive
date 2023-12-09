from source.Core.AbstractWorker import WorkerType
from source.Core.CoapWorkerPool import CoapWorkerPool


class Server(CoapWorkerPool):
    def __init__(self, ip_address, port):
        super().__init__(WorkerType.SERVER_WORKER, ip_address, port)

    def search_resources(self):
        pass

    def add_resource(self):
        pass

    def remove_resource(self):
        pass


if __name__ == '__main__':
    server = Server('127.0.0.2', int(5683))
    server.listen()
