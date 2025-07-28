import logging

import pyvisa as visa
from driver import Driver
# create a logger object for this module
logger = logging.getLogger(__name__)
# added so that log messages show up in Jupyter notebooks
logger.addHandler(logging.StreamHandler())


class Sr860(Driver):
    """Interface to a Stanford Research Systems 830 lock in amplifier."""

    def __init__(self, gpib_addr=4,name='SR860',read_code=[0,1,2,3]):
        """Create an instance of the Sr860 object.

        :param gpib_addr: GPIB address of the SR860
        """
#         try:
#             # the pyvisa manager we'll use to connect to the GPIB resources
#             self.resource_manager = visa.ResourceManager()
#         except OSError:
#             logger.exception("\n\tCould not find the VISA library. Is the VISA driver installed?\n\n")
        super().__init__()
        self.gpib_addr = str(gpib_addr)
        self._name = name
        self.multiple_names = {
            0: "X",
            1: "Y",
            2: "R",
            3: "Theta",
            4: "Aux1",
            5: "Aux2",
            6: "Aux3",
            7: "Aux4",
        }
        self.read_code = read_code
        self._name=name
 
    @property
    def instrument(self):
        if self._instrument == None:
            self._instrument = self.resource_manager.open_resource(f"GPIB{self.gpib_serial}::{self.gpib_addr}")
        return self._instrument
    @property
    def sync_filter(self):
        """
        The state of the sync filter (< 200 Hz).
        """
        return self.instrument.query_ascii_values('SYNC?')[0]

    @sync_filter.setter
    def sync_filter(self, value):
        if isinstance(value, bool):
            self.instrument.query_ascii_values('SYNC {}'.format(int(value)))
        else:
            raise RuntimeError('Sync filter input expects [True|False].')

    @property
    def low_pass_filter_slope(self):
        """
        The low pass filter slope in units of dB/octave. The choices are:

         i   slope(dB/oct) 
        ---  -------------
         0         6
         1        12
         2        18
         3        24
        """
        response = self.instrument.query_ascii_values('OSFL?')[0]
        slope = {'0': '6 dB/oct', '1': '12 dB/oct', '2': '18 dB/oct', '3': '24 dB/oct'}
        return slope[response]

    @low_pass_filter_slope.setter
    def low_pass_filter_slope(self, value):
        """
        Sets the low pass filter slope.

        :param value: The slope in units of dB/oct.
        """
        if value in (6, 12, 18, 24):
            slope = {6: '0', 12: '1', 18: '2', 24: '3'}
            self.instrument.query_ascii_values('OSFL {}'.format(slope[value]))
        else:
            raise RuntimeError('Low pass filter slope only accepts [6|12|18|24].')

    @property
    def reserve(self):
        """
        The reserve mode of the SR830.
        """
        reserve = {'0': 'high', '1': 'normal', '2': 'low noise'}
        response = self.instrument.query_ascii_values('RMOD?')[0]
        return reserve[response]

    @reserve.setter
    def reserve(self, value):
        if isinstance(value, str):
            mode = value.lower()
        elif isinstance(value, int):
            mode = value
        else:
            raise RuntimeError('Reserve expects a string or integer argument.')
        
        modes_dict = {'hi': 0, 'high': 0,   'high reserve': 0, 0: 0,
                      'normal': 1,          1: 1,
                      'lo': 2, 'low': 2,    'low noise': 2, 2: 2}
        if mode in modes_dict.keys():
            self.instrument.query_ascii_values('RMOD {}'.format(mode))
        else:
            raise RuntimeError('Incorrect key for reserve.')

    @property
    def frequency(self):
        """
        The frequency of the output signal.
        """
        return self.instrument.query_ascii_values('FREQ?')[0]

    @frequency.setter
    def frequency(self, value):
        if 0.001 <= value <= 102000:
            self.instrument.write("FREQ {}".format(value))
        else:
            raise RuntimeError('Valid frequencies are between 0.001 Hz and 102 kHz.')
    
    # INPUT and FILTER

    @property
    def input(self):
        """
        The input on the SR830 machine. Possible values:
            0: A
            1: A-B
            2: I (1 MOhm)
            3: I (100 MOhm)
        """
        return self.instrument.query_ascii_values('ISRC?')[0]

    @input.setter
    def input(self, input_value):
        input_ = {'0': 0, 0: 0, 'A': 0,
                  '1': 1, 1: 1, 'A-B': 1,    'DIFFERENTIAL': 1,
                  '2': 2, 2: 2, 'I1': 2,     'I1M': 2,           'I1MOHM': 2,
                  '3': 3, 3: 3, 'I100': 3,   'I100M': 3,         'I100MOHM': 3}
        if isinstance(input_value, str):
            query = input_value.upper().replace('(', '').replace(')', '').replace(' ', '')
        else:
            query = input_value

        if query in input_.keys():
            command = input_[query]
            self.instrument.write("ISRC {}".format(command))
        else:
            raise RuntimeError('Unexpected input for SR830 input command.')

    @property
    def input_shield_grounding(self):
        """Tells whether the shield is floating or grounded."""
        response = self.instrument.query_ascii_values("IGND?")[0]
        return {'0': 'Float', '1': 'Ground'}[response]

    @input_shield_grounding.setter
    def input_shield_grounding(self, ground_type):
        ground_types = {'float': '0', 'floating': '0', '0': '0',
                        'ground': '1', 'grounded': '1', '1': '1'}
        if ground_type.lower() in ground_types.keys():
            self.instrument.write("IGND {}".format(ground_type.lower()))
        else:
            raise RuntimeError('Improper input grounding shield type.')

    @property
    def phase(self):
        """
        The phase of the output relative to the input.
        """
        return self.instrument.query_ascii_values('PHAS?')[0]

    @phase.setter
    def phase(self, value):
        if (isinstance(value, float) or isinstance(value, int)) and -360.0 <= value <= 729.99:
            self.instrument.write("PHAS {}".format(value))
        else:
            raise RuntimeError('Given phase is out of range for the SR830. Should be between -360.0 and 729.99.')
    
    @property
    def amplitude(self):
        """
        The amplitude of the voltage output.
        """
        return self.instrument.query_ascii_values('SLVL?')[0]
    
    @amplitude.setter
    def amplitude(self, value):
        if 0.004 <= value <= 5.0:
            self.instrument.write("SLVL {}".format(value))
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

    @property
    def sensitivity(self):
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
        return sensitivity[sens_index]

    @sensitivity.setter
    def sensitivity(self, value):
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
            0: X
            1: Y
            2: R
            3: Theta
            4: Aux in 1
            5: Aux in 2
            6: Aux in 3
            7: Aux in 4


        :param values: A variable number of arguments to obtain output
        :return:
        """
        
        command_string = "SNAPD?"
        
        output_names = [self._name+':'+self.multiple_names[single_value] for single_value in values]
#         response = self.instrument.query_ascii_values(command_string.format(*values))
        response = self.instrument.query_ascii_values(command_string)
        responses = [float(x) for x in response]
        assert len(responses) == len(output_names), "%s reading interrupted"%self._name
        return responses, output_names
    def partial_multiple_output(self):
        self.auto_range()
        self.auto_scale()
        return self.multiple_output(*self.read_code)

    
    def auto_gain(self):
        """
        Mimics pressing the Auto Gain button. Does nothing if the time
        constant is more than 1 second.
        """
        self.instrument.query_ascii_values("AGAN")
    def auto_range(self):
        """
        Mimics pressing the Auto Range button. Does nothing if the time
        constant is more than 1 second.
        """
        self.instrument.write("ARNG")
    def auto_scale(self):
        """
        Mimics pressing the Auto Scale button. Does nothing if the time
        constant is more than 1 second.
        """
        self.instrument.write("ASCL")
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
