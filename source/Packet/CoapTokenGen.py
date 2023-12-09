class CoapTokenGen:
    counter = -1

    @staticmethod
    def get_token() -> bytes:
        CoapTokenGen.counter += 1
        CoapTokenGen.counter = CoapTokenGen.counter % 2
        return int(CoapTokenGen.counter).to_bytes()
