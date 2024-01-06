import argparse
from _socket import IPPROTO_UDP
from multiprocessing.managers import BaseManager
from socket import socket, AF_INET, SOCK_DGRAM

from share_drive_server.server_resource import ServerResource
from source.coap_core.coap_worker.coap_worker_pool import CoapWorkerPool


class CustomManager(BaseManager):
    # nothing
    pass


class Server(CoapWorkerPool):
    def __init__(self, ip_address, port):
        _skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        _skt.bind((ip_address, port))
        super().__init__(_skt, ServerResource("share_drive", "/home/damir/coap/server/resources/"))


def main():
    parser = argparse.ArgumentParser(description='Server script with address and port arguments')

    parser.add_argument('--server_address', type=str, default='127.0.0.1', help='Server address')
    parser.add_argument('--server_port', type=int, default=5683, help='Server port')

    args = parser.parse_args()

    Server(args.server_address, args.server_port).listen()


main()
