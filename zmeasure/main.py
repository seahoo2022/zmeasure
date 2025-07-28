# main_controller.py
import multiprocessing as mp
from .reader import reading_process
from .plotter import plotting_process
from .analyzer import analysing_process
def start_process(**configs):
    # Shared IPC objects
    global stop_event, pause_event, file_queue, clear_queue, data_queue, read_worker, plotter_worker, analysis_worker, analysis_queue, PID_ret_queue, PID_para_queue
    stop_event = mp.Event()
    pause_event = mp.Event()
    file_queue = mp.Queue()
    clear_queue = mp.Queue()
    data_queue = mp.Queue(maxsize=10)  # buffered updates to plot
    analysis_queue = mp.Queue(maxsize=10)
    PID_para_queue = mp.Queue(maxsize=10)
    PID_ret_queue = mp.Queue(maxsize=10)
    # Two separate subprocesses
    read_worker = mp.Process(target=reading_process,
                        args=(stop_event, pause_event, file_queue, clear_queue, data_queue, analysis_queue,PID_ret_queue,  configs))
    plotter_worker = mp.Process(target=plotting_process,
                         args=(stop_event, clear_queue, data_queue, configs))
    analysis_worker =  mp.Process(target=analysing_process,
                        args=(stop_event, analysis_queue, PID_para_queue, PID_ret_queue, configs))
    
    read_worker.start()
    plotter_worker.start()
    analysis_worker.start()
    
def stop_process():
    global stop_event, read_worker, plotter_worker, analysis_worker
    stop_event.set()
    read_worker.join()  # Wait for the process to finish
    plotter_worker.join()
    analysis_worker.join()

def pause_process():
    global pause_event
    pause_event.set()

def resume_process():
    global pause_event
    pause_event.clear()

def switch_file(new_filename):
    global file_queue
    file_queue.put(new_filename)
    
def update_PID(paras):
    global PID_para_queue
    PID_para_queue.put(paras)
    
def clear_plot(i='all'):
    global clear_queue
    clear_queue.put(i)