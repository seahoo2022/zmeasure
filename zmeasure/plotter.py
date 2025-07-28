# plotting_worker.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import AutoLocator, FuncFormatter
from .utility import AdaptiveCleanTickLocator,scientific_formatter, seconds_to_hms
import time
import matplotlib
matplotlib.use("QtAgg")  # or 'TkAgg' depending on what's available
import matplotlib.pyplot as plt
from collections import deque

import screeninfo  # install via pip if needed: pip install screeninfo

def fit_fig_left_third(fig):
    # Get primary screen resolution
    monitor = screeninfo.get_monitors()[0]
    screen_width = monitor.width
    screen_height = monitor.height

    # Set window size to 1/3 of screen width and full height
    fig_width = screen_width *3//7
    fig_height = screen_height *2//3

    # Apply window size and position
    mgr = fig.canvas.manager
    window = mgr.window
    window.resize(fig_width, fig_height)
    window.move(0, 0)  # position at top-left corner
    
formatter_date = FuncFormatter(seconds_to_hms)
colorseries = ['blue','orange','green','red','purple','brown','pink','gray','olive','cyan']
defaultAxeMapper = {
            'time':'$t$ (s)',
            'T_pm':'$T_{PPMS}$ (K)',
            'H_pm':'$H_{PPMS}$(Oe)',
            'temp_Insert':'$T_{Insert}$ (K)',
            'temp_rig':'$T_{Rig}$ (K)',
            'C_d':'$C_{d}$ (pF)',
            'C_f':'$C_{f}$ (pF)',
            'Vouter_Aux1':'$V_{outer}$ (V)',
            'Vinner_Aux2':'$V_{inner}$ (V)',
            'B_s(Oe)':'$B$ (Oe)',
            'MI':'$MI$ (H)',
            'force':'$F$ (N)',
            'strain':r'$\epsilon$',
            'pressure':r'$\sigma$(GPa)',
            'Freq':'$f$ (Hz)',
            'Amp':'$V_exc$ (V)',
            'Mag':r'$|V|$ (V)',
            'Phase':r'$\phi$ (deg)',
            'X':'$V_X$ (V)',
            'Y':'$V_Y$ (V)',
            'NSR':'$NSR$',
            'Y_mean':'$V_Y$ (V)',
            'displacement':r'$d(\mu m)$'
    }


    
def plotting_process(stop_event, clear_queue, data_queue, configs):
    max_plot_N = configs.get('max_plot_N', 10000)
    plotAxesColNames = configs['plot_axes_col_names']
    axeNameMapper = configs.get('axe_name_mapper', defaultAxeMapper)
    plotAxesColNames = configs['plot_axes_col_names']
    m, n = configs['ncol'], configs['nrow']
    data_buffer = deque(maxlen=max_plot_N)
    def map_plot_axes(plotAxesColNames):
        axesNames = []
        for pair in plotAxesColNames:
            pair_lst = []
            # print(pair)
            for i in range(len(pair)):
                name  = axeNameMapper.get(pair[i].split(':')[-1],pair[i].split(':')[-1])
                pair_lst.append(
                    
                    pair[i].split(':')[0]+':'+name
                )
            axesNames.append(pair_lst)
        return axesNames
    axesNames = map_plot_axes(plotAxesColNames)

    plt.ion()
    fig, axes = plt.subplots(m, n, constrained_layout=True)
    fit_fig_left_third(fig)
    df_plot = pd.DataFrame(columns=list(set(np.array(plotAxesColNames).flatten())))
    # print(df_plot)
    lines = []
    
    for i, (xname, yname) in enumerate(plotAxesColNames):
        lm, ln = i // n, i % n
        line, = axes[lm, ln].plot([], [], lw=2,color = colorseries[i], marker='$\u2764\uFE0F$')
        axes[lm,ln].set_xlabel(axesNames[i][0],fontsize=10,labelpad=8)
        axes[lm,ln].set_ylabel(axesNames[i][1],fontsize=10,labelpad=8)
        lines.append(line)
    time.sleep(5)
    while not stop_event.is_set():
        while not data_queue.empty():
            data_point = data_queue.get()
            # print(data_point)
            data_buffer.append(data_point)
            df_plot = pd.DataFrame(data_buffer)
            # df_plot.loc[len(df_plot)] = data_point
            # if len(df_plot) > max_plot_N:
            #     df_plot = df_plot.iloc[-max_plot_N:].copy()
            # print(df_plot)
        if not len(df_plot) > 0:
            # print('0 being plot!')
            continue
            

        for i, (xname, yname) in enumerate(plotAxesColNames):
            # print(xname,yname)
            x = df_plot[xname].to_numpy()
            y = df_plot[yname].to_numpy()
            # print(x,y)
            lines[i].set_data(x, y)
            lm, ln = i // n, i % n
            ax = axes[lm, ln]
            ax.relim()
            ax.autoscale_view()
          
            if '(s)' in axesNames[i][0]:
                ax.get_xaxis().set_major_locator(AutoLocator())
                ax.xaxis.set_major_formatter(formatter_date)
            else:
                xlocator = AdaptiveCleanTickLocator(span=
                                                    [df_plot[plotAxesColNames[i][0]].min(),
                                                     df_plot[plotAxesColNames[i][0]].max()]
                                                   )
                ax.get_xaxis().set_major_locator(xlocator)
                ax.xaxis.set_major_formatter(FuncFormatter(scientific_formatter))

            ylocator = AdaptiveCleanTickLocator(span=
                                                [df_plot[plotAxesColNames[i][1]].min(),
                                                 df_plot[plotAxesColNames[i][1]].max()]
                                               )
            ax.get_yaxis().set_major_locator(ylocator)
            ax.yaxis.set_major_formatter(FuncFormatter(scientific_formatter))
            ax.autoscale_view()
            ax.tick_params(which='major',direction='in',length=6,width=2,labelsize=8,rotation=45)

        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(2)