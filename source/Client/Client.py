from socket import *

from source.Packet.CoapConfig import *
from source.Packet.CoapPacket import CoapPacket

coap_message = CoapPacket(
    version=1,
    message_type=CoAPType.CON.value,
    token=b"ABAB",
    code=CoAPCodeFormat.GET.value(),
    message_id=0,
    options={
        CoAPOptionDelta.LOCATION_PATH.value: "/documents/data/forder/test",
        CoAPOptionDelta.CONTENT_FORMAT.value: CoAPContentFormat.APPLICATION_JSON.value,
        CoAPOptionDelta.URI_HOST.value: "shareDrive/marian",
        CoAPOptionDelta.URI_PORT.value: 69,
        CoAPOptionDelta.SIZE1.value: 10
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
