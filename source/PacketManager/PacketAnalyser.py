import threading

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

    def analyse_packet(self, packet: Packet):
        pass

