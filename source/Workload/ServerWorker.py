import json

from source.Logger.Logger import logger
from source.Packet.CoapConfig import CoAPOptionDelta, CoAPType, CoAPCodeFormat, CoAPContentFormat
from source.Workload.Core.AbstractWorker import CustomThread
from source.Workload.Core.Assembler import Assembler
from source.Workload.Core.Utilities import Utilities


class ServerWorker(CustomThread):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ServerWorker[{self.name}]"
        self._file_worker = Assembler()

    @logger
    def _solve_task(self):
        payload = Utilities.iterate_folder(self._task.payload)

        self._task.message_type = CoAPType.NON.value
        self._task.code = CoAPCodeFormat.EMPTY.value()
        self._task.options = {
            CoAPOptionDelta.CONTENT_FORMAT.value: CoAPContentFormat.TEXT_PLAIN_UTF8.value
        }

        skt = self._task.skt
        sender_ip = self._task.sender_ip_port
        for pld in Utilities.slit_string_on_packets(payload):
            logger.log(pld)
            self._task.payload = pld

        # skt.sendto(self._task.encode(), sender_ip)

        in_working = (self._task.token, self._task.sender_ip_port)
        self._shared_in_working.remove(in_working)
