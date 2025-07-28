# plotting_worker.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import AutoLocator, FuncFormatter
from .utility import AdaptiveCleanTickLocator,scientific_formatter, seconds_to_hms
import matplotlib
matplotlib.use("QtAgg")  # or 'TkAgg' depending on what's available
import matplotlib.pyplot as plt
from collections import deque
from .pid import PID_base, PID_strain
PIDs = {
    'strain': PID_strain
}
def analysing_process(stop_event, analysis_queue, PID_para_queue, PID_ret_queue, configs):

    PID_control_map = configs.get('PID_control_map',{})
    init_PID_value = configs.get('init_PID_value',{})
    PID_control_kwargs = configs.get('PID_control_kwargs',{key:{} for key in PID_control_map})
    PID_controllers = {}
    for key, value in PID_control_map.items():
        PID_controllers[key] = PIDs[key](init_PID_value[key], PID_control_map[key], **PID_control_kwargs[key])
        
    # data_buffer = deque(maxlen=5)
    while not stop_event.is_set():
        
        ret = {key: None for key in PID_control_map}
        if not PID_para_queue.empty():
            para = PID_para_queue.get()
            for key, PID_controller in PID_controllers.items():
                PID_controller.update_params(para[key])
        if not analysis_queue.empty():
            # print('analysis starts',analysis_queue)
            while not analysis_queue.empty():
                data_point = analysis_queue.get()
            # print('point fed',data_point)
            # data_buffer.append(data_point)
            # df_plot = pd.DataFrame(data_buffer)
            res = {}
            for key, PID_controller in PID_controllers.items():
                ret = PID_controller.update_status(data_point)
                res[key] = ret
            if not PID_ret_queue.full():
                PID_ret_queue.put(res)
        # time.sleep(1)
        