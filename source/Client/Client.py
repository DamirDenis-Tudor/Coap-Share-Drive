from socket import *

from source.Packet.CoapConfig import *
from source.Packet.CoapPacket import CoapPacket

jsonFormat = """{
      "name": "COAP",
    }"""

coap_message = CoapPacket(
    version=1,
    message_type=CoAPType.CON.value,
    token=b"ABAB",
    code=CoAPCodeFormat.POST.value(),
    message_id=0,
    options=[
        (CoAPOptionDelta.CONTENT_FORMAT.value, CoAPContentFormat.APPLICATION_JSON.value),
        (CoAPOptionDelta.LOCATION_PATH.value, "file.txt")
    ],
    payload=jsonFormat.encode('utf-8')
)

print(coap_message)

encoded_coap_message = coap_message.encode()

print(CoapPacket.decode(encoded_coap_message))

skt = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
skt.bind(('127.0.0.3', int(5683)))

skt.sendto(encoded_coap_message, ('127.0.0.2', int(5683)))
