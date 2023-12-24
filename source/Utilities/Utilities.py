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
    def get_total_packets(file_path: str, block_size: int):
        file_size = os.path.getsize(file_path)
        total_packets = (file_size + block_size - 1) // block_size
        return total_packets
