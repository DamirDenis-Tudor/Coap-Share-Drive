import json
from socket import socket

from source.Packet.CoapConfig import CoAPOptionDelta, CoAPContentFormat


class CoapPacket:
    """
    Represents a CoAP (Constrained Application Protocol) packet.

    This class provides methods for encoding and decoding CoAP
    packets, allowing for interoperability between CoAP-enabled devices.

    """

    def __init__(self, version=1, message_type=0, token=b"", code=0,
                 message_id=0, options=None, payload=None, sender_ip_port: tuple = (), skt: socket = None):
        """
        Initializes a CoAPPacket instance with the provided parameters.

        Args:
            version (int): CoAP version (default is 1).
            message_type (int): Message type (0 for CON, 1 for NON, 2 for ACK, 3 for RST).
            token (bytes): Token for the CoAP packet.
            code (int): CoAP Code indicating the method or response code.
            message_id (int): Message ID for the CoAP packet.
            options (dict): Dictionary of CoAP options.
            payload (bytes): Payload of the CoAP packet.
        """
        self.version = version
        self.message_type = message_type
        self.token = token
        self.code = code
        self.message_id = message_id
        self.options = options or {}
        self.payload = payload or b""
        self.sender_ip_port = sender_ip_port
        self.skt = skt

    def encode(self):
        """
        Encode the CoAP packet into a byte representation.

        Returns:
            bytes: Byte representation of the CoAP packet.
        """
        # CoAP Header
        header = bytes([
            (self.version << 6) | (self.message_type << 4) | (len(self.token) & 0b1111),
            self.code,
            (self.message_id >> 8) & 0xFF,
            self.message_id & 0xFF
        ])

        # CoAP Token
        token_bytes = bytes(self.token)

        options_bytes = b""
        prev_option_delta = 0

        for delta, option_value in sorted(self.options.items()):
            current_option_bytes = b""

            if isinstance(option_value, str):
                option_value_bytes = option_value.encode('utf-8')
            elif isinstance(option_value, int):
                option_value_bytes = option_value.to_bytes((option_value.bit_length() + 7) // 8, 'big')
            else:
                option_value_bytes = option_value

            delta_value = delta - prev_option_delta

            # minimum an option lower 13 must be provided
            current_option_bytes += bytes([(delta_value << 4) | len(option_value_bytes)])

            current_option_bytes += option_value_bytes

            prev_option_delta = delta
            options_bytes += current_option_bytes

        # CoAP Payload
        payload_bytes = bytes([0xFF]) + bytes(self.payload)

        # Combine all parts to form the CoAP packet
        coap_packet = header + token_bytes + options_bytes + payload_bytes

        return coap_packet

    @classmethod
    def decode(cls, coap_packet):
        # Header
        version = (coap_packet[0] >> 6) & 0b11
        message_type = (coap_packet[0] >> 4) & 0b11
        token_length = coap_packet[0] & 0b1111
        code = coap_packet[1]
        message_id = (coap_packet[2] << 8) | coap_packet[3]

        # Token
        token = coap_packet[4:4 + token_length]

        # Options
        options_start = 4 + len(token)
        options = {}
        prev_option_delta = 0

        while options_start < len(coap_packet) and coap_packet[options_start] != 0xFF:
            option_byte = coap_packet[options_start]
            delta = (option_byte >> 4) & 0b1111
            length = option_byte & 0b1111

            options_start += 1
            delta += prev_option_delta

            option_value_length = length

            option_value = coap_packet[options_start:options_start + option_value_length]

            options[delta] = CoapPacket.interpret_option_value(delta, option_value)

            options_start += option_value_length
            prev_option_delta = delta

        # Payload
        if options_start + 1 < len(coap_packet) and coap_packet[options_start] == 0xFF:
            payload = coap_packet[options_start + 1:]
        else:
            payload = b''

        return cls(version, message_type, token, code, message_id, options, payload)

    @staticmethod
    def interpret_option_value(delta, option_value):
        if delta == CoAPOptionDelta.IF_MATCH.value:
            return option_value
        elif (delta == CoAPOptionDelta.URI_HOST.value or delta == CoAPOptionDelta.URI_PATH.value
              or delta == CoAPOptionDelta.URI_QUERY.value or delta == CoAPOptionDelta.LOCATION_PATH.value
              or delta == CoAPOptionDelta.PROXY_URI.value or delta == CoAPOptionDelta.PROXY_SCHEME.value):
            return option_value.decode('utf-8')
        elif (delta == CoAPOptionDelta.ETAG.value or delta == CoAPOptionDelta.URI_PORT.value
              or delta == CoAPOptionDelta.MAX_AGE.value or delta == CoAPOptionDelta.ACCEPT.value
              or delta == CoAPOptionDelta.SIZE1.value or CoAPOptionDelta.BLOCK1 or CoAPOptionDelta.BLOCK2):
            return int.from_bytes(option_value, byteorder='big')
        elif delta == CoAPOptionDelta.IF_NONE_MATCH.value:
            return b''
        elif delta == CoAPOptionDelta.CONTENT_FORMAT.value:
            return int.from_bytes(option_value, byteorder='big')


def __repr__(self):
    """
        Return a string representation of the CoAPPacket object.

        Returns:
            str: String representation of the CoAPPacket object.
        """
    return f"CoAPPacket(version={self.version}, " \
           f"message_type={self.message_type}, " \
           f"token={self.token}, " \
           f"code={self.code}, " \
           f"message_id={self.message_id}, " \
           f"options={self.options}, " \
           f"payload={self.payload})"
