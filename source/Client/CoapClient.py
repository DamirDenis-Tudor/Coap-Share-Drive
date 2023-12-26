import threading

from source.Core.AbstractWorker import WorkerType
from source.Core.CoapWorkerPool import CoapWorkerPool
from source.Packet.CoapConfig import CoapOptionDelta
from source.Packet.CoapTemplates import CoapTemplates
from source.Packet.CoapTokenGen import CoapTokenGen
from source.Transaction.CoapTransaction import CoapTransaction
from source.Transaction.CoapTransactionPool import CoapTransactionPool
from source.Utilities.Logger import logger
from source.Packet.CoapPacket import CoapPacket


class CoapClient(CoapWorkerPool):
    def __init__(self, ip_address, port):
        super().__init__(WorkerType.CLIENT_WORKER, ip_address, port)

        self.add_background_thread(threading.Thread(target=self.run_ui))

    @logger
    def run_ui(self):
        coap_message = CoapPacket()
        while True:
            print("1 -> download\n2 -> upload\n3 -> rename/move\n4 -> delete\n5 -> sync")
            data = "1"
            path = "/CoAPthon/files.zip"
            #path = "/CoAPthon/coapping.py"
            if data == "1":
                coap_message = CoapTemplates.DOWNLOAD.value_with(CoapTokenGen.get_token(), 0)
                coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = path
                coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
                coap_message.skt = self._socket
                coap_message.sender_ip_port = ("127.0.0.2", int(5683))
            elif data == "2":
                coap_message = CoapTemplates.UPLOAD.value()
            elif data == "3":
                coap_message = CoapTemplates.MV.value()
            elif data == "4":
                coap_message = CoapTemplates.DELETE.value()
            elif data == "5":
                coap_message = CoapTemplates.SYNC.value()

            coap_message.skt.sendto(coap_message.encode(), coap_message.sender_ip_port)
            CoapTransactionPool().add_transaction(CoapTransaction(coap_message, 0))

            break

    def get_resource(self, path):
        pass


if __name__ == "__main__":
    CoapClient("127.0.0.7", int(5683)).listen()
