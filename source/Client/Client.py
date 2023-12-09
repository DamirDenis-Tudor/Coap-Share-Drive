import threading
from time import sleep

from source.Core.AbstractWorker import WorkerType
from source.Core.CoapWorkerPool import CoapWorkerPool
from source.Utilities.Logger import logger
from source.Packet.CoapConfig import CoapType, CoapCodeFormat, CoapOptionDelta, CoapContentFormat
from source.Packet.CoapPacket import CoapPacket


class Client(CoapWorkerPool):
    def __init__(self, ip_address, port, ):
        threads: list[threading.Thread] = [
            threading.Thread(target=self.run_ui),
        ]

        super().__init__(WorkerType.SERVER_WORKER, ip_address, port, threads)

    @logger
    def run_ui(self):
        coap_message = CoapPacket(
            version=1,
            message_type=4,
            token=int(134).to_bytes(),
            code=CoapCodeFormat.POST.value(),
            message_id=0,
            options={
                CoapOptionDelta.URI_PATH.value: "/share_drive",
                CoapOptionDelta.CONTENT_FORMAT.value: CoapContentFormat.APPLICATION_JSON.value,
            },
            payload=""" {"instruction":"move", "source-path": "data", "destination-path":"/"} """.encode("utf-8")
        )
        self._socket.sendto(coap_message.encode(), ("127.0.0.2", int(5683)))


if __name__ == "__main__":
    Client("127.0.0.3", int(5683)).listen()
