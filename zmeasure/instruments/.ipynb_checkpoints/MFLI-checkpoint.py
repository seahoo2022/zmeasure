import logging
from driver import Driver
import zhinst.utils
from zhinst.ziPython import ziDAQServer
import zhinst.utils.shfqa as shfqa_utils
import numpy as np
import json
mean = np.mean
# from driver import Driver
# create a logger object for this module
# logger = logging.getLogger(__name__)
# added so that log messages show up in Jupyter notebooks
# logger.addHandler(logging.StreamHandler())
# /dev5793/demods/0/sample.Theta
name_mapper = {
    'X':'x',
    'Y':'y',
    'Theta':None,
    'Freq':'frequency',
    'R':None
}
class MFLI(Driver):

    def __init__(self, server_host='192.168.1.10',device_id='dev5793',server_port=8004,read_channel={'0':['X','Y','R','Theta','Freq']},read_mode='head',name=None):
        """Create an instance of the MFLI object
        """
        super().__init__()
#         try:
#             # the pyvisa manager we'll use to connect to the GPIB resources
#             self.resource_manager = visa.ResourceManager()
#         except OSError:
#             logger.exception("\n\tCould not find the VISA library. Is the VISA driver installed?\n\n")
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.api_level = 6
        if name == None:
            self._name = device_id
        else:
            self._name = name
        self.device_id = device_id
        self.read_channel = read_channel
        # self.read_code = read_code
        self._read_mode = read_mode
        self.gpib_flag = False
        # self._name=name
        self.subscription = []
        self.gpib_flag = False
        self.subscribed = False
    def subscribe(self):
        if len(self.read_channel) != 0:
            for key in self.read_channel:
                self.subscription.append(f'/{self._name}/demods/{key}/sample')
        for path in self.subscription:
            self.daq.subscribe(self.subscription)
        self.subscribed = True
    def get_data(self):
        if not self.subscribed:
            self.subscribe()
        # print(self.subscription)
        response = self.daq.poll(0.1,10)
        # print(response)
        data = []
        dataName = []
        for key in self.read_channel:
            result = response[self.device_id]['demods'][key]['sample']
            for entry in self.read_channel[key]: 
                if entry == 'R':
                    data.append((mean(result['x'])**2+mean(result['y'])**2)**0.5)
                    dataName.append(self._name + ':' + key + ':' + 'R')
                    continue
                if entry == 'Theta':
                    data.append(np.angle(complex(mean(result['x']),mean(result['y'])))/np.pi*180)
                    dataName.append(self._name + ':' + key + ':' + 'Theta')
                    continue
                data.append(mean(result[name_mapper[entry]]))
                dataName.append(self._name + ':' + key + ':' + entry)
        return data, dataName
    def set_frequency(self,frequency,demod_idx):
        pass