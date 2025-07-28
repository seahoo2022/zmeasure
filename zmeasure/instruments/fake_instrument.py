from ..driver import Driver
import time
from multiprocessing import Manager

class FakeInstrument(Driver):
    def __init__(self, name='FakeInstrument', shared=None):
        super().__init__()
        self.name = name
        self.controller = shared if shared is not None else 0

    def read(self, *args, **kwargs):
        time.sleep(0.1)
        return [self.controller.value if hasattr(self.controller, 'value') else self.controller], [self.name]

    def write(self, value, *args, **kwargs):
        time.sleep(0.1)
        if hasattr(self.controller, 'value'):
            self.controller.value = value
        else:
            self.controller = value
        return self.controller