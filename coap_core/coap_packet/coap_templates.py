from copy import deepcopy
from enum import Enum

from coap_core.coap_packet.coap_config import CoapType, CoapCodeFormat
from coap_core.coap_packet.coap_packet import CoapPacket


class CoapTemplates(Enum):
    NOT_IMPLEMENTED = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.SERVER_ERROR_NOT_IMPLEMENTED.value(),
        message_id=0,
        options={},
        payload=""
    )

    BAD_REQUEST = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.CLIENT_ERROR_BAD_REQUEST.value(),
        message_id=0,
        options={},
        payload=""
    )

    CONFLICT = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.CLIENT_ERROR_CONFLICT.value(),
        message_id=0,
        options={},
        payload=""
    )

    NOT_FOUND = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.CLIENT_ERROR_NOT_FOUND.value(),
        message_id=0,
        options={},
        payload=""
    )

    FAILED_REQUEST = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.CLIENT_ENTITY_INCOMPLETE.value(),
        message_id=0,
        options={},
        payload=""
    )

    INTERNAL_ERROR = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.SERVER_ERROR_INTERNAL_SERVER_ERROR.value(),
        message_id=0,
        options={},
        payload=""
    )

    EMPTY_ACK = CoapPacket(
        version=1,
        message_type=CoapType.ACK.value,
        token=b"",
        code=CoapCodeFormat.EMPTY.value(),
        message_id=0,
        options={},
        payload=""
    )

    SUCCESS_CONTINUE_ACK = CoapPacket(
        version=1,
        message_type=CoapType.ACK.value,
        token=b"",
        code=CoapCodeFormat.SUCCESS_CONTINUE.value(),
        message_id=0,
        options={},
        payload="",
    )

    SUCCESS_DELETED = CoapPacket(
        version=1,
        message_type=CoapType.ACK.value,
        token=b"",
        code=CoapCodeFormat.SUCCESS_DELETED.value(),
        message_id=0,
        options={},
        payload="",
    )

    SUCCESS_CHANGED = CoapPacket(
        version=1,
        message_type=CoapType.ACK.value,
        token=b"",
        code=CoapCodeFormat.SUCCESS_CHANGED.value(),
        message_id=0,
        options={},
        payload="",
    )

    def __init__(self, coap_packet: CoapPacket):
        self.coap_packet = coap_packet

    def value_with(self, tkn, msg_id, skt=None, ip_port=None) -> CoapPacket:
        request = self.coap_packet.__copy__()
        request.token = tkn
        request.message_id = msg_id % 65536
        request.skt = skt
        request.sender_ip_port = ip_port
        return request

    def value(self) -> CoapPacket:
        return self.coap_packet.__copy__()
