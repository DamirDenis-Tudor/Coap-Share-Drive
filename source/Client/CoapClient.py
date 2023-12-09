import threading

from source.Core.AbstractWorker import WorkerType
from source.Core.CoapWorkerPool import CoapWorkerPool
from source.Packet.CoapConfig import CoapOptionDelta
from source.Packet.CoapTemplates import CoapTemplates
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

            if data == "1":
                coap_message = CoapTemplates.DOWNLOAD.value()
                coap_message.options[CoapOptionDelta.LOCATION_PATH.value] = "/CoAPthon/coapping.py"
                coap_message.options[CoapOptionDelta.URI_PATH.value] = "share_drive"
            elif data == "2":
                coap_message = CoapTemplates.UPLOAD.value()
            elif data == "3":
                coap_message = CoapTemplates.MV.value()
            elif data == "4":
                coap_message = CoapTemplates.DELETE.value()
            elif data == "5":
                coap_message = CoapTemplates.SYNC.value()

            self._socket.sendto(coap_message.encode(), ("127.0.0.2", int(5683)))
            break


if __name__ == "__main__":
    th = threading.Thread(target=CoapClient("127.0.0.3", int(5683)).listen)
    th.start()
    th.join()
