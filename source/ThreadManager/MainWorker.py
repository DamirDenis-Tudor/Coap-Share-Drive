import select
from socket import *

from source.PacketManager.Packet import Packet

s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
s.bind(('127.0.0.1', int(2003)))

while True:
    r, _, _ = select.select([s], [], [], 1)
    if r:
        data, address = s.recvfrom(1)
        print(Packet(data, address))