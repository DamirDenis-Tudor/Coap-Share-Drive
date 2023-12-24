from source.Core.AbstractWorker import AbstractWorker
from source.Packet.CoapConfig import CoapOptionDelta
from source.Packet.CoapPacket import CoapPacket


class ClientWorker(AbstractWorker):
    def __init__(self, owner):
        super().__init__(owner)
        self.name = f"ClientWorker[{self.name}]"

        self._handled_responses = 0
        self._total_responses = 0

    # for the long_term request/ responses, create transaction components that handle that
    def _solve_task(self):
        option = CoapPacket().decode_option_block(self._task.options[CoapOptionDelta.BLOCK2.value])
        index = option["NUM"]
        has_next = option["M"]

        if not has_next:
            self._total_responses = index

        self._handled_responses += 1

        if self._total_responses != 0:
            if self._handled_responses == self._total_responses:
                pass
                # self._owner.remove_long_term_work()

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