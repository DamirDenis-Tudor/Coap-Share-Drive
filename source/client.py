from socket import *

from source.PacketManager.Packet import *

encoded_packet = Packet.encode({
    "CoapVer": 1,
    "PacketType": PacketType.CON,
    "TokenLength": TokenGenerator.TOKEN_LENGTH,
    "PacketCode": PacketCode.RequestCode.GET,
    "PacketId": 0,
    "Token": TokenGenerator.generate_token(),
    "EntityType": EntityType.FILE,
    "PacketDepth": 0,
    "DepthOrder": 0,
    "NextState": NextState.NO_PACKET,
    "PayloadFormat": PayloadFormat.STRING,
    "Payload": "/text.txt"
})

s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
s.bind(('0.0.0.0', int(2002)))
s.sendto(encoded_packet, ("127.0.0.1", 2003))
