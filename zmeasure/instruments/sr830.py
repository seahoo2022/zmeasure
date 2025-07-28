import logging

import pyvisa as visa
from ..driver import Driver
import numpy as np
# create a logger object for this module
logger = logging.getLogger(__name__)
# added so that log messages show up in Jupyter notebooks
logger.addHandler(logging.StreamHandler())


class Sr830(Driver):
    """Interface to a Stanford Research Systems 830 lock in amplifier."""

    def __init__(self, gpib_addr=1,name='SR830',read_code=[1,2,3,4]):
        """Create an instance of the Sr830 object.

        :param gpib_addr: GPIB address of the SR830
        """
#         try:
#             # the pyvisa manager we'll use to connect to the GPIB resources
#             self.resource_manager = visa.ResourceManager()
#         except OSError:
#             logger.exception("\n\tCould not find the VISA library. Is the VISA driver installed?\n\n")
        super().__init__()
        # self.gpib_serial = gpib_serial
        self.gpib_addr = gpib_addr
        self._name = name
        self.multiple_names = {
            1: "X",
            2: "Y",
            3: "R",
            4: "Theta",
            5: "Aux1",
            6: "Aux2",
            7: "Aux3",
            8: "Aux4",
            9: "Freq",
            10: "CH1display",
            11: "CH2display"
        }
        self.read_code = read_code
        self._name=name

    @property
    def instrument(self):
        if self._instrument == None:
            self._instrument = self.resource_manager.open_resource(f"GPIB{self.gpib_serial}::{self.gpib_addr}")
            # self.instrument.read_termination = '\n'
        return self._instrument
    def query(self,cmd):
        self.instrument.write_raw(cmd.encode())
        return self.instrument.read()

    def get_frequency(self):
        """
        The frequency of the output signal.
        """
        response = self.instrument.query('FREQ?').strip().split(',')[0]
        # print(response)
        response = float(response)
        return [response],[self._name+":"+"Freq"]

    def set_frequency(self, value):
        if 0.001 <= value <= 102000:
            self.instrument.write("FREQ {}".format(value))
        else:
            raise RuntimeError('Valid frequencies are between 0.001 Hz and 102 kHz.')
  
    def get_amplitude(self):
        """
        The amplitude of the voltage output.
        """
        """
        The frequency of the output signal.
        """
        response = self.instrument.query('SLVL?').strip().split(',')[0]
        # print(response)
        response = float(response)
        return [response],[self._name+":"+"Amp"]
        # return [self.instrument.query_ascii_values('SLVL?')[0]],[self._name+":"+"Amp"]
    
    def set_amplitude(self, value):
        if 0.004 <= value <= 5.0:
            self.instrument.write("SLVL {}".format(value))
        elif 0.004 > value >=0:
            self.instrument.write("SLVL 0.004".format(value))
        else:
            raise RuntimeError('Given amplitude is out of range. Expected 0.004 to 5.0 V.')

    @property
    def time_constant(self):
        """
        The time constant of the SR830.
        """
        time_constant = {0: '10 us',  10: '1 s',
                         1: '30 us',  11: '3 s',
                         2: '100 us', 12: '10 s',
                         3: '300 us', 13: '30 s',
                         4: '1 ms',   14: '100 s',
                         5: '3 ms',   15: '300 s',
                         6: '10 ms',  16: '1 ks',
                         7: '30 ms',  17: '3 ks',
                         8: '100 ms', 18: '10 ks',
                         9: '300 ms', 19: '30 ks'}

        const_index = self.instrument.query_ascii_values('OFLT?')[0]
        return time_constant[const_index]

    @time_constant.setter
    def time_constant(self, value):
        if value.lower() == 'increment':
            if self.time_constant + 1 <= 19:
                self.time_constant += 1
        elif value.lower() == 'decrement':
            if self.time_constant - 1 >= 0:
                self.time_constant -= 1
        elif 0 <= value <= 19:
            self.instrument.write("SENS {}".format(value))
        else:
            raise RuntimeError('Time constant index must be between 0 and 19 (inclusive).')

    def get_sensitivity(self):
        """Voltage/current sensitivity for inputs."""
        sensitivity = {0: "2 nV/fA",		13: "50 uV/pA",
                       1: "5 nV/fA",		14: "100 uV/pA",
                       2: "10 nV/fA",	    15: "200 uV/pA",
                       3: "20 nV/fA",	    16: "500 uV/pA",
                       4: "50 nV/fA",	    17: "1 mV/nA",
                       5: "100 nV/fA",	    18: "2 mV/nA",
                       6: "200 nV/fA",	    19: "5 mV/nA",
                       7: "500 nV/fA",	    20: "10 mV/nA",
                       8: "1 uV/pA",		21: "20 mV/nA",
                       9: "2 uV/pA",		22: "50 mV/nA",
                       10: "5 uV/pA",		23: "100 mV/nA",
                       11: "10 uV/pA",	    24: "200 mV/nA",
                       12: "20 uV/pA",	    25: "500 mV/nA",
                       26: "1 V/uA"}

        sens_index = self.instrument.query_ascii_values('SENS?')[0]
        return sens_index

    
    def set_sensitivity(self, value):
        if isinstance(value, int) and 0 <= value <= 26:
            self.instrument.write("SENS {}".format(value))
        else:
            raise RuntimeError("Invalid input for sensitivity.")
                
    def set_display(self, channel, display, ratio=0):
        """Set the display of the amplifier.

        Display options are:
        (for channel 1)     (for channel 2)
            0: X            0: Y
            1: R            1: Theta
            2: X Noise      2: Y Noise
            3: Aux in 1     3: Aux in 3
            4: Aux in 2     4: Aux in 4

        Ratio options are (i.e. divide output by):
            0: none         0: none
            1: Aux in 1     1: Aux in 3
            2: Aux in 2     2: Aux in 4

        Args:
            channel (int): which channel to modify (1 or 2)
            display (int): what to display
            ratio (int, optional): display the output as a ratio
        """
        self.instrument.write("DDEF {}, {}, {}".format(channel, display, ratio))
        
    def get_display(self, channel):
        """Get the display configuration of the amplifier.

        Display options are:
        (for channel 1)     (for channel 2)
            0: X            0: Y
            1: R            1: Theta
            2: X Noise      2: Y Noise
            3: Aux in 1     3: Aux in 3
            4: Aux in 2     4: Aux in 4

        Args:
            channel (int): which channel to return the configuration for

        Returns:
            int: the parameter being displayed by the amplifier
        """
        return self.instrument.query_ascii_values("DDEF? {}".format(channel))
    
    def single_output(self, value):
        """Get the current value of a single parameter.
        Possible parameter values are:
            1: X
            2: Y
            3: R
            4: Theta

        Returns:
            float: the value of the specified parameter
        """
        return self.instrument.query_ascii_values("OUTP? {}".format(value))[0]
            
    def multiple_output(self, *values):
        """Queries the SR830 for multiple output. See below for possibilities.

        Possible parameters are:
            1: X
            2: Y
            3: R
            4: Theta
            5: Aux in 1
            6: Aux in 2
            7: Aux in 3
            8: Aux in 4
            9: Reference frequency
            10: CH1 display
            11: CH2 display

        :param values: A variable number of arguments to obtain output
        :return:
        """
        # print(values)
        command_string = "SNAP? " + ("{}," * len(values))[:-1]
        
        output_names = [self._name+':'+self.multiple_names[single_value] for single_value in values]
        response = self.query(command_string.format(*values)).strip().split(',')
        responses = [float(x) for x in response]
        if len(responses) != len(output_names):
            print("%s reading interrupted"%self._name)
            print(responses)
            raise Exception
            
        return responses, output_names
    def partial_multiple_output(self):
        return self.multiple_output(*self.read_code)

    
    def auto_read(self):
        """
        Mimics pressing the Auto Gain button. Does nothing if the time
        constant is more than 1 second.
        """
        sensitivity_num = {0: 2e-9,		13: 50e-6,
                       1: 5e-9,		14: 100e-6,
                       2:10e-9,	    15: 200e-6,
                       3:20e-9,	    16: 500e-6,
                       4: 50e-9,	    17:1e-3,
                       5: 100e-9,	    18: 2e-3,
                       6:200e-9,	    19: 5e-3,
                       7: 500e-9,	    20:10e-3,
                       8: 1e-6,		21:20e-3,
                       9: 2e-6,		22: 50e-3,
                       10: 5e-6,		23: 0.1,
                       11: 10e-6,	    24: 0.2,
                       12:20e-6,	    25: 0.5,
                       26: 1.0}
        reading_data,reading_name = self.partial_multiple_output()
        sens_levl = self.get_sensitivity()
        sens_num = sensitivity_num[sens_levl]
        # sens = self.get_sensitivity()
        maxer = max(abs(np.array(reading_data[:2])))
        # print(reading_data)
        while (abs(maxer) > sens_num or abs(maxer) < sens_num*0.2) and sens_levl>=0 and sens_levl<=26:
            if abs(maxer) > sens_num:
                # print(sens_levl)
                sensnumsList = sorted(list(sensitivity_num.values()))
                for i in range(26):
                    if sensnumsList[i] < maxer < sensnumsList[i+1]:
                        break
                self.set_sensitivity(i+1)
                sens_num = sensitivity_num[sens_levl]
                sens_levl = i+1
                reading_data,reading_name = self.partial_multiple_output()
                maxer = max(reading_data[:2])
            elif abs(maxer) < sens_num*0.2:
                # sens_levl = 
                sens_levl =int(sens_levl-1)
                # print(sens_levl)
                self.set_sensitivity(sens_levl)
                sens_num = sensitivity_num[sens_levl]
                reading_data,reading_name = self.partial_multiple_output()
                maxer = max(reading_data[:2])

        return reading_data, reading_name
        
    def partial_auto_read(self):
        return self.auto_read()
    def auto_reserve(self):
        """
        Mimics pressing the Auto Reserve button.
        """
        self.instrument.query_ascii_values("ARSV")

    def auto_phase(self):
        """
        Mimics pressing the Auto Phase button.
        """
        self.instrument.query_ascii_values("APHS")

    def auto_offset(self, parameter):
        """
        Automatically offsets the given voltage parameter.

        :param parameter: A string from ['x'|'y'|'r'], case insensitive.
        """
        self.instrument.query_ascii_values("AOFF {}".format(parameter.upper()))

    # Data storage commands

    @property
    def data_sample_rate(self):
        """Data sample rate, which can be 62.5 mHz, 512 Hz, or Trigger.
        
        Expected strings: 62.5, 62.5 mhz, 62.5mhz, mhz, 0, 512, 512hz, 512 hz,
        hz, 13, trig, trigger, 14."""
        rate_dict = {'0': '62.5 mHz', '13': '512 Hz', '14': 'Trigger'}

        response = self.instrument.query_ascii_values("SRAT?")[0]
        return rate_dict[response]

    @data_sample_rate.setter
    def data_sample_rate(self, rate):
        rate_dict = {'62.5': '0',   '0': '0',   '62.5mhz': '0', 'mhz': '0',
                     '512': '13',   '13': '13', '512hz': '13',  'hz': '13',
                     'trig': '14',  '14': '14', 'trigger': '14'}
        rate_value = str(rate).lower().replace(' ', '')
        if rate_value in rate_dict.keys():
            self.instrument.write("SRAT {}".format(rate_value))
        else:
            raise RuntimeError('Sample rate input not recognized.')

    @property
    def data_scan_mode(self):
        """Data scan mode, which is either a 1-shot or a loop.
        
        Expected strings: 1-shot, 1 shot, 1shot, loop."""
        scan_modes = {'0': '1-shot', '1': 'loop'}
        response = self.instrument.query_ascii_values("SEND?")[0]
        return scan_modes[response]

    @data_scan_mode.setter
    def data_scan_mode(self, scan_mode):
        scan_modes = {'1shot': '0', 'loop': '1'}
        mode = scan_mode.replace('-', '').replace(' ', '')
        self.instrument.write("SEND {}".format(scan_modes[mode]))

    @property
    def trigger_starts_scan(self):
        """Determines if a Trigger starts scan mode."""
        response = self.instrument.query_ascii_values("TSTR?")[0]
        return {'0': False, '1': True}[response]

    @trigger_starts_scan.setter
    def trigger_starts_scan(self, starts):
        starts_value = int(bool(starts))
        self.instrument.write("TSTR {}".format(starts_value))

    def trigger(self):
        """Sends a software trigger."""
        self.instrument.write("TRIG")

    def start_scan(self):
        """Starts or continues a scan."""
        self.instrument.write("STRT")

    def pause_scan(self):
        """Pauses a scan."""
        self.instrument.write("PAUS")

    def reset_scan(self):
        """Resets a scan and releases all stored data."""
        self.instrument.write("REST")
