class CoapPacket:
    """
    Represents a CoAP (Constrained Application Protocol) packet.

    This class provides methods for encoding and decoding CoAP
    packets, allowing for interoperability between CoAP-enabled devices.

    """

    def __init__(self, version=1, message_type=0, token=b"", code=0,
                 message_id=0, options=None, payload=None, sender_ip_port: tuple = ()):
        """
        Initializes a CoAPPacket instance with the provided parameters.

        Args:
            version (int): CoAP version (default is 1).
            message_type (int): Message type (0 for CON, 1 for NON, 2 for ACK, 3 for RST).
            token (bytes): Token for the CoAP packet.
            code (int): CoAP Code indicating the method or response code.
            message_id (int): Message ID for the CoAP packet.
            options (list): List of tuples representing CoAP options.
                Each tuple contains (Option Delta, Option Value).
            payload (bytes): Payload of the CoAP packet.
        """
        self.version = version
        self.message_type = message_type
        self.token = token
        self.code = code
        self.message_id = message_id
        self.options = options or []
        self.payload = payload or b""
        self.sender_ip_port = sender_ip_port

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

        # CoAP Options
        options_bytes = b""
        for option in self.options:
            delta = option[0]
            option_value = option[1]

            if isinstance(option_value, int):
                option_bytes = bytes([delta << 4 | len(bytes([option_value]))]) + bytes([option_value])
            elif isinstance(option_value, bytes):
                option_bytes = bytes([delta << 4 | len(option_value)]) + option_value
            elif isinstance(option_value, str):
                option_bytes = bytes([delta << 4 | len(option_value.encode('utf-8'))]) + option_value.encode('utf-8')
            else:
                # Handle other types accordingly
                pass

            options_bytes += option_bytes

        # CoAP Payload
        payload_bytes = bytes([0xFF]) + bytes(self.payload)

        # Combine all parts to form the CoAP packet
        coap_packet = header + token_bytes + options_bytes + payload_bytes

        return coap_packet

    @classmethod
    def decode(cls, coap_packet, sender_ip_port: tuple = ()):
        """
           Decode a byte representation of a CoAP packet.

           Args:
               coap_packet (bytes): Byte representation of the CoAP packet.

           Returns:
               CoAPPacket: Instance of CoAPPacket class.
               :param sender_ip_port:
               :param coap_packet:
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
        payload_start = options_start
        options = []
        while options_start < len(coap_packet) and coap_packet[options_start] != 0xFF:
            option_byte = coap_packet[options_start]
            delta = (option_byte >> 4) & 0b1111
            length = option_byte & 0b1111
            options_start += 1
            option_value = coap_packet[options_start:options_start + length]
            options_start += length
            options.append((delta, option_value))

        # payload
        if options_start + 1 < len(coap_packet) and coap_packet[options_start] == 0xFF:
            payload_start = options_start + 1
            payload = coap_packet[payload_start:]
        else:
            payload = b""

        return cls(version, message_type, token, code, message_id, options, payload, sender_ip_port)

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
