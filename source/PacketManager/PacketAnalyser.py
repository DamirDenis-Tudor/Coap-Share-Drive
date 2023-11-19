import threading
from socket import socket

from source.PacketManager.Packet import Packet


class PacketAnalyser:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Double-checked locking to ensure only one instance is created
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(PacketAnalyser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.__folders = {}
        self.__files_depth = {}
        self.__files = {}
        self.__skt = None

    def set_socket(self, skt: socket):
        self.__skt = skt

    def analyse_packet(self, packet: Packet):
        # verify the format of the packet

        pass

