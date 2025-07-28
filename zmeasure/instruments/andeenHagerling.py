from statistics import mean, stdev
import pyvisa as visa
import re
from ..driver import Driver
class AndeenHagerling(Driver):

    def __init__(self, gpib_addr=28,name='AH'):
        """
        Constructor for AndeenHagerling 2550A Sourcemeter

        :param gpib_addr: GPIB address (configured on AndeenHagerling 2550A)
        """
        super().__init__()
        self.gpib_addr = str(gpib_addr)
        self._name = name

    @property
    def instrument(self):
        if self._instrument == None:
            self._instrument = self.resource_manager.open_resource(f"GPIB{self.gpib_serial}::{self.gpib_addr}")
        return self._instrument


    # Data acquisition

    def trigger_and_read(self, *measurements):
        """
        
        Reads data from the AndeenHagerling 2550A. Equivalent to the command :INIT; :FETCH?

        Multiple string arguments may be used. For example::
            
            keithley.read('voltage', 'current')
            keithley.read('time')

        The first line returns a list in the form [voltage, current] and the second line
        returns a list in the form [time].

        Note: The returned lists contains the values in the order that you requested.
        """
        response = self.instrument.query('SI').strip()
#         print('response=',response)
        numbers = re.findall(r'\d+\.?\d*',response)
#         print(numbers)
        response = [float(x) for x in numbers]
        names = [self._name+':'+x for x in ['S', 'C_d','Loss_C','V']]
        assert len(response) == len(names), "%s reading interrupted"%self._name
        return response,names
