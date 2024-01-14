from copy import deepcopy
from enum import Enum

from coap_core.coap_packet.coap_config import CoapType, CoapOptionDelta, CoapCodeFormat, CoapContentFormat
from coap_core.coap_packet.coap_packet import CoapPacket


class DriveTemplates(Enum):
    """
    DriveTemplates is an Enum class that defines various CoAP packet templates for different operations.
    Each template is represented as a CoapPacket with specific parameters.

    Author: Damir Denis-Tudor
    """

    DOWNLOAD = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.GET.value(),
        message_id=0,
        options={
            CoapOptionDelta.BLOCK2.value: 6,  # block size
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
            CoapOptionDelta.LOCATION_PATH.value: "<UNDEFINED>",
            CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.APPLICATION_JSON.value,
        },
        payload="",
        internal_computation=True
    )

    CHANGE = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.POST.value(),
        message_id=0,
        options={
            CoapOptionDelta.URI_PATH.value: "<UNDEFINED>",
            CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.APPLICATION_JSON.value,
        },
        payload=""
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

    FETCH = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.FETCH.value(),
        message_id=0,
        options={
            CoapOptionDelta.BLOCK2.value: 6,  # block size
            CoapOptionDelta.URI_PATH.value: "<UNDEFINED>",
        },
        payload=""
    )

    CONTENT_RESPONSE = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.SUCCESS_CONTENT.value(),
        message_id=0,
        options={
            CoapOptionDelta.LOCATION_PATH.value: "",
            CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.APPLICATION_OCTET_STREAM.value,
        },
        payload="",
    )

    PATH_RESPONSE = CoapPacket(
        version=1,
        message_type=CoapType.CON.value,
        token=b"",
        code=CoapCodeFormat.SUCCESS_CONTENT.value(),
        message_id=0,
        options={
            CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.APPLICATION_JSON.value,
            CoapOptionDelta.BLOCK2.value: 6,
        },
        payload=""
    )

    def __init__(self, coap_packet: CoapPacket):
        """
        Constructor for DriveTemplates Enum.

        Parameters:
        - coap_packet (CoapPacket): The CoAP packet template for the Enum value.
        """
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
