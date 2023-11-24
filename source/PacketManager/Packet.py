from socket import socket

from bitfields import Bits

from source.Logger.Logger import logger
from source.PacketManager.PacketUtils.Config import *


class Packet:

    def __init__(self, raw_packet: bytes, skt: socket = None, external_ip: tuple = None):
        self.__is_empty = False
        if not raw_packet:
            self.__is_empty = True
            return

        bits_packet = Bits(int.from_bytes(raw_packet, byteorder='big'))

        self.socket = skt
        self.extern_ip = external_ip
        self.coap_ver = format(int(bits_packet[0]), '01b')
        self.packet_type = PacketType.get_field_name(format(int(bits_packet[1:3]), '02b'))
        self.token_length = int(bits_packet[3:7])
        self.packet_code = PacketCode.get_field_name(format(int(bits_packet[7:15]), '08b'))
        self.packet_id = int(bits_packet[15:31])

        index = self.token_length + 31
        self.token = format(int(bits_packet[31:index]), f'0{self.token_length}b')
        self.entity_type = EntityType.get_field_name(format(int(bits_packet[index:index + 2]), '02b'))

        index += 2
        self.packet_depth = int(bits_packet[index:index + 4])

        index += 4
        self.packet_depth_order = int(bits_packet[index:index + 6])

        index += 6
        self.next_state = NextState.get_field_name(format(int(bits_packet[index:index + 1]), '01b'))

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
        if self.__is_empty:
            return f"Empty packet"
        return str(self.to_dict())

    def __repr__(self):
        if self.__is_empty:
            return f"Empty packet:"
        return f"Packet(sender: {self.extern_ip}, tkn: {self.token} ,pkt_id {self.packet_id}), payload {self.payload}"

    @classmethod
    def empty_packet(cls):
        return cls(bytes())

    def is_empty(self):
        return self.__is_empty

    def to_dict(self):
        if self.is_empty():
            return {"EmptyPacket": True}

        return {
            "ExternIP": self.extern_ip,
            "CoapVer": self.coap_ver,
            "PacketType": self.packet_type,
            "TokenLength": format(self.token_length, '04b'),
            "PacketCode": self.packet_code,
            "PacketId": self.packet_id,
            "Token": self.token,
            "EntityType": self.entity_type,
            "PacketDepth": self.packet_depth,
            "PacketDepthOrder": self.packet_depth_order,
            "NextState": self.next_state,
            "PayloadFormat": self.payload_format,
            "Payload": self.payload
        }

    @staticmethod
    def encode(content: dict):
        coap_ver = str(content.get("CoapVer"))
        packet_type = content.get("PacketType").value
        token_length = content.get("TokenLength")
        packet_code = content.get("PacketCode").value
        packet_id = format(content.get("PacketId"), '016b')
        token = content.get("Token")
        entity_type = content.get("EntityType").value
        packet_depth = format(content.get("PacketDepth"), '04b')
        packet_depth_order = format(content.get("PacketDepth"), '06b')
        next_state = content.get("NextState").value
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

        bits_sequence = coap_ver + packet_type + token_length + packet_code + packet_id + token + \
                        entity_type + packet_depth + packet_depth_order + next_state + payload_format + payload

        matched_bytes = int(bits_sequence, 2).to_bytes((len(bits_sequence) + 7) // 8, byteorder='big')

        return matched_bytes
