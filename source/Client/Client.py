from socket import *

from source.PacketManager.Packet import *
from source.PacketManager.PacketUtils.TokenGen import TokenGenerator

encoded_packet = Packet.encode({
    "CoapVer": 1,
    "PacketType": PacketType.CON,
    "TokenLength": TokenGenerator.TOKEN_LENGTH,
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

s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
s.bind(('127.0.0.5', int(2002)))
s.sendto(encoded_packet, ("127.0.0.1", int(8730)))
