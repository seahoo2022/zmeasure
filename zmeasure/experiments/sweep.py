import time
import numpy as np
from ..utility import error_response,wait_until, get_highest_indx,get_highest_indx_file
def shift_none_right(seq):
    """Shift None one position to the right to preserve logical split markers."""
    seq = list(seq)
    for i in reversed(range(len(seq) - 1)):
        if seq[i] is None and seq[i + 1] is not None:
            seq[i], seq[i + 1] = seq[i + 1], None
    return seq


def partition_sequence(seq):
    """
    Given a sequence with None as split points, return:
    - list of partitions (list of lists)
    - list of (start, end) tuples from each partition
    """
    partitions = []
    block = []
    for x in seq:
        if x is None:
            if block:
                partitions.append(block)
                block = []
        else:
            block.append(x)
    if block:
        partitions.append(block)

    start_end = [(b[0], b[-1]) for b in partitions if b]
    return partitions, start_end

class Sweeper:
    def __init__(
        self,
        label="",
        read_csv_func=None,
        pause_func=None,
        resume_func=None,
        stop_func=None,
        switch_file_func=None,
        get_latest_file_func=None,
        data_folder=None,
        wait_until_func=wait_until,
        delay_resume=10,
        wait_first=1200,
        wait_rest=600,
        sweep_func=None,
        get_current_func=None,
        safe_rate = None,
    ):
        self.label = label
        self.read_csv_func = read_csv_func
        self.switch_file_func = switch_file_func
        self.pause_func = pause_func
        self.resume_func = resume_func
        self.stop_func = stop_func
        self.wait_until = wait_until_func
        self.get_latest_file = get_latest_file_func
        self.data_folder = data_folder
        self.delay_resume = delay_resume
        self.wait_first = wait_first
        self.wait_rest = wait_rest
        self.sweep_func = sweep_func
        self.get_current_func = get_current_func
        self.safe_rate = safe_rate
    def instrument_safe_call(self, func, *args, **kwargs):
        """Safely call an instrument command with pause and resume around error_response."""
        if self.pause_func is not None:
            self.pause_func()
            time.sleep(0.5)
        try:
            return error_response(func, *args, **kwargs)
        finally:
            time.sleep(0.5)
            if self.resume_func is not None:
                self.resume_func()
        
        
    def run_single_sweep(
        self,
        
        sweep_values,
        sweep_rates,
        entry_names,
        entry_tolerances,
    ):
        flag = True
        parts = 0
        partitions, start_end = partition_sequence(sweep_values)
        for i, target in enumerate(sweep_values):

            current_val = self.instrument_safe_call(self.get_current_func)
            print(current_val)
            if isinstance(target, type(None)) or np.isnan(target):
                flag = True
                continue
            if flag:
                print('switch file')
                self.instrument_safe_call(self.switch_file_func,f"{self.label}_from_{current_val}_to_{start_end[parts][1]}")
                parts += 1
                print('switch file done')
                flag = False
            

            comp_code = '<' if current_val > target else '>'
            temp_sign = 1 if comp_code == '<' else -1

            self.instrument_safe_call(self.sweep_func,target, sweep_rates[i])

            time.sleep(self.delay_resume)

            if len(entry_names) == 0:
                continue

            comp_codes = [comp_code]+['<']*(len(entry_names)-1)
            result = self.wait_until(
                self.read_csv_func,
                entry_names=entry_names,
                comp_codes=comp_codes,
                set_values=[target+temp_sign*entry_tolerances[0]]+entry_tolerances[1:],
                stablizes=[False]+[True]*(len(entry_names)-1),
            )

            time.sleep(self.wait_first if i == 0 else self.wait_rest)

        return

class DoubleSweeper(Sweeper):
    def __init__(self, outer_sweeper, inner_sweeper):
        super().__init__()
        
        self.outer_sweeper = outer_sweeper
        self.inner_sweeper = inner_sweeper
        self.outer_label = outer_sweeper.label
        self.inner_label = inner_sweeper.label
        self.outer_sweep_func = outer_sweeper.sweep_func
        self.inner_sweep_func = inner_sweeper.sweep_func
        self.outer_get_current_func = outer_sweeper.get_current_func
        self.inner_get_current_func = inner_sweeper.get_current_func
        
        
    def run_double_sweep(
        self,
       
        outer_sweep_values,
        outer_sweep_rates,
        outer_entry_names,
        outer_entry_tolerances,
        
        inner_sweep_values,
        inner_sweep_rates,
        inner_entry_names,
        inner_entry_tolerances,
        sweep_back = False,
        # outer_label="outer",
        # inner_label="inner"
    ):
        
        if sweep_back:
            outer_sweep_values = np.concatenate((outer_sweep_values,[outer_sweep_values[0]]))
            inner_sweep_values = np.concatenate((inner_sweep_values,inner_sweep_values[-2::-1]))
            outer_sweep_rates = np.concatenate((outer_sweep_rates,[outer_sweep_rates[0]]))
            inner_sweep_rates = np.concatenate((inner_sweep_rates,inner_sweep_rates[-2::-1]))
        outer_label = self.outer_sweeper.label
        inner_label = self.inner_sweeper.label
        for outer_val in outer_sweep_values:
            # Update label for file naming
            self.outer_sweeper.label = f"{outer_label}"

            # Sweep outer (single value)
            self.outer_sweeper.run_single_sweep(
                sweep_values=[outer_val],
                sweep_rates=outer_sweep_rates,
                entry_names=outer_entry_names,
                entry_tolerances=outer_entry_tolerances,
            )

            time.sleep(1)

            # Sweep inner (full list)
            self.inner_sweeper.label = f"{outer_label}_{outer_val}__{inner_label}"
            self.inner_sweeper.run_single_sweep(
                sweep_values=inner_sweep_values,
                sweep_rates=inner_sweep_rates,
                entry_names=inner_entry_names,
                entry_tolerances=inner_entry_tolerances,
            )