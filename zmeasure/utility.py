import time
import os
import datetime
import numpy as np
from matplotlib.ticker import MaxNLocator, Locator, AutoLocator, FuncFormatter
import random
from functools import partial
import pickle
# utilities
#np.interp()
import time
import pandas as pd
# from PID import PID  # Install via 'pip install simple-pid'
# def mkdir(*args):
#     dirs = os.path.join('',*args)
#     if not os.path.exists(dirs):
#         os.makedirs(dirs)
#     return dirs

def mkdir(*args):
    print(args)
    dirs = os.path.join('',*args)
    if not os.path.exists(dirs):
        os.makedirs(dirs)
        print(f'{dirs} created')
    else:
        print(f'{dirs} already exists')
    
    if 'data' in args:
        if not os.path.exists(os.path.join(dirs,'000-description.txt')):
            with open(os.path.join(dirs,'000-description.txt'),'w') as f:
                f.write(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {args} created') #write the time the folder was created
        else:
            print(f'{dirs} already exists, description file already exists')
    return dirs
def reset_all(instruList):
    for instru in instruList:
        instru.reset()
    return 
def wait_until(read_csv_func,entry_names,comp_codes,set_values,
               pool_num=5,timeout=50000,stablizes=None,step_time=2):
    t0 = time.time()
    t1 = t0
    flags = [True]*len(entry_names)
    if stablizes == None:
        stablizes = [True]*len(entry_names)
    while t1-t0<timeout and any(flags):
        df = read_csv_func()
        stat_df = df.loc[len(df)-pool_num:]
        avg = stat_df.mean()
        std = stat_df.std()
        
        
        for k in range(len(entry_names)):
            
            if not flags[k]:
                continue
            stablize = stablizes[k]
            comp_code = comp_codes[k]
            set_value = set_values[k]
            entry_name = entry_names[k]
            if stablize:
                to_compare = std[entry_name]
                comp_code = '<'
            else:
                to_compare = avg[entry_name]
                
            if comp_code == '<' and to_compare < set_value:
                flags[k] = False
            elif comp_code == '<=' and to_compare <= set_value:
                flags[k] = False
            elif comp_code == '>' and to_compare > set_value:
                flags[k] = False
            elif comp_code == '>=' and to_compare >= set_value:
                flags[k] = False
        time.sleep(step_time)
        t1 = time.time()
    if any(flags) == False:
        return avg

def seconds_to_hms(x,pos):
    h = int(x//3600)
    m = int((x % 3600)//60)
    s = int(x%60)
    return f"{h:02d}:{m:02d}:{s:02d}"
def now():
    return '{date:%Y-%m-%d_%H-%M-%S}'.format(date=datetime.datetime.now())


def read_all(funcs_to_call):
        all_data = []
        all_data_name = []
        for i in range(len(funcs_to_call)):
            t1 = time.time()
            data,name = error_response(funcs_to_call[i])
            time.sleep(0.02)
            # print(i,time.time()-t1)
            # print(i,name,data,{key:value for key,value in zip(name,data)})
            all_data += data
            all_data_name += name
        return np.array(all_data), np.array(all_data_name)
# def read_all(funcs_to_call):
#     all_data = []
#     all_data_name = []
#     for i in range(len(funcs_to_call)):
#         #t001 = time.time()
#         data,name = funcs_to_call[i]()
#         #t002 = time.time()
#         #print(i,name,t002-t001)
#         time.sleep(0.05)
        
#         all_data += data
#         all_data_name += name
#     return np.array(all_data), np.array(all_data_name)
def cls_all(funcs_to_call):
    for i in range(len(funcs_to_call)):
        try:
            dataName = funcs_to_call[i]()
            time.sleep(0.5)
        except Exception as e:
            print(i,'cls error',e)
            pass
    return
def pick_data_indx(all_data_name, read_col_names):
    indx = []
    for i in range(len(read_col_names)):
#             print(read_col_names[i])
        indx.append(np.where(all_data_name == read_col_names[i])[0][0])
    return indx

def error_response(func,*args,**kwargs):
    k = 0
    max_error = kwargs.get('max_error',10)
    cls_func = kwargs.get('cls_func',False)
    func_kwargs = kwargs.get('func_kwargs',dict())
    while k<max_error:
        try:
            response = func(*args,**func_kwargs)
        except Exception as e:
            k+=1
            print('%dth trial failed'%k, e)
            
            if cls_func != False:
                cls_func()
            continue
        else:
            return response
def get_d(Cd):
    return 48.46/(Cd-0.0479)-46.24
def get_disp(Cd,Cd0):
    return get_d(Cd)-get_d(Cd0)
def get_current_disp(func,Cd0):
    Cd = func()[0][0]
    return get_disp(Cd,Cd0)
def get_current_strain(func,Cd0,L):
    Cd = func()[0][0]
    return get_disp(Cd,Cd0)/L

def get_cernox_temp(file='cernox_250212.pickle'):
    with open(file,'rb') as f:
        revintp = pickle.load(f)
    def T_cernox(R):
        return np.exp(revintp(np.log(R)))
    return T_cernox
        
class AdaptiveCleanTickLocator(Locator):
    def __init__(self, span, base_intervals=None):
        """
        Custom tick locator that places ticks at clean fractional values.
        `base_intervals`: list of preferred tick step sizes (e.g., 0.1, 0.25, 0.5).
        """
        # Default base intervals if not provided: 0.25, 0.5, 1
        self.base_intervals = [1, 0.5, 0.25]
        self.span = span
        
    def __call__(self):
        """Return tick locations based on axis limits."""
#         span = self.span
        vmin,vmax = self.span
        span = vmax-vmin
        if span == 0:
            return [vmax]
        # Determine the tick step based on the data span
        
        step_size = self._get_tick_step(span)
#         print(vmax,span,step_size)
        # Start from the nearest clean tick below vmin
        ticks = []
        current_tick = np.floor(vmin / step_size) * step_size
        while current_tick < vmax:
            ticks.append(current_tick)
            current_tick += step_size
        ticks.append(current_tick)
#         print(ticks)
        return ticks
    
    def _get_tick_step(self, span):
        """Determine the appropriate step size based on the span of the axis."""
        magnitude = 10 ** np.floor(np.log10(span))  # Order of magnitude of the span
        for i in range(1):
            for base in self.base_intervals:
                step_size = base * magnitude*10**i
                if span / step_size <= 10:  # Choose a step size that gives a reasonable number of ticks
                    return step_size
#         print('oh shit',span)
        return magnitude  # Fallback to a simple magnitude step
def scientific_formatter(val,pos=6):
    # print(val)
    if val == None or val == np.nan:
        return None
    formatted=f'{val:.6e}'
    try:
        c,e=formatted.split('e')
    except:
        print('Value None Error')
        return None
    if abs(int(e)) < 3:
        return f'{val:.6f}'.rstrip('0').rstrip('.')
    c = c.rstrip('0').rstrip('.')
    return f"{c}e{int(e)}"


def get_highest_indx(folderpath):
    files = os.listdir(folderpath)
    idx = [0]
    for i in range(len(files)):
        try:
            im = int(files[i][:3])
            idx.append(im)
        except:
            pass
    return max(idx)

def get_highest_indx_file(folderpath):
    files = os.listdir(folderpath)
    idx = [0]
    idfiles = []
    for i in range(len(files)):
        try:
            im = int(files[i][:3])
            idx.append(im)
            idfiles.append(files[i].split('/')[-1][:-4])
        except:
            pass
    stidx,stfile = [list(t) for t in zip(*sorted(zip(idx[1:],idfiles)))]
    return stidx[-1],stfile[-1],'--'.join(stfile[-1].split('--')[1:])

class simulated_instru:
    def __init__(self) -> None:
        self.channel = 5
    def read(self,i):
        return [i+random.random(),i+random.random()],['sim:X','sim:Y']
    
    def partial_read(self,):
        return self.read(self.channel)
    
def elapsed_time(start_time):
    return [time.time()-start_time], ['sys:time']
def real_time():
    return [time.time()], ['sys:real_time']