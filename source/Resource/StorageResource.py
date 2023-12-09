from source.Packet.CoapConfig import CoapOptionDelta, CoapCodeFormat
from source.Packet.CoapTemplates import CoapTemplates
from source.Resource.Resource import Resource
from source.Utilities.Logger import logger
from source.Utilities.Utilities import Utilities


class StorageResource(Resource):
    def __init__(self, path: str):
        super().__init__(path)

    @logger
    def get(self, request):
        if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                request.options.get(CoapOptionDelta.BLOCK1.value)):
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]

            block_op: bin = bin(request.options[CoapOptionDelta.BLOCK1.value])[-3:]
            if block_op.__contains__('b'):
                block_op = request.options[CoapOptionDelta.BLOCK1.value]
            else:
                block_op = int(block_op, 2)

            generator = Utilities.split_file_on_packets(path, 2 ** (block_op + 4))
            if generator:
                for payload in generator:
                    response = CoapTemplates.BYTES_RESPONSE.value()
                    response.payload = payload
                    request.skt.sendto(response.encode(), request.sender_ip_port)
            else:
                pass
        else:
            invalid_request = CoapTemplates.BAD_REQUEST.value()
            invalid_request.token = request.token
            request.skt.sendto(invalid_request.encode(), request.sender_ip_port)

    def post(self, request):
        pass

    def put(self, request):
        pass

    def delete(self, request):
        pass
