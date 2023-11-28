from source.Logger.Logger import logger
from source.Packet.Old_Packet.Packet import Packet


class Assembler:
    def __init__(self):
        self._files = {}
        self._file_paths = {}
        self._files_size = {}

    @logger
    def assemble_packets(self, packet: Packet):
        pass


