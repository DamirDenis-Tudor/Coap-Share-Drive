import json
from copy import deepcopy, copy
from socket import socket

from coap_core.coap_packet.coap_config import CoapOptionDelta, CoapContentFormat


class CoapPacket:
    """
    Represents a CoAP (Constrained Application Protocol) packet.

    This class provides methods for encoding and decoding CoAP
    packets, allowing for interoperability between CoAP-enabled devices.

    Reference: https://datatracker.ietf.org/doc/html/rfc7252#autoid-9
    """

    @staticmethod
    def decode_option_block(option) -> dict | None:
        """
        Decode an option block value into a dictionary of its components.

        Args:
        - option (int): The option block value to be decoded.

        Returns:
        - dict: A dictionary containing the decoded components - {'SZX': szx, 'M': m, 'NUM': num, 'BLOCK_SIZE': actual_block_size}.
        """
        if not option:
            return None

        # Extracting individual bits using bit masking and shifting
        num = option >> 4
        m = (option >> 3) & 0b1
        szx = option & 0b111

        # Calculating the actual block size
        actual_block_size = 2 ** (szx + 4)

        return {'NUM': num, 'M': m, 'SZX': szx, 'BLOCK_SIZE': actual_block_size}

    @staticmethod
    def encode_option_block(num: int, m: int, szx: int = 6) -> int:
        """
        Encode values of NUM, M, and SZX into an option block value.

        Args:
        - num (int): The value of NUM (four bits).
        - m (int): The value of M (one bit).
        - Szx (int): The value of SZX (three bits).

        Returns:
        - int: The resulting option block value.
        """
        # Combining values to create the option block
        option = (num << 4) | (m << 3) | szx

        return option

    @staticmethod
    def _encode_option(option_value, delta_value) -> bytes:
        """
        Encode a CoAP option value and delta values/datatypes.
        For the option values, there are three encoding possibilities: int/str/bytes

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
        If you'll add a new option, be sure to handle its format interpretation here.

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
              or delta == CoapOptionDelta.SIZE1.value or CoapOptionDelta.BLOCK1 or CoapOptionDelta.BLOCK2
              or delta == CoapOptionDelta.SIZE2.value):
            return int.from_bytes(option_value, byteorder='big')
        elif delta == CoapOptionDelta.IF_NONE_MATCH.value:
            return b''
        elif delta == CoapOptionDelta.CONTENT_FORMAT.value:
            return int.from_bytes(option_value, byteorder='big')

    def __init__(self, version=0, message_type=0, token=b"", code=0,
                 message_id=0, options=None, payload: bytes | str = None,
                 internal_computation=False, sender_ip_port: tuple = (), skt: socket = None):
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

        self.needs_internal_computation = internal_computation
        self.encoded = b""

    def __repr__(self):
        """
        Return a string representation of the CoAPPacket object.

        Returns:
            str: String representation of the CoAPPacket object.
        """
        readable_options = deepcopy(self.options)
        for option in readable_options.keys():
            if option == CoapOptionDelta.BLOCK2.value or option == CoapOptionDelta.BLOCK1.value:
                readable_options[option] = CoapPacket.decode_option_block(readable_options[option])
        return f"CoAPPacket(version={self.version}, " \
               f"message_type={self.message_type}, " \
               f"token={self.token}, " \
               f"code={self.code}, " \
               f"message_id={self.message_id}, " \
               f"options={readable_options}, "

    def __copy__(self):
        """
        Create a shallow copy of the CoapPacket instance.

        Returns:
            CoapPacket: Shallow copy of the CoapPacket instance.
        """
        return self.__class__(
            version=copy(self.version),
            message_type=copy(self.message_type),
            token=copy(self.token),
            code=copy(self.code),
            message_id=copy(self.message_id),
            options=deepcopy(self.options),
            payload=copy(self.payload),
            internal_computation=copy(self.needs_internal_computation),
            sender_ip_port=copy(self.sender_ip_port),
            skt=copy(self.skt)
        )

    def has_option_block(self):
        return CoapOptionDelta.BLOCK1.value in self.options or CoapOptionDelta.BLOCK2.value in self.options

    def get_block_id(self) -> int | None:
        if CoapOptionDelta.BLOCK1.value in self.options:
            return CoapPacket.decode_option_block(self.options[CoapOptionDelta.BLOCK1.value])["NUM"]
        elif CoapOptionDelta.BLOCK2.value in self.options:
            return CoapPacket.decode_option_block(self.options[CoapOptionDelta.BLOCK2.value])["NUM"]
        else:
            return None

    def get_option_code(self):
        if CoapOptionDelta.BLOCK1.value in self.options:
            return CoapOptionDelta.BLOCK1.value
        elif CoapOptionDelta.BLOCK2.value in self.options:
            return CoapOptionDelta.BLOCK2.value
        else:
            return None

    def get_size_code(self):
        if CoapOptionDelta.SIZE1.value in self.options:
            return CoapOptionDelta.SIZE1.value
        elif CoapOptionDelta.SIZE2.value in self.options:
            return CoapOptionDelta.SIZE2.value
        else:
            return None

    def get_size_code_based_on_option(self):
        if CoapOptionDelta.BLOCK1.value in self.options:
            return CoapOptionDelta.SIZE1.value
        elif CoapOptionDelta.BLOCK2.value in self.options:
            return CoapOptionDelta.SIZE2.value
        else:
            return None

    def work_id(self) -> tuple:
        return self.sender_ip_port, self.token, self.message_id, self.get_block_id()

    def general_work_id(self) -> tuple:
        return self.sender_ip_port, self.token

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
        if self.encoded:
            return self.encoded

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
        if self.payload:
            if CoapOptionDelta.CONTENT_FORMAT.value in self.options:
                if self.options[CoapOptionDelta.CONTENT_FORMAT.value] == CoapContentFormat.TEXT_PLAIN_UTF8.value:
                    payload_bytes = bytes([0xFF]) + bytes(self.payload.encode(encoding="utf-8"))
                elif self.options[CoapOptionDelta.CONTENT_FORMAT.value] == CoapContentFormat.APPLICATION_JSON.value:
                    if not isinstance(self.payload, str):
                        self.payload = json.dumps(self.payload)
                    payload_bytes = bytes([0xFF]) + bytes(self.payload.encode(encoding="utf-8"))
                else:
                    payload_bytes = bytes([0xFF]) + bytes(self.payload)
            else:

                payload_bytes = bytes([0xFF]) + bytes(self.payload)
        else:
            payload_bytes = bytes([0xFF])

        # Combine all parts to form the CoAP packet
        coap_packet = header + token_bytes + options_bytes + payload_bytes

        self.encoded = coap_packet

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

            options[delta + prev_option_delta] = CoapPacket._decode_option(delta + prev_option_delta, option_value)

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
            elif options[CoapOptionDelta.CONTENT_FORMAT.value] == CoapContentFormat.APPLICATION_JSON.value:
                payload = json.loads(payload)
        return cls(version, message_type, token, code, message_id, options, payload, False, address, skt)

    def send(self):
        """
        Send the CoapPacket over the socket to the specified address.
        """
        self.skt.sendto(self.encode(), self.sender_ip_port)
