from select import select
from socket import *
from time import sleep

from source.Logger.Logger import logger
from source.Packet.Packet import *
from source.Packet.TokenGen import TokenGenerator

s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
s.bind(('127.0.0.8', int(2000)))

encoded_packet = Packet.encode({
    "CoapVer": 1,
    "PacketType": PacketType.CON,
    "TokenLength": TOKEN_LENGTH,
    "PacketCode": PacketCode.RequestCode.GET,
    "PacketId": 0,
    "Token": TokenGenerator.generate_token(),
    "EntityType": EntityType.FILE,
    "PacketDepth": 0,
    "DepthOrder": 0,
    "NextState": NextState.NO_PACKET,
    "PayloadFormat": PayloadFormat.STRING,
    "Payload": "source/Server/Server.PY"
})
s.sendto(encoded_packet, ("127.0.0.2", int(6601)))

while True:
    active_socket_read, _, _ = select([s], [], [], 0.01)
    if active_socket_read:
        data, address = s.recvfrom(1032)
        print(Packet(raw_packet=data, skt=s, external_ip=address).__repr__())
