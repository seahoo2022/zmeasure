from statistics import mean, stdev
import pyvisa as visa
from driver import Driver

class Rp100(Driver):

    def __init__(self, serial_port=3,name='Rp100'):
        """
        Constructor for RP100 Sourcemeter
        1 to single tension
        2 to double compression
        """
        super().__init__()
        self.serial_port = str(serial_port)
#         self._resource_manager = visa.ResourceManager()
#         self.instrument = self._resource_manager.open_resource("ASRL3::{}".format(self.serial_port))
        self._name = name
        self.upper_slew = 100
        self.upper_volt = 200
        self.lower_volt = -200
        
    def boundary_volt(self,T):
        if T> 250:
            lm = [-20,120]
        elif 100<T<=250:
            lm = [-20+(T-250)*180/250,120]
        else:
            lm = [-20+(T-250)*180/250,120+80/100*(100-T)]
        return [max(self.lower_volt,lm[0]),min(self.upper_volt,lm[1])]


    @property
    def instrument(self):
        # if self._instrument == None:
        # self._instrument = self.resource_manager.open_resource("ASRL{}".format(self.serial_port))
            # self.instrument.read_termination = '\n'
        return self.resource_manager.open_resource("ASRL{}".format(self.serial_port))
    
    # source functions
    def get_rate(self):
        response = float(self.instrument.query('SOUR:' + 'VOLT' + ':SLEW?').strip())
        if abs(response) > self.upper_slew:
            print('Beyond Upper Boundary or Scanning Rate |%.2f| > %.2f'%(response,self.upper_slew))
            self.instrument.write('SOUR:' + 'VOLT' + ':SLEW %.2f'%self.upper_slew)
            response = self.upper_slew
        return response
    
    def filter_volt(self,voltage,T=None):
        if T == None:
            limit = [self.lower_volt,self.upper_volt]
        else:
            limit = self.boundary_volt(T)
        if not limit[0]<=voltage<=limit[1]:
            return False
        return True
    
    def source_value(self):
        """Get or set the numeric value of the source chosen from Keithley2400.source_type."""
        response1 = self.instrument.query('SOUR1:' + 'VOLT' + ':NOW?').strip()
        response2 = self.instrument.query('SOUR2:' + 'VOLT' + ':NOW?').strip()
        return [float(response1),float(response2)], [self._name+':'+'setVolt1_now',self._name+':'+'setVolt2_now']
    
    def get_set_source_value(self):
        """Get or set the numeric value of the source chosen from Keithley2400.source_type."""
        response1 = self.instrument.query('SOUR1:' + 'VOLT' + '?').strip()
        response2 = self.instrument.query('SOUR2:' + 'VOLT' + '?').strip()
        try:
            response1 = float(response1)
            response2 = float(response2)
        except ValueError as e:
            raise e
        return [response1,response2], [self._name+':'+'setVolt1',self._name+':'+'setVolt2']
    def get_meas_source_value(self):
        """Get or set the numeric value of the source chosen from Keithley2400.source_type."""
        response1 = self.instrument.query('MEAS1:' + 'VOLT' + '?').strip()
        response2 = self.instrument.query('MEAS2:' + 'VOLT' + '?').strip()
        return [float(response1),float(response2)], [self._name+':'+'measVolt1',self._name+':'+'measVolt2']
    def set_source_value(self, *value,T=None):
        flag = self.filter_volt(value[0],T) and self.filter_volt(value[1],T)
        if flag:
            print('bingo!')
#             prin
            self.instrument.write("SOUR1:VOLT %.2f"%value[0])
            self.instrument.write("SOUR2:VOLT %.2f"%value[1])
        else:
            print('Voltage Beyond Boundary: Check your voltage setup')
        return flag
    # Output configuration

    def get_output(self):
        """Gets or sets the source output of the Keithley 6221.

        Expected input: boolean

        :returns: boolean"""
        output = {'0': 0, '1': 1}
        response1 = self.instrument.query("OUTP1?").strip()
        response2 = self.instrument.query("OUTP2?").strip()
        
        return [output[response1],output[response2]],[self._name+':'+'Output1',self._name+':'+'Output2']

    def set_output(self, *value):
        if value[0]:
            self.instrument.write("OUTP1 1")
        else:
            self.instrument.write("OUTP1 0")
        if value[1]:
            self.instrument.write("OUTP2 1")
        else:
            self.instrument.write("OUTP2 0")
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
        read_types = {'voltage': 0, 'current': 1, 'resistance': 2, 'time': 3}

        measure_list = []
        measure_stdev_list = []

        for measurement in measurements:
            samples = response[read_types[measurement]::5]
            measure_list.append(mean(samples))
            if len(samples) > 1:
                measure_stdev_list.append(stdev(samples))

        return measure_list, measure_stdev_list

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

    def identify(self):
        """Returns manufacturer, model number, serial number, and firmware revision levels."""
        response = self.instrument.query('*idn?')
        return {'manufacturer': response[0],
                'model': response[1],
                'serial number': response[2],
                'firmware revision level': response[3]
                }

    def send_bus_trigger(self):
        """Sends a bus trigger to SourceMeter."""
        self.instrument.write('*trg')
