from statistics import mean, stdev
import pyvisa as visa
import time
from driver import Driver
import subprocess
from drivers.ppmsCMD import ppmsQuery
class PPMS(Driver):

    
    def __init__(self, gpib_addr=15,name='PPMS',read_code=[6,0]):
        """

        :param gpib_addr: GPIB address (configured on PPMS)
        """
        super().__init__()
        self.gpib_addr = str(gpib_addr)
        self.channelNames ={
            0: 'Code',
            1: 'T_pm',
            2: 'H_pm'
        }

        self._name = name
        self.read_code = read_code
        self.gpib_serial = 0
    def query(self,strarg):
        return ppmsQuery(strarg)
    def cls_ppms(self):
        self.query('*CLS')

    # @property
    # def instrument(self):
    #     if self._instrument == None:
    #         self._instrument = self.resource_manager.open_resource(f"GPIB{self.gpib_serial}::{self.gpib_addr}")
    #         # self._instrument.baud_rate=9600
    #         self._instrument.timeout=5000
    #         self._instrument.write_termination = None
    #         self._instrument.read_termination = ';'
    #     return self._instrument


    # # source functions
    # def init_timer(self):
    #     self.instrument.write('TIME 0 0 0')
    # def get_timer(self):
    #     response = self.query(b'TIME?').stripe()[:-1].split(',')
    #     return response

    def get_set_field(self):
        """
        :param value: FIELD RATE APPROACHCODE
        approachcode: 0: Fast settle approach; 1: No overshoot approach; 2: Oscillate approach
        """
#         self.instrument.lock_excl()
#         self.cls_ppms()
        response = self.query("FIELD?").strip()[:-1].split(',')
        # print(response)
        #self.instrument
        if len(response[-1]) == 0:
            response[-1] = '0'
        response = [float(entry) for entry in response]
        response_name = ['SetField','FieldRate','FieldApproachMode','MagnetMode']
#         self.cls_ppms()
        return response, [self._name+':'+name for name in response_name]

    def set_field(self, *value):
#         self.instrument.lock_excl()
#         self.cls_ppms()
        str_values = [str(single_value) for single_value in value]
        self.query("FIELD "+' '.join(str_values))
#         self.cls_ppms()
        #self.instrument.close()
        

    def get_set_temp(self):
        """Gets or sets the source type of the Keithley 2400 SourceMeter.

        Expected strings for setting: 'voltage', 'current'"""
#         self.instrument.lock_excl()
#         self.cls_ppms()
        response = self.query("TEMP?").strip()[:-1].split(',')
        if len(response[-1]) == 0:
            response[-1] = '0'
#         self.cls_ppms()
        #self.instrument.close()
        # print(response)
        response = [float(entry) for entry in response]
        response_name = ['SetTemp','TempRate','TempApproachMode']
        return response, [self._name+':'+name for name in response_name]

    def set_temp(self, *value):
        """
        :param value: TEMP RATE APPROACHCODE
        approachcode: 0: Fast settle approach; 1: No overshoot approach; 
        """
#         self.instrument.lock_excl()
#         self.cls_ppms()
        str_values = [str(single_value) for single_value in value]
        self.query("TEMP "+' '.join(str_values))
#         self.cls_ppms()
        #self.instrument.close()

    def get_data(self,code=6,mode=0):
#         self.instrument.lock_excl()
#         self.cls_ppms()
        response = self.query(("GetDat? "+str(code))).strip()[:-1].split(',')
        # #self.instrument
#         self.cls_ppms()
        # print(response)
        # print(response)
        response = [float(entry) for entry in response]
        bincode = bin(code)[2:]
        name_list = ['pm:Deci Code','pm:Timestamp',]
        for i,dig in enumerate(bincode[::-1]):
            if dig == '1':
                name_list.append(self._name+":"+self.channelNames[i])
        assert len(response) == len(name_list), "%s reading interrupted"%self._name
        for i in range(len(response)):
            if 'T_pm' not in name_list:
                continue
#             if response[i]<0.3 or response[i] > 400:
            assert response[i]<400 and response[i] > 0.3, "%s reading interrupted"%self._name
        return response, name_list
    def partial_get_data(self):
        return self.get_data(*self.read_code)
    def identify(self):
        """Returns manufacturer, model number, serial number, and firmware revision levels."""
#         self.instrument.write('*CLS\r')
        response = self.query('*IDN?')
#         time.sleep(1)
#         response = self.instrument.read()
        return response


    # Resistance sensing

    @property
    def resistance_ohms_mode(self):
        """Gets or sets the resistance mode.

        Expected strings for setting: 'manual', 'auto'"""
        modes = {'MAN': 'manual', 'AUTO': 'auto'}
        response = self.instrument.query('sense:resistance:mode?').strip()
        return modes[response]

    @resistance_ohms_mode.setter
    def resistance_ohms_mode(self, value):
        modes = {'manual': 'MAN', 'auto': 'AUTO'}
        if value.lower() in modes.keys():
            self.instrument.write('sense:resistance:mode {}'.format(modes[value.lower()]))
        else:
            raise RuntimeError('Expected a value from [\'manual\'|\'auto\']')

    @property
    def expected_ohms_reading(self):
        """Gets or sets the expected range of a resistance reading from the device under test."""
        response = self.instrument.query('sense:resistance:range?').strip()
        return float(response)

    @expected_ohms_reading.setter
    def expected_ohms_reading(self, value):
        if isinstance(value, int) or isinstance(value, float):
            self.instrument.write('sense:resistance:range {}'.format(value))
        else:
            raise RuntimeError('Expected an int or float.')

    @property
    def four_wire_sensing(self):
        """Gets the status of or sets four-wire sensing.

        Expected booleans for setting: True, False."""
        response = self.instrument.query('system:rsense?').strip()
        return bool(int(response))

    @four_wire_sensing.setter
    def four_wire_sensing(self, value):
        if isinstance(value, bool):
            self.instrument.write('system:rsense {}'.format(int(value)))
        else:
            raise RuntimeError('Expected boolean value.')

    # Voltage sensing and compliance

    @property
    def expected_voltage_reading(self):
        """Gets or sets the expected voltage reading from the device under test."""
        response = self.instrument.query('sense:voltage:RANGE?').strip()
        return float(response)

    @expected_voltage_reading.setter
    def expected_voltage_reading(self, value):
        if isinstance(value, int) or isinstance(value, float):
            self.instrument.write('sense:voltage:range {}'.format(value))
        else:
            raise RuntimeError('Expected an int or float.')

    @property
    def voltage_compliance(self):
        """Gets or sets the voltage compliance.

        Expected range of floats: 200e-6 <= x <= 210"""
        response = self.instrument.query("SENS:VOLT:PROT:LEV?").strip()
        return float(response)

    @voltage_compliance.setter
    def voltage_compliance(self, value):
        if 200e-6 <= value <= 210:
            self.instrument.write("SENS:VOLT:PROT {}".format(str(value)))
        else:
            raise RuntimeError('Voltage compliance cannot be set. Value must be between 200 \u03BC' + 'V and 210 V.')

    def within_voltage_compliance(self):
        """Queries if the measured voltage is within the set compliance.

        :returns: boolean"""
        response = self.instrument.query('SENS:VOLT:PROT:TRIP?').strip()
        return not bool(int(response))

    # Current sensing and compilance

    @property
    def expected_current_reading(self):
        """Gets or sets the expected current reading from the device under test."""
        response = self.instrument.query('sense:current:range?').strip()
        return float(response)

    @expected_current_reading.setter
    def expected_current_reading(self, value):
        if isinstance(value, int) or isinstance(value, float):
            self.instrument.write('sense:current:range {}'.format(value))
        else:
            RuntimeError('Expected an int or float.')

    @property
    def current_compliance(self):
        """Sets or gets the current compliance level in Amperes."""
        response = self.instrument.query("SENS:CURR:PROT:LEV?").strip()
        return float(response)

    @current_compliance.setter
    def current_compliance(self, value):
        if 1e-9 <= value <= 1.05:
            self.instrument.write("SENS:CURR:PROT {}".format(str(value)))
        else:
            raise RuntimeError('Current compliance cannot be set. Value must be between 1 nA and 1.05 A.')

    def within_current_compliance(self):
        """Queries if the measured current is within the set compliance.

        :returns: boolean"""
        response = self.instrument.query('SENS:CURR:PROT:TRIP?').strip()
        return not bool(int(response))

    # Output configuration

    @property
    def output(self):
        """Gets or sets the source output of the Keithley 2400.

        Expected input: boolean

        :returns: boolean"""
        output = {'0': False, '1': True}
        response = self.instrument.query("OUTP?").strip()
        return output[response]

    @output.setter
    def output(self, value):
        if value:
            self.instrument.write("OUTP ON")
        else:
            self.instrument.write("OUTP OFF")

    @property
    def output_off_mode(self):
        """Gets or sets the output mode when the output is off.

        Expected input strings: 'himp', 'normal', 'zero', 'guard'

        :returns: description of the output's off mode"""
        modes = {'HIMP': 'high impedance', 'NORM': 'normal', 'ZERO': 'zero', 'GUAR': 'guard'}
        response = self.instrument.query('OUTP:SMOD?').strip()
        return modes[response]

    @output_off_mode.setter
    def output_off_mode(self, value):
        modes = {'high impedance': 'HIMP', 'himp': 'HIMP', 'normal': 'NORM', 'norm': 'NORM',
                 'zero': 'ZERO', '0': 'ZERO', 'guard': 'GUARD'}
        self.instrument.write('OUTP:SMOD {}'.format(modes[value.lower()]))

    # Data acquisition

    def read(self, *measurements):
        """
        
        Reads data from the Keithley 2400. Equivalent to the command :INIT; :FETCH?

        Multiple string arguments may be used. For example::
            
            keithley.read('voltage', 'current')
            keithley.read('time')

        The first line returns a list in the form [voltage, current] and the second line
        returns a list in the form [time].

        Note: The returned lists contains the values in the order that you requested.

        :param str *measurements: Any number of arguments that are from: 'voltage', 'current', 'resistance', 'time'
        :return list measure_list: A list of the arithmetic means in the order of the given arguments
        :return list measure_stdev_list: A list of the standard deviations (if more than 1 measurement) in the order
            of the given arguments
        """
        response = self.instrument.query('read?').strip().split(',')
        response = [float(x) for x in response]

        return response

    # Trigger functions

    @property
    def trace_delay(self):
        """The amount of time the SourceMeter waits after the trigger to perform Device Action."""
        return float(self.instrument.query('trigger:delay?').strip())

    @trace_delay.setter
    def trace_delay(self, delay):
        if isinstance(delay, float) or isinstance(delay, int):
            if 0.0 <= delay <= 999.9999:
                self.instrument.write('trigger:delay {}'.format(delay))
            else:
                raise RuntimeError('Expected delay to be between 0.0 and 999.9999 seconds.')
        else:
            raise RuntimeError('Expected delay to be an int or float.')

    @property
    def trigger(self):
        """Gets or sets the type of trigger to be used.

        Expected strings for setting: 'immediate', 'tlink', 'timer', 'manual', 'bus',
        'nst', 'pst', 'bst' (see source code for other possibilities)"""
        triggers = {'IMM': 'immediate',         'TLIN': 'trigger link',         'TIM': 'timer',
                    'MAN': 'manual',            'BUS': 'bus trigger',           'NST': 'low SOT pulse',
                    'PST': 'high SOT pulse',    'BST': 'high or low SOT pulse'}
        return triggers[self.instrument.query('trigger:source?')]

    @trigger.setter
    def trigger(self, trigger):
        triggers = {
            'imm': 'IMM', 'immediate': 'IMM',
            'tlin': 'TLIN', 'tlink': 'TLIN', 'trigger link': 'TLIN',
            'tim': 'TIM', 'timer': 'TIM',
            'man': 'MAN', 'manual': 'MAN',
            'bus': 'BUS', 'bus trigger': 'BUS',
            'nst': 'NST', 'low SOT pulse': 'NST',
            'pst': 'PST', 'high SOT pulse': 'PST',
            'bst': 'BST', 'high or low SOT pulse': 'BST'
        }
        if trigger.lower() in triggers.keys():
            self.instrument.query('trigger:source {}'.format(trigger))
        else:
            raise RuntimeError('Unexpected trigger input. See documentation for details.')

    @property
    def trigger_count(self):
        """Gets or sets the number of triggers

        Expected integer value range: 1 <= n <= 2500"""
        return float(self.instrument.query('trigger:count?').strip())

    @trigger_count.setter
    def trigger_count(self, num_triggers):
        if isinstance(num_triggers, int):
            if 1 <= num_triggers <= 2500:
                self.instrument.write('trigger:count {}'.format(num_triggers))
            else:
                raise RuntimeError('Trigger count expected to be between 1 and 2500.')
        else:
            raise RuntimeError('Trigger count expected to be type int.')

    def initiate_cycle(self):
        """Initiates source or measure cycle, taking the SourceMeter out of an idle state."""
        self.instrument.write('initiate')

    def abort_cycle(self):
        """Aborts the source or measure cycle, bringing the SourceMeter back into an idle state."""
        self.instrument.write('abort')

    # Data storage / Buffer functions

    # Note: :trace:data? and :read? are two separate buffers of
    # maximum size 2500 readings.
    
    @property
    def num_readings_in_buffer(self):
        """Gets the number of readings that are stored in the buffer."""
        return int(self.instrument.query('trace:points:actual?').strip())

    @property
    def trace_points(self):
        """Gets or sets the size of the buffer
        
        Expected integer value range: 1 <= n <= 2500"""
        return int(self.instrument.query('trace:points?').strip())

    @trace_points.setter
    def trace_points(self, num_points):
        if isinstance(num_points, int):
            if 1 <= num_points <= 2500:
                self.instrument.write('trace:points {}'.format(num_points))
            else:
                raise RuntimeError('Keithley 2400 SourceMeter may only have 1 to 2500 buffer points.')
        else:
            raise RuntimeError('Expected type of num_points: int.')

    def trace_feed_source(self, value):
        """Sets the source of the trace feed.

        Expected strings: 'sense', 'calculate1', 'calculate2'"""
        if value in ('sense', 'calculate1', 'calculate2'):
            self.instrument.write('trace:feed {}'.format(value))
        else:
            raise RuntimeError('Unexpected trace source type. See documentation for details.')

    def read_trace(self):
        """Read contents of buffer."""
        trace = self.instrument.query('trace:data?').strip().split(',')
        trace_list = [float(x) for x in trace]
        return trace_list

    def clear_trace(self):
        """Clear the buffer."""
        self.instrument.query('trace:clear')

    def buffer_memory_status(self):
        """Check buffer memory status."""
        response = self.instrument.query('trace:free?')
        return response

    def fill_buffer(self):
        """Fill buffer and stop."""
        self.instrument.write('trace:feed:control next')

    def disable_buffer(self):
        """Disables the buffer."""
        self.instrument.write('trace:feed:control never')

    # Sweeping

    # TODO: implement these!!!

    @property
    def sweep_start(self):
        """To be implemented."""
        pass

    @sweep_start.setter
    def sweep_start(self, start):
        pass

    @property
    def sweep_end(self):
        """To be implemented."""
        pass

    @sweep_end.setter
    def sweep_end(self, end):
        pass

    @property
    def sweep_center(self):
        """To be implemented."""
        pass

    @sweep_center.setter
    def sweep_center(self, center):
        pass

    @property
    def sweep_span(self):
        """To be implemented."""
        pass

    @sweep_span.setter
    def sweep_span(self, span):
        pass

    @property
    def sweep_ranging(self):
        """To be implemented."""
        pass

    @sweep_ranging.setter
    def sweep_ranging(self, _range):
        pass

    @property
    def sweep_scale(self):
        """To be implemented."""
        pass

    @sweep_scale.setter
    def sweep_scale(self, scale):
        pass

    @property
    def sweep_points(self):
        """To be implemented."""
        pass

    @sweep_points.setter
    def sweep_points(self, num_points):
        pass

    @property
    def sweep_direction(self):
        """To be implemented."""
        pass

    @sweep_direction.setter
    def sweep_direction(self, direction):
        pass

    # Ramping commands

    def ramp_to_zero(self):
        pass

    def ramp_to_setpoint(self, setpoint: float, step: float, wait: float):
        pass

    # Common commands

    def clear_status(self):
        """Clears all event registers and Error Queue."""
        self.instrument.write('*cls')

    def reset_to_defaults(self):
        """Resets to defaults of Sourcemeter."""
        self.instrument.write('*rst')

    def send_bus_trigger(self):
        """Sends a bus trigger to SourceMeter."""
        self.instrument.write('*trg')
