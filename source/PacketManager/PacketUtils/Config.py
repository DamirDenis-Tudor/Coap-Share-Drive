from enum import Enum


class TransmissionParameters(Enum):
    """
        MAX_TRANSMIT_WAIT = ACK_TIMEOUT * ((2 ** ( MAX_RETRANSMIT + i )) - 1) * ACK_RANDOM_FACTOR
    """
    ACK_TIMEOUT = 2
    ACK_RANDOM_FACTOR = 1.5
    MAX_RETRANSMIT = 4
    NSTART = 1
    DEFAULT_LEISURE = 5


class PacketType(Enum):
    CON = "00"
    NON = "01"
    ACK = "10"
    RST = "11"

    @staticmethod
    def get_field_name(value):
        for member in PacketType:
            if member.value == value:
                return member
        return None


class PayloadFormat(Enum):
    EMPTY = "00"
    OPAQUE = "01"
    UINT = "10"
    STRING = "11"

    @staticmethod
    def get_field_name(value):
        for member in PayloadFormat:
            if member.value == value:
                return member
        return None


class PacketCode:
    class RequestCode(Enum):
        EMPTY = "00000000"
        GET = "00000001"
        POST = "00000010"
        PUT = "00000011"
        DELETE = "00000100"

    class SuccessResponse(Enum):
        CREATED = "01000001"
        DELETED = "01000010"
        VALID = "01000011"
        CHANGED = "01000100"
        CONTENT = "01000101"

    class ClientErrorResponse(Enum):
        BAD_REQUEST = "10000000"
        UNAUTHORIZED = "10000001"
        NOT_FOUND = "10000100"
        METHOD_NOT_ALLOWED = "10000101"

    class ServerErrorResponse(Enum):
        INTERNAL_SERVER_ERROR = "10100000"
        NOT_IMPLEMENTED = "10100001"
        SERVICE_UNAVAILABLE = "10100011"

    @staticmethod
    def get_field_name(value):
        for inner_class in [PacketCode.RequestCode, PacketCode.SuccessResponse,
                            PacketCode.ClientErrorResponse, PacketCode.ServerErrorResponse]:
            for member in inner_class:
                if member.value == value:
                    return member
        return None


class EntityType(Enum):
    NONE = "00"
    FILE = "01"
    FOLDER = "10"

    @staticmethod
    def get_field_name(value):
        for member in EntityType:
            if member.value == value:
                return member
        return None


class NextState(Enum):
    PACKET = "0"
    NO_PACKET = "1"

    @staticmethod
    def get_field_name(value):
        for member in NextState:
            if member.value == value:
                return member
        return None


TOKEN_LENGTH = "0111"
SERVER_IP_PORT = ('127.0.0.1', 6000)
