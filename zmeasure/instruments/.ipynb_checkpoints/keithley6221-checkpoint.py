from statistics import mean, stdev
import pyvisa as visa
from driver import Driver

class Keithley6221(Driver):

    def __init__(self, gpib_addr=23,name='KL6221',read_code=[]):
        """
        Constructor for Keithley 6221 Sourcemeter

        :param gpib_addr: GPIB address (configured on Keithley 6221)
        """
        super().__init__()
        self.gpib_addr = str(gpib_addr)
        self._name = name
        
        
        self.read_code = read_code

    @property
    def instrument(self):
        if self._instrument == None:
            self._instrument = self.resource_manager.open_resource(f"GPIB{self.gpib_serial}::{self.gpib_addr}")
            self.instrument.read_termination = '\n'
            # self.instrument.read_termination = '\n'
        return self._instrument
    
    def set_output(self,value):
        if value:
            self.instrument.write('OUTP 1')
        else:
            self.instrument.write('OUTP 0')
    def get_output(self):
        response = self.instrument.query('OUTP?')
        if response:
            return [1],[self._name+':'+'Iout_on']
        else:
            return [0],[self._name+':'+'Iout_on']
            
    def get_ac_source(self):
        response = self.instrument.query('SOUR:WAVE:AMPL?')
        source_value = float(response)
        freq = self.instrument.query('SOUR:WAVE:FREQ?')
        freq_value = float(freq)
        return [source_value,freq_value],[self._name+':'+'Iamp',self._name+':'+'Freq']

    def set_ac_source(self,source_value):
        response = self.instrument.write('SOUR:WAVE:AMPL {}'.format(source_value))

    def set_ac_freq(self,freq_value):
        response = self.instrument.write('SOUR:WAVE:FREQ {}'.format(freq_value))
        
    def get_ac_range_mode(self):
        ### mode 0:Best 1:Fix
        value = self.instrument.query('SOUR:WAVE:RANG?')
        return  [value],[self._name+':'+'RangeMode']
    def set_ac_range_mode(self,mode):
        ### mode 0:Best 1:Fix
        if mode == 0:
            code = 'BEST'
        else:
            code = 'FIX'
        self.instrument.write('SOUR:WAVE:RANG '+code)

    def set_ac_output(self,value):
        if value:
            self.instrument.write('SOUR:WAVE:ARM')
            self.instrument.write('SOUR:WAVE:INIT')
        else:
            self.instrument.write('SOUR:WAVE:ABOR')
            
    def get_ac_output(self):
        response = int(self.instrument.query('SOUR:WAVE:ARM?'))
        if response:
            return [1],[self._name+':'+'Iac_on']
        else:
            return [0],[self._name+':'+'Iac_on']
    # Common commands

    def clear_status(self):
        """Clears all event registers and Error Queue."""
        self.instrument.write('*cls')

    def reset_to_defaults(self):
        """Resets to defaults of Sourcemeter."""
        self.instrument.write('*rst')

    def identify(self):
        """Returns manufacturer, model number, serial number, and firmware revision levels."""
        response = self.instrument.write('*idn?')
        return {'manufacturer': response[0],
                'model': response[1],
                'serial number': response[2],
                'firmware revision level': response[3]
                }

    def send_bus_trigger(self):
        """Sends a bus trigger to SourceMeter."""
        self.instrument.write('*trg')
