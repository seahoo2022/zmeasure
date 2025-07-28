# reading_worker.py
import time
import pandas as pd
import gc

def reading_process(stop_event, pause_event, file_queue, clear_queue, data_queue, analysis_queue,PID_ret_queue, configs):
    from functools import partial
    from matplotlib.ticker import AutoLocator, FuncFormatter
    from .read_write_tab import init_file
    from .utility import (get_highest_indx, elapsed_time, real_time,
                       pick_data_indx, error_response, read_all)

    max_plot_N = configs.get('max_plot_N', 10000)
    clear_funcs = configs.get('clear_funcs')
    datafolder = configs['data_folder']
    defaultFile = configs['default_file']
    readColNames = configs.get('read_col_names', None)
    plotAxesColNames = configs['plot_axes_col_names']
    start_time = configs.get('start_time', time.time())
    PID_control_map = configs.get('PID_control_map',{})
    previous_stamp = start_time
    # PID_size = configs.get('PID_size',10)
    
    read_funcs = [partial(elapsed_time, start_time), real_time] + configs['read_funcs']
    readColNames = ['sys:time', 'sys:real_time'] + readColNames

    idx = get_highest_indx(datafolder) + 1
    csvfile, csvwriter = init_file(defaultFile, readColNames, idx, datafolder)
    all_data, all_data_name = error_response(read_all,read_funcs)
    indx = pick_data_indx(all_data_name, readColNames)
    df_plot = pd.DataFrame(columns=readColNames)
    df_plot.loc[len(df_plot)] = [all_data[i] for i in indx]
    
    while not stop_event.is_set():
        if not file_queue.empty():
            idx = get_highest_indx(datafolder) + 1
            new_filename = file_queue.get()
            csvfile.close()
            csvfile, csvwriter = init_file(new_filename, readColNames, idx, datafolder)

        if not pause_event.is_set():
            
            all_data, all_data_name = error_response(read_all,read_funcs)
            
            data_to_save = [all_data[i] for i in indx]
            df_plot.loc[len(df_plot)] = data_to_save
            if len(df_plot) > max_plot_N:
                df_plot = df_plot.iloc[-max_plot_N:].copy()
            csvwriter.writerow(data_to_save)
            csvfile.flush()

            # Only send latest row to plot
            if not data_queue.full():
                data_queue.put(df_plot.iloc[-1].to_dict())
            if not analysis_queue.full():
                analysis_queue.put(df_plot.iloc[-1].to_dict())
            gc.collect()
            t0 = time.time()
            while not analysis_queue.empty() and time.time()-t0<=5:
                time.sleep(0.1)
                pass
            # if not analysis_queue.empty():
            #     continue
            if not PID_ret_queue.empty():
                while not PID_ret_queue.empty():
                    set_values = PID_ret_queue.get()
                    
                # print(set_values)
                new_stamp = False
                # previous_stamp = set_values[0]
                for key in PID_control_map:
                    if set_values[key] is None:
                        continue
                    if set_values[key][0] <= previous_stamp:
                        continue
                    # if [1] is None: 
                    #     continue
                    error_response(PID_control_map[key][1][1],*set_values[key][1])
                    new_stamp = set_values[key][0]
                if new_stamp:
                    previous_stamp =  new_stamp
    csvfile.close()
