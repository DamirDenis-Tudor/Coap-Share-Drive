from enum import Enum


class CoapType(Enum):
    """
    Enum class representing CoAP message types.
    """
    CON = 0
    NON = 1
    ACK = 2
    RST = 3

    @staticmethod
    def is_valid(item):
        for member in CoapType:
            if member.value == item:
                return True
        return False


class CoapCodeFormat(Enum):
    """
    Enum class representing CoAP code format possibilities.

    Each enumeration value represents a specific combination of CoAP message type and code.
    """
    # Request Codes
    EMPTY = (0, 0)
    GET = (0, 1)
    POST = (0, 2)
    PUT = (0, 3)
    DELETE = (0, 4)
    FETCH = (0, 5)

    # Response Codes
    SUCCESS_CREATED = (2, 1)
    SUCCESS_DELETED = (2, 2)
    SUCCESS_VALID = (2, 3)
    SUCCESS_CHANGED = (2, 4)
    SUCCESS_CONTENT = (2, 5)
    SUCCESS_CONTINUE = (2, 31)

    CLIENT_ERROR_BAD_REQUEST = (4, 0)
    CLIENT_ERROR_UNAUTHORIZED = (4, 1)
    CLIENT_ERROR_FORBIDDEN = (4, 3)
    CLIENT_ERROR_NOT_FOUND = (4, 4)
    CLIENT_ERROR_METHOD_NOT_ALLOWED = (4, 5)
    CLIENT_ENTITY_INCOMPLETE = (4, 8)
    CLIENT_ERROR_CONFLICT = (4, 9)
    CLIENT_ERROR_PRECONDITION_FAILED = (4, 12)
    CLIENT_ERROR_REQUEST_ENTITY_TOO_LARGE = (4, 13)
    CLIENT_ERROR_UNSUPPORTED_CONTENT_FORMAT = (4, 15)

    SERVER_ERROR_INTERNAL_SERVER_ERROR = (5, 0)
    SERVER_ERROR_NOT_IMPLEMENTED = (5, 1)
    SERVER_ERROR_BAD_GATEWAY = (5, 2)
    SERVER_ERROR_SERVICE_UNAVAILABLE = (5, 3)
    SERVER_ERROR_GATEWAY_TIMEOUT = (5, 4)
    SERVER_ERROR_PROXYING_NOT_SUPPORTED = (5, 5)

    def __init__(self, message_type, code):
        self.message_type = message_type
        self.code = code

    def __repr__(self):
        return f"CoAPCodeFormat({self.message_type}, {self.code})"

    def value(self) -> int:
        """
        Get the integer representation of the CoAP code.
        """
        return (self.message_type << 5) | self.code

    @staticmethod
    def is_method(code):
        return (code == CoapCodeFormat.GET.value() or
                code == CoapCodeFormat.PUT.value() or
                code == CoapCodeFormat.POST.value() or
                code == CoapCodeFormat.DELETE.value() or
                code == CoapCodeFormat.FETCH.value())

    @staticmethod
    def is_success(code):
        return (code == CoapCodeFormat.SUCCESS_CONTENT.value() or
                code == CoapCodeFormat.SUCCESS_CHANGED.value() or
                code == CoapCodeFormat.SUCCESS_VALID.value() or
                code == CoapCodeFormat.SUCCESS_CREATED.value() or
                code == CoapCodeFormat.SUCCESS_DELETED.value() or
                code == CoapCodeFormat.SUCCESS_CONTINUE.value())

    @staticmethod
    def is_valid(item):
        for member in CoapCodeFormat:
            if member.value() == item:
                return True
        return False

    @staticmethod
    def get_field_name(value):
        for member in CoapCodeFormat:
            if member.value() == value:
                return member
        return None


class CoapOptionDelta(Enum):
    """
    Enum class representing CoAP option deltas.

    BLOCK FORMAT 23|27:
        - SZX -> size of the block with the length of 3 bits: 0 for 2**4 ... 6 for 2**10
                actual block size will be 2**(SZX + 4) ;
        - M   -> 1 bit flag the specifies if there will be a next block
        - NUM -> the current block number being requested/received

        BLOCK1 -> REQUEST ex. GET
        BLOCK2 -> RESPONSE ex. PUT

    """
    IF_MATCH = 1

    URI_HOST = 3

    ETAG = 4

    IF_NONE_MATCH = 5

    URI_PORT = 7

    LOCATION_PATH = 8

    URI_PATH = 11

    CONTENT_FORMAT = 12

    MAX_AGE = 14

    URI_QUERY = 15

    ACCEPT = 17

    LOCATION_QUERY = 20

    BLOCK2 = 23
    BLOCK1 = 27

    PROXY_URI = 35
    PROXY_SCHEME = 39

    SIZE1 = 60
    SIZE2 = 28

    @staticmethod
    def is_valid(items: dict):
        if len(items) > 0:
            for item in items:
                valid_item = False
                for member in CoapOptionDelta:
                    if member.value == item:
                        valid_item = True
                if not valid_item:
                    return False
        return True


class CoapContentFormat(Enum):
    """
    Enum class representing CoAP content formats.
    """
    TEXT_PLAIN_UTF8 = 0
    APPLICATION_LINK_FORMAT = 40
    APPLICATION_XML = 41
    APPLICATION_OCTET_STREAM = 42
    APPLICATION_EXI = 47
    APPLICATION_JSON = 50

    @staticmethod
    def is_valid(item):
        for member in CoapContentFormat:
            if member.value == item:
                return True
        return False


CURRENT_TOKEN = -1


def gen_token() -> bytes:
    global CURRENT_TOKEN
    CURRENT_TOKEN += 1
    return int(CURRENT_TOKEN).to_bytes()


def verify_format(task) -> bool:
    if (task.version != 1
            or not CoapType.is_valid(task.message_type)
            or not CoapCodeFormat.is_valid(task.code)
            or not CoapOptionDelta.is_valid(task.options)):
        return False

    return True
