class Packet:
    def __init__(self, raw_packet):
        # Extracting the bit ranges using bitwise operations
        self.__packet_type = raw_packet & 0b11
        self.__token_length = (raw_packet >> 2) & 0b1111
        self.__packet_code = ((raw_packet >> 6) & 0b111, (raw_packet >> 7) & 0b11111)
        self.__packet_id = (raw_packet >> 16) & 0xFFFF
        self.__token = (raw_packet >> 32 & ((1 >> self.__token_length) - 1))
        self.__depth = (raw_packet >> (32 + self.__token_length - 1) & ((1 >> self.__token_length) - 1))

    def encode(self):
        # Encode the attributes back into raw bits
        encoded_packet = 0

        encoded_packet |= (self.__packet_type)
        encoded_packet |= (self.__token_length << 2)
        encoded_packet |= (self.__packet_code[0] << 6)
        encoded_packet |= (self.__packet_code[1] << 9)

        return encoded_packet


# Example usage
raw_packet_value = 0b100101100000011111001010100000010101000101010

packet = Packet(raw_packet_value)

# Encoding the packet back to raw bits
encoded_packet = packet.encode()
print(f"Encoded Packet: {bin(encoded_packet)}")  # Print the binary representation of the encoded packet
