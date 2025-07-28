import pandas as pd
import os
import csv
from .utility import now, get_highest_indx,get_highest_indx_file
def init_file(filename, col_names,idx,datafolder):
    highest_idx, last_file, last_file_name = get_highest_indx_file(datafolder)
    if last_file_name == filename:
        csvfile = open(os.path.join(datafolder,last_file+'.dat'), 'a', newline='')
        csvwriter = csv.writer(csvfile,delimiter='\t')
    else:
        
        csvfile = open(os.path.join(datafolder,'%03d-'%idx+now()+'--'+filename+'.dat'), 'w', newline='')
        csvwriter = csv.writer(csvfile,delimiter='\t')
        csvwriter.writerow(col_names)
    
    return csvfile, csvwriter
def read_file(filename):
    return pd.read_csv(filename,sep='\t')
def read_idx(folder,idx):

    files = os.listdir(folder)
    #idx = [0]
    for i in range(len(files)):
        try:
            im = int(files[i][:3])
            if im == idx:
                return read_file(os.path.join(folder,files[i]))
        except:
            pass
    return None
def read_max_idx(folder):
    idx = get_highest_indx(folder)
    return read_idx(folder,idx)

def read_stable_idx(folder,idx):

    files = os.listdir(folder)
    #idx = [0]
    for i in range(len(files)):
        if files[i][:6] != 'stable':
            continue
        try:
            im = int(files[i][7:10])
            if im == idx:
                return read_file(os.path.join(folder,files[i]))
        except:
            pass
    return None