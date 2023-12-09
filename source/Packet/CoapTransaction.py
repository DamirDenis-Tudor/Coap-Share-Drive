from socket import socket

from source.Packet import CoapPacket
from source.Utilities.Timer import Timer


class CoapTransaction:
    def __init__(self, request):
        self._request: CoapPacket = request

        self.__timer = Timer()
        self.__timer.reset()

        self.__ack_timeout = 5
        self.__ack_received = False

    def get_request(self):
        return self._request

    def run_timer(self):
        skt: socket = self._request.skt
        dest = self._request.sender_ip_port

        while not self.__ack_received:
            if self.__timer.elapsed_time() > self.__ack_timeout:
                skt.sendto(self._request.encode(), dest)
                self.__ack_timeout *= 2
                self.__timer.reset()
