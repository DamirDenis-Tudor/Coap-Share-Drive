import json
import os


class Utilities:
    @staticmethod
    def file_exists(file_path: str):
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str):
        return os.path.exists(file_path) and os.path.isdir(file_path)

    @staticmethod
    def iterate_folder(source: str):
        entities = {'FOLDERS': [], 'FILES': {}}
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                entities['FILES'][file_path] = Utilities.get_total_packets(file_path)

            for folder in dirs:
                folder_path = os.path.join(root, folder)
                entities['FOLDERS'].append(folder_path)

        return json.dumps(entities)

    @staticmethod
    def split_file_on_packets(file_path: str, block_size: int):
        with open(file_path, 'rb') as file:
            while True:
                file_data = file.read(block_size)
                if not file_data:
                    break
                yield file_data

    @staticmethod
    def slit_string_on_packets(string: str):
        i = 0
        stop = False
        while True:
            str_data = None
            if (i + 1) * PAYLOAD_LENGTH < len(string):
                str_data = string[i * PAYLOAD_LENGTH:(i + 1) * PAYLOAD_LENGTH]
            elif not stop:
                str_data = string[i * PAYLOAD_LENGTH:]
                stop = True
            i = i + 1
            if str_data is None:
                break
            yield str_data

    @staticmethod
    def get_packet_at_index(file_path, packet_index):
        with open(file_path, 'rb') as file:
            file.seek((packet_index - 1) * PAYLOAD_LENGTH)
            return file.read(PAYLOAD_LENGTH)

    @staticmethod
    def get_total_packets(file_path: str):
        file_size = os.path.getsize(file_path)
        total_packets = (file_size + PAYLOAD_LENGTH - 1) // PAYLOAD_LENGTH
        return total_packets
