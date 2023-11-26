import os

from source.Packet.Old_Packet.Config import EntityType, PAYLOAD_LENGTH


class Utilities:
    @staticmethod
    def file_exists(file_path: str):
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str):
        return os.path.exists(file_path) and os.path.isdir(file_path)

    @staticmethod
    def iterate_folder(source: str):
        entities = {"FOLDERS": [], "FILES": {}}
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                entities["FILES"][file_path] = Utilities.get_total_packets(file_path)

            for folder in dirs:
                folder_path = os.path.join(root, folder)
                entities["FOLDERS"].append(folder_path)

        return entities

    @staticmethod
    def split_file_on_packets(file_path: str):
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(PAYLOAD_LENGTH)
                if not data:
                    break
                yield data

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


print(Utilities.iterate_folder("/home/damir/GithubRepos/proiectrcp2023-echipa-21-2023/test"))
