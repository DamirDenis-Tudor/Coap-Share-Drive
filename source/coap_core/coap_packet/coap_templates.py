from copy import deepcopy
from enum import Enum

from source.coap_core.coap_packet.coap_config import CoapType, CoapCodeFormat, CoapContentFormat, CoapOptionDelta
from source.coap_core.coap_packet.coap_packet import CoapPacket


class CoapTemplates(Enum):

    DOWNLOAD = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.GET.value(),
        message_id=0,
        options={
            CoapOptionDelta.BLOCK1.value: 6,  # block size
            CoapOptionDelta.URI_PATH.value: "<UNDEFINED>",
            CoapOptionDelta.LOCATION_PATH.value: "<UNDEFINED>"
        },
        payload=""
    )

    UPLOAD = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.PUT.value(),
        message_id=0,
        options={
            CoapOptionDelta.BLOCK1.value: 6,  # block size
            CoapOptionDelta.URI_PATH.value: "<UNDEFINED>",
            CoapOptionDelta.LOCATION_PATH.value: "<UNDEFINED>"
        },
        payload=""
    )

    MV = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.POST.value(),
        message_id=0,
        options={
            CoapOptionDelta.URI_PATH.value: "<UNDEFINED>",
            CoapOptionDelta.LOCATION_PATH.value: "<UNDEFINED>",
            CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.TEXT_PLAIN_UTF8.value,
        },
        payload="<UNDEFINED>"
    )

    DELETE = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.DELETE.value(),
        message_id=0,
        options={
            CoapOptionDelta.URI_PATH.value: "<UNDEFINED>",
            CoapOptionDelta.LOCATION_PATH.value: "<UNDEFINED>"
        },
        payload=""
    )

    SYNC = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.FETCH.value(),
        message_id=0,
        options={
            CoapOptionDelta.URI_PATH.value: "<UNDEFINED>",
        },
        payload=""
    )

    NON_COAP_FORMAT = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.EMPTY.value(),
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

    FAILED_REQUEST = CoapPacket(
        version=1,
        message_type=CoapType.RST.value,
        token=b"",
        code=CoapCodeFormat.CLIENT_ENTITY_INCOMPLETE.value(),
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

    DUMMY_PACKET = CoapPacket(
        version=0,
        message_type=0,
        token=b"",
        code=0,
        message_id=0,
        options={},
        payload=""
    )

    SUCCESS_VALID_ACK = CoapPacket(
        version=1,
        message_type=CoapType.ACK.value,
        token=b"",
        code=CoapCodeFormat.SUCCESS_VALID.value(),
        message_id=0,
        options={
            CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.TEXT_PLAIN_UTF8.value,
        },
        payload=""
    )

    BYTES_RESPONSE = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.SUCCESS_CONTENT.value(),
        message_id=0,
        options={
            CoapOptionDelta.LOCATION_PATH.value: "",
            CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.APPLICATION_OCTET_STREAM.value,
            CoapOptionDelta.BLOCK2.value: 6,  # block size
        },
        payload=""
    )

    def __init__(self, coap_packet: CoapPacket):
        self.coap_packet = coap_packet

    def value_with(self, tkn, msg_id) -> CoapPacket:
        request = deepcopy(self.coap_packet)
        request.token = tkn
        request.message_id = msg_id % 65536
        return request

    def value(self) -> CoapPacket:
        return deepcopy(self.coap_packet)
