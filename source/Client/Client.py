from select import select
from socket import *
from time import sleep

from source.PacketManager.Packet import *
from source.PacketManager.PacketUtils.TokenGen import TokenGenerator

s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
s.bind(('127.0.0.5', int(2000)))
i = 0
while True:

    if i < 100:
        encoded_packet = Packet.encode({
            "CoapVer": 1,
            "PacketType": PacketType.CON,
            "TokenLength": TOKEN_LENGTH,
            "PacketCode": PacketCode.RequestCode.GET,
            "PacketId": 57,
            "Token": TokenGenerator.generate_token(),
            "EntityType": EntityType.FILE,
            "PacketDepth": 0,
            "DepthOrder": 0,
            "NextState": NextState.NO_PACKET,
            "PayloadFormat": PayloadFormat.STRING,
            "Payload": "/text.txt"
        })
        logger.log(Packet(encoded_packet).__repr__())
        s.sendto(encoded_packet, ("127.0.0.1", int(6601)))
        sleep(0.01)
        i += 1

    active_socket_read, _, _ = select([s], [], [], 0.01)
    if active_socket_read:
        data, address = s.recvfrom(1032)
        print(Packet(raw_packet=data, skt=s, external_ip=address))