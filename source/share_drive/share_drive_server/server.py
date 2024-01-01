from source.coap_core.coap_worker.coap_worker_pool import CoapWorkerPool
from source.coap_core.coap_resource.resource_manager import ResourceManager
from source.share_drive.share_drive_server.server_resource import ServerResource


class Server(CoapWorkerPool):
    def __init__(self, ip_address, port):
        super().__init__(ip_address, port)

        ResourceManager().set_root_path("/home/damir/coap/server/resources/")
        ResourceManager().discover_resources()
        ResourceManager().add_default_resource(ServerResource("share_drive"))


if __name__ == '__main__':
    server = Server(
        '127.0.0.2',
        int(5683)
    )
    server.listen()
