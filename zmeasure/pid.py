import numpy as np
def _clamp(value, limits):
    lower, upper = limits
    if value is None:
        return None
    if isinstance(value, np.ndarray) or isinstance(value, list) or isinstance(value, tuple):
        # print('here')
        return np.array([_clamp(s_value, limits) for s_value in value])
    if (upper is not None) and (value > upper) :
        return upper
    elif (lower is not None) and (value < lower):
        return lower
    return value
def _clamp_out(value, limits):
    lower, upper = limits
    if value is None:
        return None
    if isinstance(value, np.ndarray) or isinstance(value, list) or isinstance(value, tuple):
        # print('here')
        return np.array([_clamp_out(s_value, limits) for s_value in value])
    if (upper is not None) and (value < upper) and value> 0:
        return upper
    elif (lower is not None) and (value > lower) and value< 0:
        return lower
    return value
import time

def boundary_volt(T):
        if T> 250:
            lm = [-20,120]
        elif 100<T<=250:
            lm = [-20+(T-250)*180/250,120]
        else:
            lm = [-20+(T-250)*180/250,120+80/100*(100-T)]
        return lm

class PID_base:
    def __init__(self, init_value, keys, kp=1.0, ki=0.0, kd=0.0):
        """
        Parameters:
        - init_value: initial setpoint
        - target_key: the key in the incoming data dict used for PID control
        - kp, ki, kd: PID gains
        """
        self.target = init_value
        self.keys = keys
        self.current_keys = keys[0][0]
        self.output_keys = keys[1][0]
        
        # PID gains
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        # Error terms
        self.integral = 0.0
        self.previous_error = None
        self.previous_time = None
        self.output_limits = None
        # For output
        self.output = None
        self.max_rate = 0.01
        self.max_stepsize = 0.05
        
    def update_params(self, kwargs):
        new_target=kwargs.get('new_target', None)
        new_limits=kwargs.get('new_limits', None)
        new_max_rate=kwargs.get('new_max_rate', None)
        new_max_stepsize=kwargs.get('new_max_stepsize', None)
        
        if new_target is not None:
            self.target = new_target
            self.integral = 0.0
            self.previous_error = None
            self.previous_time = None
        if new_target in {'stop','pause',False}:
            self.target = None
            self.integral = 0.0
            self.previous_error = None
            self.previous_time = None
        if new_limits is not None:
            self.output_limits = new_limits
        if new_max_rate is not None:
            self.max_rate = new_max_rate
        if new_max_stepsize is not None:
            self.max_stepsize = new_max_stepsize
    
    def PID_kernel(self, error,derivative):
        # PID output
        # print(error,self.integral,derivative)
        delta = (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )
        return delta

    
    def update_limits(self, data_point):
        # to be implemented
        return self.output_limits
    
    def update_status(self, data_point):
        """
        Update PID based on new data_point (a dict).
        Returns new control value.
        """
        output_limits = self.update_limits(data_point)
        current_time = time.time()
        current_value = data_point.get(self.current_keys[0])
        # print(current_value)
        current_stamp = data_point.get('sys:real_time')
        self.output = np.array([data_point.get(key) for key in self.output_keys])
        # print(self.output,'o')
        print('strain target',self.target)
        if current_value is None or self.target == None:
            # print('?')
            return None  # Fallback if data is missing
        
        error = self.target - current_value

        # Time delta
        if self.previous_time is None:
            dt = 0.0
        else:
            dt = current_time - self.previous_time
        # Integral term
        self.integral += error * dt

        # Derivative term
        if self.previous_error is None or dt == 0:
            derivative = 0.0
        else:
            derivative = (error - self.previous_error) / dt
            
        stepsize_limit = [-min(self.max_rate*dt, self.max_stepsize),min(self.max_rate*dt, self.max_stepsize)]
        raw_delta =self.PID_kernel(error, derivative)
        # print(raw_delta)
        delta = _clamp(raw_delta, stepsize_limit)
        delta = _clamp_out(delta, [-0.01,0.01])
        # print(delta)
        
        self.output =  _clamp(self.output+delta, output_limits)
        
        # Update state
        self.previous_error = error
        self.previous_time = current_time
        # print(self.output,self.output+delta, output_limits)
        # print(raw_delta, delta, self.output)
        if all(self.output==0):
            return None
        return (current_stamp, self.output)


class PID_strain(PID_base):
    def __init__(self, init_value, keys, kp=1.0, ki=0.0, kd=0.0, multiplier=[1,-0.5]):
        super().__init__(init_value, keys,kp,ki,kd)
        self.multiplier = np.array([1,-0.5])
        
    def PID_kernel(self, error,derivative):
        # PID output
        # print(error,self.integral,derivative)
        delta = np.array(
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )
        return delta * self.multiplier

    def update_params(self, kwargs):
        super().update_params(kwargs)
        new_multiplier=kwargs.get('new_multiplier', None)
        if new_multiplier is not None:
            self.multiplier = new_multiplier
        # print('this is new target',self.target)
    
    def update_limits(self, data_point):
        T = data_point['PPMS:T_pm']
        lm = boundary_volt(T)
        return _clamp(self.output_limits, lm)