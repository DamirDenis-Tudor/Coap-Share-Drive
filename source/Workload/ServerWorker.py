from datetime import datetime
from time import sleep

from source.Logger.Logger import logger
from source.Packet.Config import PacketType, PacketCode, EntityType, PayloadFormat
from source.Packet.Packet import Packet
from source.Workload.Core.CustomThread import CustomThread
from source.Workload.Core.FileWorker import FileWorker


class ServerWorker(CustomThread):
    def __init__(self, shared_in_working: list[tuple[int, str]]):
        super().__init__(shared_in_working)
        self.name = f"ServerWorker[{self.name}]"
        self._file_worker = FileWorker()

    @logger
    def _solve_task(self):
        skt = self._task.get_socket()
        dest = self._task.get_external_ip()

        if self._task.get_packet_code() == PacketCode.RequestCode.GET:

            if (self._task.get_entity_type() == EntityType.FILE and
                    self._file_worker.file_exists(self._task.get_payload())):
                file_path = self._task.get_payload()

                self._task.set_packet_code(PacketCode.RequestCode.EMPTY)
                self._task.set_payload_format(PayloadFormat.UINT)
                self._task.set_payload(self._file_worker.get_total_packets(file_path))
                skt.sendto(Packet.encode(self._task.to_dict()), dest)

                sleep(10)

                self._task.set_packet_type(PacketType.NON)
                self._task.set_payload_format(PayloadFormat.OPAQUE)

                start_time = datetime.now()

                for packet in self._file_worker.split_file_on_packets(file_path):
                    self._task.set_packet_id(self._task.get_packet_id() + 1)
                    self._task.set_payload(packet)
                    # skt.sendto(Packet.encode(self._task.to_dict()), dest)

                end_time = datetime.now()
                total_execution_time = end_time - start_time

                print(f"Total Execution Time: {total_execution_time}")

            elif (self._task.get_entity_type() == EntityType.FOLDER and
                  self._file_worker.folder_exists(self._task.get_payload())):
                pass

            else:
                self._task.set_packet_type(PacketType.RST)
                self._task.set_packet_code(PacketCode.ServerErrorResponse.INVALID_PATH)
                skt.sendto(Packet.encode(self._task.to_dict()), dest)

        elif self._task.get_packet_code() == PacketCode.RequestCode.POST:
            pass

        elif self._task.get_packet_code() == PacketCode.RequestCode.PUT:
            pass

        elif self._task.get_packet_code() == PacketCode.RequestCode.DELETE:
            pass

        in_working = (self._task.get_token(), self._task.get_external_ip())
        self._shared_in_working.remove(in_working)
