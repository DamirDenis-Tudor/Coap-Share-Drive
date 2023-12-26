import os

class FileUtilities:
    @staticmethod
    def file_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.isdir(file_path)

    @staticmethod
    def iterate_folder(source: str) -> list[str]:
        f = []
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                f.append(file_path)

        return f

    @staticmethod
    def split_file_on_packets(file_path: str, block_size: int):
        with open(file_path, 'rb') as file:
            while True:
                file_data = file.read(block_size)
                if not file_data:
                    break
                yield file_data

    @staticmethod
    def get_total_packets(file_path: str, block_size: int) -> int:
        file_size = os.path.getsize(file_path)
        total_packets = (file_size + block_size - 1) // block_size
        return total_packets


print(FileUtilities.iterate_folder("/home/damir/GithubRepos/proiectrcp2023-echipa-21-2023/test"))