from copy import copy
from enum import Enum

from source.Packet.CoapConfig import CoapType, CoapCodeFormat, CoapContentFormat, CoapOptionDelta
from source.Packet.CoapPacket import CoapPacket


class CoapTemplates(Enum):
    NON_COAP_FORMAT = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"ABAB",
        code=CoapCodeFormat.EMPTY.value(),
        message_id=0,
        options={},
        payload=""
    )

    def __init__(self, coap_packet: CoapPacket):
        self.coap_packet = coap_packet

    def value(self):
        return copy(self.coap_packet)
