import threading
from select import select
from socket import *

from source.Core.AbstractWorker import WorkerType
from source.Core.WorkerPool import WorkerPool
from source.Logger.Logger import logger
from source.Packet.CoapConfig import CoAPType, CoAPCodeFormat, CoAPOptionDelta, CoAPContentFormat
from source.Packet.CoapPacket import CoapPacket


class Client:
    def __init__(self, ip_addr: str, port: int):
        threading.current_thread().name = f"Client[{threading.current_thread().name}]"

        self.__socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self.__socket.bind((ip_addr, port))

        self.__worker_pool = WorkerPool(WorkerType.SERVER_WORKER)
        self.__worker_pool.start()

        self.__ui_thread = threading.Thread(target=self.run_ui, name="ClientUi[Thread-UI]")
        self.__ui_thread.start()

    @logger
    def listen(self):
        while True:
            active_socket, _, _ = select([self.__socket], [], [], 0.01)

            if active_socket:
                data, address = self.__socket.recvfrom(1032)
                self.__worker_pool.submit_task(CoapPacket.decode(data))

            self.__worker_pool.check_idle_workers()

    @logger
    def run_ui(self):
        coap_message = CoapPacket(
            version=1,
            message_type=CoAPType.CON.value,
            token=b"ABAB",
            code=CoAPCodeFormat.POST.value(),
            message_id=0,
            options={
                CoAPOptionDelta.URI_PATH.value: "/share_drive",
                CoAPOptionDelta.CONTENT_FORMAT.value: CoAPContentFormat.APPLICATION_JSON.value,
                CoAPOptionDelta.BLOCK1.value: 54
            },
            payload=""" {"instruction":"move", "source-path": "data", "destination-path":"/"} """.encode("utf-8")
        )
        self.__socket.sendto(coap_message.encode(), ("127.0.0.2", int(5683)))


if __name__ == "__main__":
    Client("127.0.0.3", int(5683)).listen()
