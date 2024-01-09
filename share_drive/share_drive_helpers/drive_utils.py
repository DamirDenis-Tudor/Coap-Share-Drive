import os
import zipfile

from coap_core.coap_utilities.coap_logger import logger


class DriveUtilities:
    """
    DriveUtilities provides a set of utility methods for file and folder operations.

    Author: Damir Denis-Tudor
    """

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check if a file exists at the specified path.

        Parameters:
        - file_path (str): The path to the file.

        Returns:
        - bool: True if the file exists, False otherwise.
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def folder_exists(file_path: str) -> bool:
        """
        Check if a folder exists at the specified path.

        Parameters:
        - file_path (str): The path to the folder.

        Returns:
        - bool: True if the folder exists, False otherwise.
        """
        return os.path.exists(file_path) and os.path.isdir(file_path)

    @staticmethod
    def get_total_paths(source: str):
        """
        Count the total number of paths (files and directories) in the given source directory.

        Parameters:
        - source (str): The path to the source directory.

        Returns:
        - int: The total number of paths.
        """
        index = 0
        for root, dirs, files in os.walk(source):
            for _ in dirs:
                index += 1
            for _ in files:
                index += 1
        return index

    @staticmethod
    def get_total_packets(file_path: str, block_size: int) -> int:
        """
        Calculate the total number of packets needed to transmit a file in chunks of the specified block size.

        Parameters:
        - file_path (str): The path to the file.
        - block_size (int): The size of each packet in bytes.

        Returns:
        - int: The total number of packets.
        """
        file_size = os.path.getsize(file_path)
        total_packets = (file_size + block_size - 1) // block_size
        return total_packets

    @staticmethod
    def compress_folder(input_folder):
        """
        Compress the contents of the specified folder into a zip file.

        Parameters:
        - input_folder (str): The path to the input folder.

        Returns:
        - str: The path to the created zip file.
        """
        output_zip = f"{input_folder}.zip"
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_STORED) as zip_file:
            for folder, folders, filenames in os.walk(input_folder):
                for filename in filenames:
                    file_path = os.path.join(folder, filename)
                    arcname = os.path.relpath(file_path, input_folder)
                    zip_file.write(file_path, arcname)
        return output_zip

    @staticmethod
    def decompress_folder(zip_file_path: str):
        """
        Decompress the contents of the specified zip file into a folder with the same name.

        Parameters:
        - zip_file_path (str): The path to the zip file.
        """
        output_folder = zip_file_path.split(".zip")[0]
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)

    @staticmethod
    def delete_file(file_path):
        """
        Delete the specified file, log an error if it fails.

        Parameters:
        - file_path (str): The path to the file.
        """
        try:
            os.remove(file_path)
        except OSError as e:
            logger.debug(f"Error deleting file '{file_path}': {e}")

    @staticmethod
    def split_on_paths(source: str, relative_to: str):
        """
        Generate a list of dictionaries representing paths (directories and files)
        relative to the specified base directory.

        Parameters:
        - source (str): The path to the source directory.
        - relative_to (str): The common prefix to be removed from paths.

        Returns:
        - list: List of dictionaries representing paths.
        """
        paths = [{"dummy_key": "dummy_value"}]
        for root, dirs, files in os.walk(source):
            for d in dirs:
                dir_path = os.path.join(root, d)
                # Remove the common prefix to get the relative path
                dir_path = dir_path.split(relative_to)[1].removeprefix("/")
                paths.append({"folder": dir_path})
            for file in files:
                file_path = os.path.join(root, file)
                # Remove the common prefix to get the relative path
                file_path = file_path.split(relative_to)[1].removeprefix("/")
                paths.append({"file": file_path})
        return paths

    @staticmethod
    def split_on_packets(file_path: str, block_size: int):
        """
        Generate chunks of a file with the specified block size.

        Parameters:
        - file_path (str): The path to the file.
        - block_size (int): The size of each packet in bytes.

        Yields:
        - bytes: Chunks of the file data.
        """
        with open(file_path, 'rb') as file:
            while True:
                file_data = file.read(block_size)
                if not file_data:
                    break
                yield file_data
