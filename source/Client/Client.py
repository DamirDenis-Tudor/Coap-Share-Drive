from socket import *

from source.Packet.CoapConfig import *
from source.Packet.CoapPacket import CoapPacket

# Block1 and Block2 options
block_number = 0  # Starting block number
block_size = 64  # Block size in bytes

# CoAP message with Block1 and Block2 options
# IS NECCESSRY TO HAVE AN OPTION THAT IS BELLOW 12 -> CONTENT FORMAT
coap_message = CoapPacket(
    version=1,
    message_type=CoAPType.CON.value,
    token=b"ABAB",
    code=CoAPCodeFormat.GET.value(),
    message_id=0,
    options={
        CoAPOptionDelta.URI_QUERY.value: "path",
        CoAPOptionDelta.LOCATION_PATH.value: "path",
        CoAPOptionDelta.CONTENT_FORMAT.value: CoAPContentFormat.APPLICATION_JSON.value,
        CoAPOptionDelta.BLOCK1.value: 12
    },
    payload="""{"name":"marius"}""".encode("utf-8")
)

encoded_coap_message = coap_message.encode()

skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
skt.bind(('127.0.0.3', int(5683)))

skt.sendto(encoded_coap_message, ('127.0.0.3', int(5683)))

data, _ = skt.recvfrom(2000)
pkt = CoapPacket.decode(data)

print(pkt.options)
