from socket import socket
from bitfields import Bits
from source.Packet.Old_Packet.Config import *


class Packet:
    def __init__(self, raw_packet: bytes, skt: socket = None, external_ip: tuple = None):
        self.__is_empty = False
        if not raw_packet:
            self.__is_empty = True
            return

        bits_packet = Bits(int.from_bytes(raw_packet, byteorder='big'))

        self.__socket = skt
        self.__external_ip = external_ip
        self.__coap_ver = format(int(bits_packet[0]), '01b')
        self.__packet_type = PacketType.get_field_name(format(int(bits_packet[1:3]), '02b'))
        self.__token_length = int(bits_packet[3:7])
        self.__packet_code = PacketCode.get_field_name(format(int(bits_packet[7:15]), '08b'))
        self.__packet_id = int(bits_packet[15:47])

        index = self.__token_length + 47
        self.__token = format(int(bits_packet[47:index]), f'0{self.__token_length}b')
        self.__entity_type = EntityType.get_field_name(format(int(bits_packet[index:index + 2]), '02b'))

        index += 2
        self.__packet_depth = int(bits_packet[index:index + 4])

        index += 4
        self.__packet_depth_order = int(bits_packet[index:index + 6])

        index += 6
        self.__next_state = NextState.get_field_name(format(int(bits_packet[index:index + 1]), '01b'))

        index += 1
        self.__payload_format = PayloadFormat.get_field_name(format(int(bits_packet[index:index + 2]), '02b'))

        index += 2

        self.__payload_opaque: bytes
        self.__payload_uint: int
        self.__payload_string: str
        if self.__payload_format == PayloadFormat.OPAQUE:
            self.__payload_opaque = bits_packet[index:].to_bytes().decode('utf-8')
        elif self.__payload_format == PayloadFormat.UINT:
            self.__payload_uint = int(bits_packet[index:])
        elif self.__payload_format == PayloadFormat.STRING:
            self.__payload_string = bits_packet[index:].to_bytes().decode('utf-8')

    def __str__(self):
        if self.__is_empty:
            return f"Empty packet"
        return str(self.to_dict())

    def __repr__(self):
        if self.__is_empty:
            return f"Empty packet:"

        return (
            f"Packet("
            f"type: {self.__packet_type}, "
            f"tkn: {self.__token}, "
            f"code: {self.__packet_code}, "
            f"entity: {self.__entity_type}, "
            f"packet_id: {self.__packet_id}, "
            f"payload_format: {self.__payload_format}, "
            f"payload: {self.get_payload()}"
        )

    @staticmethod
    def encode(content: dict):
        coap_ver = str(content.get("CoapVer"))
        packet_type = content.get("PacketType").value
        token_length = content.get("TokenLength")
        packet_code = content.get("PacketCode").value
        packet_id = format(content.get("PacketId"), '032b')
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
                payload = int(payload, 2).to_bytes((len(payload) + 7) // 8, byteorder='big')
            elif content.get("PayloadFormat") == PayloadFormat.UINT:
                payload = bin(content.get("Payload"))[2:-1]
                payload = int(payload, 2).to_bytes((len(payload) + 7) // 8, byteorder='big')
            elif content.get("PayloadFormat") == PayloadFormat.OPAQUE:
                payload = content.get("Payload")
        except (AttributeError, TypeError, UnicodeEncodeError) as invalid_payload:
            print(f"Invalid payload: {invalid_payload}")

        bits_sequence = (coap_ver + packet_type + token_length + packet_code + packet_id + token +
                         entity_type + packet_depth + packet_depth_order + next_state + payload_format)

        matched_bytes = int(bits_sequence, 2).to_bytes((len(bits_sequence) + 7) // 8, byteorder='big') + payload

        return matched_bytes

    @classmethod
    def empty_packet(cls):
        return cls(bytes())

    def is_empty(self):
        return self.__is_empty

    # Getter and setter for socket
    def get_socket(self):
        return self.__socket

    def set_socket(self, skt):
        self.__socket = skt

    # Getter and setter for external_ip
    def get_external_ip(self):
        return self.__external_ip

    def set_external_ip(self, external_ip):
        self.__external_ip = external_ip

    # Getter and setter for coap_ver
    def get_coap_ver(self):
        return self.__coap_ver

    def set_coap_ver(self, coap_ver):
        self.__coap_ver = coap_ver

    # Getter and setter for packet_type
    def get_packet_type(self):
        return self.__packet_type

    def set_packet_type(self, packet_type):
        self.__packet_type = packet_type

    # Getter and setter for token_length
    def get_token_length(self):
        return self.__token_length

    def set_token_length(self, token_length):
        self.__token_length = token_length

    # Getter and setter for packet_code
    def get_packet_code(self):
        return self.__packet_code

    def set_packet_code(self, packet_code):
        self.__packet_code = packet_code

    # Getter and setter for packet_id
    def get_packet_id(self):
        return self.__packet_id

    def set_packet_id(self, packet_id):
        self.__packet_id = packet_id

    # Getter and setter for token
    def get_token(self):
        return self.__token

    def set_token(self, token):
        self.__token = token

    # Getter and setter for entity_type
    def get_entity_type(self):
        return self.__entity_type

    def set_entity_type(self, entity_type):
        self.__entity_type = entity_type

    # Getter and setter for packet_depth
    def get_packet_depth(self):
        return self.__packet_depth

    def set_packet_depth(self, packet_depth):
        self.__packet_depth = packet_depth

    # Getter and setter for packet_depth_order
    def get_packet_depth_order(self):
        return self.__packet_depth_order

    def set_packet_depth_order(self, packet_depth_order):
        self.__packet_depth_order = packet_depth_order

    # Getter and setter for next_state
    def get_next_state(self):
        return self.__next_state

    def set_next_state(self, next_state):
        self.__next_state = next_state

    # Getter and setter for payload_format
    def get_payload_format(self):
        return self.__payload_format

    def set_payload_format(self, payload_format):
        self.__payload_format = payload_format

    # Getter and setter for payload
    def get_payload(self):
        if self.__payload_format == PayloadFormat.OPAQUE:
            return self.__payload_opaque
        elif self.__payload_format == PayloadFormat.UINT:
            return self.__payload_uint
        elif self.__payload_format == PayloadFormat.STRING:
            return self.__payload_string
        return None

    def set_payload(self, payload):
        if self.__payload_format == PayloadFormat.OPAQUE:
            self.__payload_opaque = payload
        elif self.__payload_format == PayloadFormat.UINT:
            self.__payload_uint = payload
        elif self.__payload_format == PayloadFormat.STRING:
            self.__payload_string = payload

    def to_dict(self):
        if self.is_empty():
            return {"EmptyPacket": True}

        return {
            "ExternIP": self.__external_ip,
            "CoapVer": self.__coap_ver,
            "PacketType": self.__packet_type,
            "TokenLength": format(self.__token_length, '04b'),
            "PacketCode": self.__packet_code,
            "PacketId": self.__packet_id,
            "Token": self.__token,
            "EntityType": self.__entity_type,
            "PacketDepth": self.__packet_depth,
            "PacketDepthOrder": self.__packet_depth_order,
            "NextState": self.__next_state,
            "PayloadFormat": self.__payload_format,
            "Payload": self.get_payload()
        }
