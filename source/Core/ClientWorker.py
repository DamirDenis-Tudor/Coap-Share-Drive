from source.Core.AbstractWorker import AbstractWorker
from source.File.FileHandler import FileHandler
from source.Packet.CoapConfig import CoapOptionDelta
from source.Packet.CoapPacket import CoapPacket
from source.Utilities.Logger import logger


class ClientWorker(AbstractWorker):
    def __init__(self, owner):
        super().__init__(owner)

        self.name = f"ClientWorker[{self.name}]"
        self.__file_handler = FileHandler()

    # for the long_term request/ responses, create transaction components that handle that
    def _solve_task(self, task):
        if task.has_option_block():
            match self.__file_handler.handle_packets(task):
                case FileHandler.FINISH_ASSEMBLY:
                    logger.log(f"Assembly of {task.token} finished.")
                case FileHandler.CONTINUE_ASSEMBLY:
                    pass
                case FileHandler.ALREADY_ASSEMBLED:
                    logger.log(f"Assembly of {task.token} already finished.")

            self._owner.remove_long_term_work(task.long_term_work_id())
