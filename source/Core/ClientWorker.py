from source.Core.AbstractWorker import AbstractWorker
from source.Packet.CoapConfig import CoapOptionDelta
from source.Packet.CoapPacket import CoapPacket
from source.Utilities.Logger import logger


class ClientWorker(AbstractWorker):
    def __init__(self, owner):
        super().__init__(owner)
        self.name = f"ClientWorker[{self.name}]"

        self._handled_responses = 0
        self._total_responses = 0
        self._index = 0

        self._write_index = 0
        self._received_packets: dict[int:bytes] = {}

    # for the long_term request/ responses, create transaction components that handle that
    def _solve_task(self):
        option = CoapPacket().decode_option_block(self._task.options[CoapOptionDelta.BLOCK2.value])

        logger.log(f"write_index: {self._write_index}, {self._task}")
        if self._write_index == option["NUM"]:
            self._received_packets[option["NUM"]] = self._task.payload
            index = self._write_index

            while self._write_index + 1 in self._received_packets:
                self._write_index += 1

            for i in range(index, self._write_index+1):
                with open("/home/damir/GithubRepos/proiectrcp2023-echipa-21-2023/mama.zip", 'ab') as file:
                    file.write(self._received_packets[i])
                    self._received_packets.pop(i)
            self._write_index += 1
        else:
            self._received_packets[option["NUM"]] = self._task.payload

        if not option["M"]:
            self._total_responses = option["NUM"]

        self._handled_responses += 1

        logger.log(self._handled_responses)
        if self._total_responses != 0:
            if self._handled_responses == self._total_responses:
                self._owner.remove_long_term_work(self._task.token)

        # block_size = option["BLOCK_SIZE"]
        #
        # if self._last_index < index:
        #     # If there are gaps in the sequence, write null bytes followed by the payload
        #     self._last_index = index
        #     with open("mama.zip", 'wb') as f:
        #         f.write(bytes([0] * index * block_size) + self._task.payload)
        # else:
        #     # If the index is not greater than _last_index, write the payload at the specified index
        #     with open("mama.zip", 'rb+') as f:
        #         f.seek(index * block_size)
        #         f.write(self._task.payload)