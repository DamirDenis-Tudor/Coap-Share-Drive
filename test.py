from coap_core.coap_utilities.coap_singleton import CoapSingleton


class Test1(metaclass=CoapSingleton):
    def __init__(self, data):
        self.data = 1


class Test2(metaclass=CoapSingleton):
    def __init__(self):
        self.data = 1

        print(id(Test1(self.data)))


Test2()
print(id(Test1(3)))
