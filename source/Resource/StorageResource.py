from time import sleep

from source.Packet.CoapConfig import CoapOptionDelta
from source.Packet.CoapPacket import CoapPacket
from source.Packet.CoapTemplates import CoapTemplates
from source.Transaction.CoapTransaction import CoapTransaction
from source.Resource.Resource import Resource
from source.Transaction.CoapTransactionPool import CoapTransactionPool
from source.Utilities.Logger import logger
from source.File.FileUtilities import FileUtilities


class StorageResource(Resource):
    def __init__(self, path: str):
        super().__init__(path)

    @logger
    def get(self, request):
        sleep(5)
        if (request.options.get(CoapOptionDelta.LOCATION_PATH.value) and
                request.options.get(CoapOptionDelta.BLOCK1.value)):
            path = self.get_path() + request.options[CoapOptionDelta.LOCATION_PATH.value]

            block_fields = CoapPacket.decode_option_block(request.options[CoapOptionDelta.BLOCK1.value])

            total_packets = FileUtilities.get_total_packets(path, block_fields["BLOCK_SIZE"])
            generator = FileUtilities.split_file_on_packets(path, block_fields["BLOCK_SIZE"])

            logger.log(f"Total packets: {total_packets}")
            if generator:

                index = 1
                for payload in generator:
                    if CoapTransactionPool().transaction_previously_failed(request.token):
                        logger.log("STOP GENERATING FAILED TRANSMISSION")
                        generator.close()
                        break

                    response = CoapTemplates.BYTES_RESPONSE.value_with(request.token, request.message_id + index)

                    response.payload = payload
                    response.skt = request.skt
                    response.sender_ip_port = request.sender_ip_port
                    response.options[CoapOptionDelta.BLOCK2.value] = (
                        CoapPacket.encode_option_block(index - 1, int(index != total_packets), block_fields["SZX"])
                    )

                    """
                        it's important to limit the number of active transactions, the reasons are described bellow: 
                        - a large number of transactions can reach at "Illegal block fragments." 
                          when the default port is used, the packets are malformed; 
                        - RAM reason: a large number of transactions will reach to a large number of bytes
                          stored at runtime;
                        - after numerous tests i reached to the conclusion that 50 is the optimal number
                          for both speed and consistency transfer;
                    """
                    while CoapTransactionPool().get_number_of_transactions() >= 25:
                        pass

                    if index == total_packets:
                        while CoapTransactionPool().get_number_of_transactions() != 0:
                            pass

                    response.skt.sendto(response.encode(), response.sender_ip_port)
                    CoapTransactionPool().add_transaction(CoapTransaction(response, request.message_id))

                    index += 1
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
