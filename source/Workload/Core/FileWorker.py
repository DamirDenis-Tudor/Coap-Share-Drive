import os

from source.Logger.Logger import logger
from source.Packet.Config import EntityType, PAYLOAD_LENGTH, PacketType, PayloadFormat, FILE_PATH, TOTAL_FILE_PACKETS
from source.Packet.Packet import Packet


class FileWorker:
    def __init__(self):
        self._entities = []
        self._files = {}
        self._file_paths = {}
        self._files_size = {}

    def iterate_folder(self, source: str):
        depth_order = {}
        for root, dirs, files in os.walk(source):
            depth = len(root.split('/'))
            if depth not in depth_order:
                depth_order[depth] = 0
            self._entities.append(({root: EntityType.FOLDER}, (depth, depth_order[depth])))

            for file in files:
                file_path = os.path.join(root, file)
                self._entities.append(({file_path: EntityType.FILE}, (depth, depth_order[depth])))
                depth_order[depth] += 1

            for folder in dirs:
                folder_path = os.path.join(root, folder)
                self._entities.append(({folder_path: EntityType.FOLDER}, (depth, depth_order[depth])))
                depth_order[depth] += 1

    @logger
    def assemble_packets(self, packet: Packet):
        if packet.get_packet_type() == PacketType.CON:

            if (packet.get_packet_id() == FILE_PATH and
                    packet.get_payload_format() == PayloadFormat.STRING):

                if packet.get_entity_type() == EntityType.FILE:
                    depth_tuple = (packet.get_packet_depth(), packet.get_packet_depth_order())
                    self._file_paths[depth_tuple] = packet.get_payload()

                elif packet.get_entity_type() == EntityType.FOLDER:
                    os.makedirs(f"/home/coap/{packet.get_payload()}")

            elif (packet.get_packet_id() == TOTAL_FILE_PACKETS and
                  packet.get_payload_format() == PayloadFormat.UINT):

                depth_tuple = (packet.get_packet_depth(), packet.get_packet_depth_order())
                self._files_size[depth_tuple] = packet.get_payload()

            else:
                depth_tuple = (packet.get_packet_depth(), packet.get_packet_depth_order())
                file_path = self._file_paths[depth_tuple]
                self._files[file_path][packet.get_packet_id()-2] = packet.get_payload()

    @staticmethod
    def file_exists(file_path: str):
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str):
        return os.path.exists(file_path) and os.path.isdir(file_path)

    @staticmethod
    def get_total_packets(file_path: str):
        file_size = os.path.getsize(file_path)
        total_packets = (file_size + PAYLOAD_LENGTH - 1) // PAYLOAD_LENGTH
        return total_packets

    @logger
    def split_file_on_packets(self, file_path: str):
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(PAYLOAD_LENGTH)
                if not data:
                    break
                yield data

    @logger
    def get_packet_at_index(self, file_path, packet_index):
        with open(file_path, 'rb') as file:
            file.seek((packet_index - 1) * PAYLOAD_LENGTH)
            return file.read(PAYLOAD_LENGTH)
