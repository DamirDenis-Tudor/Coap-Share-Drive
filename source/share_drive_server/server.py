import argparse

from share_drive_server.server_resource import ServerResource
from source.coap_core.coap_worker.coap_worker_pool import CoapWorkerPool
from source.coap_core.coap_resource.resource_manager import ResourceManager


class Server(CoapWorkerPool):
    def __init__(self, ip_address, port):
        super().__init__(ip_address, port)

        ResourceManager().set_root_path("/home/damir/coap/server/resources/")
        ResourceManager().discover_resources()
        ResourceManager().add_default_resource(ServerResource("share_drive"))


def main():
    parser = argparse.ArgumentParser(description='Server script with address and port arguments')

    parser.add_argument('--server_address', type=str, default='192.168.1.102', help='Server address')
    parser.add_argument('--server_port', type=int, default=5683, help='Server port')

    args = parser.parse_args()

    Server(args.server_address, args.server_port).listen()

main()