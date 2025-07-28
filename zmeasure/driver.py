from zhinst.ziPython import ziDAQServer
import pyvisa as visa
class Driver:
    def __init__(self):
        self._instrument = None
        self._resource_manager = None
        self._daq = None
        self._name=None
        self.gpib_flag = True
        self.gpib_serial=0
    @property
    def daq(self):
        if self._daq == None:
            print("Initializing Server")
            self._daq = ziDAQServer(self.server_host,self.server_port,self.api_level)
            self._daq.connectDevice(self.device_id,"PCIe")
        return self._daq

    @property
    def resource_manager(self):
        if self._resource_manager == None:
            print(f"{self._name} Initializaing resource manager")
            self._resource_manager = visa.ResourceManager()
        return self._resource_manager
    def reset(self):
        if self.gpib_flag and self._instrument != None:
            self._instrument.close()
        else:
            self.subscribed = False
        self._instrument = None
        self._resource_manager = None
        self._daq = None
    def cls(self):
        self.instrument.write('*CLS')
    def idn(self):
        return self.instrument.query('*IDN?')
    def query(self,cmd):
        if isinstance(cmd,str):
            cmd = cmd.encode()
        elif isinstance(cmd,bytes):
            pass
        self.instrument.write_raw(cmd)
        return self.instrument.read()