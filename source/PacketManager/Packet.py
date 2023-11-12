from bitfields import Bits
from source.PacketManager.PacketUtils.Config import *
from source.PacketManager.PacketUtils.TokenGen import TokenGenerator


class Packet:
    def __init__(self, raw_packet: int, external_ip: str):
        bits_packet = Bits(raw_packet)
        self.extern_ip = external_ip
        self.coap_ver = format(int(bits_packet[0]), '01b')
        self.packet_type = PacketType.get_field_name(format(int(bits_packet[1:3]), '02b'))
        self.token_length = int(bits_packet[3:7])
        self.packet_code = PacketCode.get_field_name(format(int(bits_packet[7:15]), '08b'))
        self.packet_id = int(bits_packet[15:31])

        index = self.token_length + 31
        self.token = int(bits_packet[31:index])
        self.packet_depth = int(bits_packet[index:index + 4])

        index += 4
        self.multiple_packets = MultiplePackets.get_field_name(format(int(bits_packet[index:index + 1]), '01b'))

        index += 1
        self.payload_format = PayloadFormat.get_field_name(format(int(bits_packet[index:index + 2]), '02b'))

        index += 2
        self.payload = None
        if self.payload_format == PayloadFormat.OPAQUE:
            self.payload = bits_packet[index:]
        elif self.payload_format == PayloadFormat.UINT:
            self.payload = int(bits_packet[index:])
        elif self.payload_format == PayloadFormat.STRING:
            self.payload = bits_packet[index:].to_bytes().decode('utf-8')

    def __str__(self):
        return (
            f"Packet Details \n"
            f"  From: {self.extern_ip}\n"
            f"  Coap Version: {self.coap_ver}\n"
            f"  Packet Type: {self.packet_type}\n"
            f"  Token Length: {self.token_length}\n"
            f"  Packet Code: {self.packet_code}\n"
            f"  Packet ID: {self.packet_id}\n"
            f"  Token: {self.token}\n"
            f"  Packet Depth: {self.packet_depth}\n"
            f"  Multiple Packets: {self.multiple_packets}\n"
            f"  Payload Format: {self.payload_format}\n"
            f"  Payload: {self.payload}\n"
        )

    def __repr__(self):
        return str(self)

    @staticmethod
    def encode(content: dict):
        coap_ver = str(content.get("CoapVer"))
        packet_type = content.get("PacketType").value
        token_length = content.get("TokenLength")
        packet_code = content.get("PacketCode").value
        packet_id = format(content.get("PacketId"), '016b')
        token = content.get("Token")
        packet_depth = format(content.get("PacketDepth"), '04b')
        multiple_packets = content.get("MultiplePackets").value
        payload_format = content.get("PayloadFormat").value

        payload = ''
        try:
            if content.get("PayloadFormat") == PayloadFormat.STRING:
                payload = ''.join(format(ord(b), '08b') for b in str(content.get("Payload")))
            elif content.get("PayloadFormat") == PayloadFormat.UINT:
                payload = bin(content.get("Payload"))[2:]
            elif content.get("PayloadFormat") == PayloadFormat.OPAQUE:
                payload = bin(content.get("Payload"))[2:]
        except (AttributeError, TypeError, UnicodeEncodeError) as invalid_payload:
            print(f"Invalid payload: {invalid_payload}")
            # Handle the exception or add additional logging here

        bits_sequence = coap_ver + packet_type + token_length + packet_code + packet_id + token \
                        + packet_depth + multiple_packets + payload_format + payload

        matched_bytes = int(bits_sequence, 2).to_bytes((len(bits_sequence) + 7) // 8, byteorder='big')

        return int.from_bytes(matched_bytes, byteorder='big')


for x in range(1, 30):
    # Test the encode method
    encoded_packet = Packet.encode({
        "CoapVer": 1,
        "PacketType": PacketType.CON,
        "TokenLength": TokenGenerator.TOKEN_LENGTH,
        "PacketCode": PacketCode.RequestCode.GET,
        "PacketId": 0,
        "Token": TokenGenerator.generate_token(),
        "PacketDepth": 0,
        "MultiplePackets": MultiplePackets.MULTIPLE,
        "PayloadFormat": PayloadFormat.STRING,
        "Payload": "/text.txt"
    })

    packet = Packet(encoded_packet, "192.125.111.15")
    print(packet)

    encoded_packet1 = Packet.encode({
        "CoapVer": 1,
        "PacketType": PacketType.RST,
        "TokenLength": TokenGenerator.TOKEN_LENGTH,
        "PacketCode": PacketCode.RequestCode.EMPTY,
        "PacketId": 0,
        "Token": TokenGenerator.generate_token(),
        "PacketDepth": 0,
        "MultiplePackets": MultiplePackets.SINGLE,
        "PayloadFormat": PayloadFormat.EMPTY,
        "Payload": ""
    })
    packet1 = Packet(encoded_packet1, "192.125.0.15")
    print(packet1)
