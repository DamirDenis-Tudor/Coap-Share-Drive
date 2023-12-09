import json
from socket import socket

from source.Packet.CoapConfig import CoapOptionDelta, CoapContentFormat


class CoapPacket:
    """
    Represents a CoAP (Constrained Application Protocol) packet.

    This class provides methods for encoding and decoding CoAP
    packets, allowing for interoperability between CoAP-enabled devices.

    Reference: https://datatracker.ietf.org/doc/html/rfc7252#autoid-9
    """

    @staticmethod
    def _encode_option(option_value, delta_value) -> bytes:
        """
        Encode a CoAP option value and delta values/datatypes.
        For the option values there are three encoding possibilities: int/str/bytes

        Based on the option delta/value length the format will use or not the extended field.
        - When option delta exceeds allowed value|12| there may be need of some adjustments:
            - |13 <= delta_value < 269|: the most significant 4 bits from the first byte will be set to |13|;
              the next step is to use the first byte of the extended option delta and set it to: |delta_value - 13|;
            - |269 <= delta_value <= 65804|: the most significant 4 bits from the first byte must be set |14|;
              the next step is to use the all 2 bytes of the extended option delta and set it to: |delta_value - 269|;
        - The same logic applies for option_value_length

        Reference: https://datatracker.ietf.org/doc/html/rfc7252#autoid-10

        Args:
            option_value: Value of the CoAP option.
            delta_value: Delta value for the option.

        Returns:
            bytes: Encoded CoAP option.
        """
        if isinstance(option_value, str):
            option_bytes = option_value.encode('utf-8')
        elif isinstance(option_value, int):
            option_bytes = option_value.to_bytes((option_value.bit_length() + 7) // 8, 'big')
        else:
            option_bytes = option_value

        option_bytes_len = len(option_bytes)

        current_option_bytes = b""
        if delta_value < 13:
            if option_bytes_len < 13:
                current_option_bytes += bytes([(delta_value << 4) | option_bytes_len])
            elif 13 <= option_bytes_len < 269:
                current_option_bytes += bytes([(delta_value << 4) | 13])
                current_option_bytes += (option_bytes_len - 13).to_bytes(1, 'big')
            elif 269 <= option_bytes_len <= 65804:
                current_option_bytes += bytes([(delta_value << 4) | 14])
                current_option_bytes += (option_bytes_len - 269).to_bytes(2, 'big')
        elif 13 <= delta_value < 269:
            if option_bytes_len < 13:
                current_option_bytes += bytes([13 << 4 | option_bytes_len, delta_value - 13])
            elif 13 <= option_bytes_len < 269:
                current_option_bytes += bytes([13 << 4 | 13, delta_value - 13])
                current_option_bytes += (option_bytes_len - 13).to_bytes(1, 'big')
            elif 269 <= delta_value <= 65804:
                current_option_bytes += bytes([13 << 4 | 13, delta_value - 14])
                current_option_bytes += (option_bytes_len - 269).to_bytes(2, 'big')
        elif 269 <= delta_value <= 65804:
            if option_bytes_len < 13:
                current_option_bytes += bytes([14 << 4 | option_bytes_len])
                current_option_bytes += (delta_value - 269).to_bytes(2, 'big')
            elif 13 <= option_bytes_len < 269:
                current_option_bytes += bytes([14 << 4 | option_bytes_len])
                current_option_bytes += (delta_value - 269).to_bytes(2, 'big')
                current_option_bytes += (option_bytes_len - 13).to_bytes(1, 'big')
            elif 269 <= option_bytes_len <= 65804:
                current_option_bytes += bytes([14 << 4 | option_bytes_len])
                current_option_bytes += (delta_value - 269).to_bytes(2, 'big')
                current_option_bytes += (option_bytes_len - 269).to_bytes(2, 'big')

        return current_option_bytes + option_bytes

    @staticmethod
    def _decode_option(delta, option_value) -> object:
        """
        Interpret the value of a CoAP option based on the option delta.
        This method is useful because it classifies the format of the option value.
        If you'll add new option be sure to handle its format interpretation here.

        Args:
            delta: Delta value for the option.
            option_value: Encoded value of the CoAP option.

        Returns:
            Any: Interpreted value of the CoAP option.
        """
        if delta == CoapOptionDelta.IF_MATCH.value:
            return option_value
        elif (delta == CoapOptionDelta.URI_HOST.value or delta == CoapOptionDelta.URI_PATH.value
              or delta == CoapOptionDelta.URI_QUERY.value or delta == CoapOptionDelta.LOCATION_PATH.value
              or delta == CoapOptionDelta.PROXY_URI.value or delta == CoapOptionDelta.PROXY_SCHEME.value):
            return option_value.decode('utf-8')
        elif (delta == CoapOptionDelta.ETAG.value or delta == CoapOptionDelta.URI_PORT.value
              or delta == CoapOptionDelta.MAX_AGE.value or delta == CoapOptionDelta.ACCEPT.value
              or delta == CoapOptionDelta.SIZE1.value or CoapOptionDelta.BLOCK1 or CoapOptionDelta.BLOCK2):
            return int.from_bytes(option_value, byteorder='big')
        elif delta == CoapOptionDelta.IF_NONE_MATCH.value:
            return b''
        elif delta == CoapOptionDelta.CONTENT_FORMAT.value:
            return int.from_bytes(option_value, byteorder='big')

    def __init__(self, version=1, message_type=0, token=b"", code=0,
                 message_id=0, options=None, payload: object = None, sender_ip_port: tuple = (), skt: socket = None):
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

    def encode(self) -> bytes:
        """
        Encode the CoAP packet into a byte representation.

        This method encodes a CoAP packet into a byte representation, including the CoAP header, token, options,
        and payload. The CoAP header is constructed based on the version, message type, token length, code, and message
        ID. The token is included in the encoded packet, followed by the options, which are iteratively processed and
        encoded using the _code_option helper method. The payload, if present, is also included in the final byte
        representation. The encoded CoAP packet is then returned as bytes.

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
            delta_value = delta - prev_option_delta

            options_bytes += CoapPacket._encode_option(option_value, delta_value)

            prev_option_delta = delta

        # CoAP Payload
        payload_bytes = bytes([0xFF]) + bytes(self.payload)

        # Combine all parts to form the CoAP packet
        coap_packet = header + token_bytes + options_bytes + payload_bytes

        return coap_packet

    @classmethod
    def decode(cls, coap_packet, address: tuple, skt: socket):
        """
        Decode a byte representation of a CoAP packet.

        This class method decodes a byte representation of a CoAP packet into a CoapPacket instance.
        It extracts information from the CoAP header, including the version, message type, token length,
        code, and message ID. The token is then retrieved from the byte representation, followed by the
        options, which are processed using the _interpret_option_value helper method. The payload, if present,
        is also extracted. The decoded CoapPacket instance is then returned.

        Args:
            coap_packet (bytes): Byte representation of the CoAP packet.

        Returns:
            CoapPacket: Decoded CoapPacket instance.
            :param coap_packet:
            :param address:
            :param skt:
        """
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

            # Handle delta extension
            if delta == 13:
                delta += coap_packet[options_start + 1]
                options_start += 1
            elif delta == 14:
                delta += int.from_bytes(coap_packet[options_start + 1:options_start + 3], 'big')
                options_start += 2

            # Handle length extension
            if length == 13:
                length += coap_packet[options_start + 1]
                options_start += 1
            elif length == 14:
                length = int.from_bytes(coap_packet[options_start + 1:options_start + 3], 'big') + 269
                options_start += 2

            option_value = coap_packet[options_start + 1:options_start + 1 + length]

            options[delta + prev_option_delta] = CoapPacket._decode_option(delta, option_value)

            options_start += 1 + length
            prev_option_delta = delta + prev_option_delta

        # Payload
        if options_start + 1 < len(coap_packet) and coap_packet[options_start] == 0xFF:
            payload = coap_packet[options_start + 1:]
        else:
            payload = b''
        if CoapOptionDelta.CONTENT_FORMAT.value in options:
            if options[CoapOptionDelta.CONTENT_FORMAT.value] == CoapContentFormat.TEXT_PLAIN_UTF8.value:
                payload = payload.decode("utf-8")
            elif options[CoapOptionDelta.CONTENT_FORMAT.value] == CoapContentFormat.TEXT_PLAIN_UTF8.value:
                payload = json.loads(payload)
        return cls(version, message_type, token, code, message_id, options, payload, address, skt)

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
