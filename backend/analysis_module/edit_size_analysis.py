import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from misc_utils.datetime_utils import (convert_to_datetime)
from user_type_detection import (is_temp, is_bot)

import json

# ==================EXPECTED RESULT================== 
# average, total statistics (grouping by categories and sub-categories) on the delta of the changes

# Function for analysing the size changes of articles over time
# raw_data -> array of dicts containing revisions data
# exclude_minor -> bool value to skip minor edits
def edit_size_change_analysis(raw_data, exclude_minor = False):
    data = []
    
    # transforms the api data into a standardised format, filters out entries, and populates the dataset
    for i in raw_data:
        if exclude_minor and 'minor' in i: continue
        
        entry = {
            'text': i['*'],
            'comment': i['comment'],
            'contentformat': i['contentformat'],
            'contentmodel': i['contentmodel'],
            'parentid': i['parentid'],
            'revid': i['revid'],
            'size': i['size'],
            'edit_size': ('minor' if 'minor' in i else 'major'),
            'tags': i['tags'],
            'timestamp': convert_to_datetime(i['timestamp']),
            'user': i['user'],
            'userid': i['userid'],
        }
        data.append(entry)
        
    preprocessed_data = pd.DataFrame(data)
    # returns an empty final dict, if the dataset is empty
    if preprocessed_data.empty:
        return {
            'final_dataframe': pd.DataFrame(),
            'entry_amount': 0
        }
        
    # returns a datafram with edit sizes and their corresponding dates + number of processed entries
    return {
        'final_dataframe': preprocessed_data.groupby(['timestamp', 'size']).size().reset_index(name='edit_count').drop(columns=['edit_count']),
        'entry_amount': len(preprocessed_data)
    }

def edit_size_delta_analysis(raw_data, time_span = 'hour', exclude=''):
    # processes the exclude filter string into a python dict
    filters = {}
    if exclude:
        for i in exclude.split('&'):
            if '=' not in i: continue
    
            key, value = i.split('=', 1)
            filters[key.strip()] = [v.strip() for v in value.split('|') if v.strip()]
    
    # helper function to exclude certain objects from the dataset
    def _exclude(obj, filters):    
        if 'edit_size' in filters:
            if obj['edit_size'] in filters['edit_size']: return False
        
        return True
    
    data = []
    
    # transforms the api data into a standardised format, filters out entries, and populates the dataset
    for i in raw_data:        
        entry = {
            'text': i['*'],
            'comment': i['comment'],
            'contentformat': i['contentformat'],
            'contentmodel': i['contentmodel'],
            'parentid': i['parentid'],
            'revid': i['revid'],
            'size': i['size'],
            'edit_size': ('minor' if 'minor' in i else 'major'),
            'tags': i['tags'],
            'timestamp': convert_to_datetime(i['timestamp']),
            'user': i['user'],
            'userid': i['userid'],
            'usertype': ('temp' if is_temp(i['user']) else 'bot' if is_bot(i['user']) else 'user')
        }
        if _exclude(entry, filters): data.append(entry)
        
    data = sorted(data, key=lambda x: x['timestamp'])
    
    for i in range(len(data)):
        data[i]['rel_delta'] = (data[i-1]['size']-data[i]['size']) * -1 if i-1 >= 0 else data[i]['size']
        data[i]['abs_delta'] = abs(data[i-1]['size']-data[i]['size']) if i-1 >= 0 else data[i]['size']
        
    preprocessed_data = pd.DataFrame(data)
    # returns an empty final dict, if the dataset is empty
    if preprocessed_data.empty:
        return {
            'final_dataframe': pd.DataFrame(),
            'dataframe_averages': {},
            'entry_amount': 0
        }
            
    # establishes the given time period and converts it to the standard Pandas DataFrame format 
    preprocessed_data['timestamp'] = pd.to_datetime(preprocessed_data['timestamp'])
    time_frequencies = {
        'minute': 'min',
        'hour': 'h',
        'day': 'D',
        'week': 'W-SUN',
        'month': 'M',
        'year': 'Y'
    }
    frequency = time_frequencies.get(time_span, 'h')
    periods = preprocessed_data['timestamp'].dt.to_period(frequency)
    preprocessed_data['time_group'] = periods.dt.start_time
    all_groups = pd.period_range(periods.min(), periods.max(), freq=frequency).to_timestamp()
    all_groups.name = 'time_group'
    
    averages = {}
    _deltas = ['rel_delta', 'abs_delta']
    
    final_dataframe = preprocessed_data.groupby(['timestamp'] + _deltas).size().reset_index(name='_').drop(columns=['_'])
        
    for delta in _deltas:
        # average relative and absolute delta for entire dataset
        averages[f'average_{delta}'] = final_dataframe.mean()[delta]
    
        # average relative and absolute delta per time period
        averages[f'average_{delta}_per_{time_span}'] = preprocessed_data.groupby(['time_group'])[delta].aggregate(['mean']).reindex(all_groups, fill_value=0).mean()['mean']
        
        # average relative and absolute delta per user type for entire dataset
        for i, val in preprocessed_data.groupby(['timestamp', 'usertype'] + _deltas).size().reset_index(name='_').drop(columns=['_']).groupby('usertype').mean().drop(columns='timestamp')[delta].items():
           averages[f'average_{i}_{delta}'] = np.float64(val)
    
        # average relative and absolute delta per user type per time period      
        for index, value in preprocessed_data.groupby(['time_group', 'usertype'])[delta].aggregate(['mean']).groupby('usertype').mean().items():
            for i, val in value.items():
                averages[f'average_{i}_{delta}_per_{time_span}'] = np.float64(val)
            
    return {
        'final_dataframe': final_dataframe,
        'dataframe_averages': averages,
        'entry_amount': len(preprocessed_data)
    }

def show_plot(dataframe: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))

    dataframe.plot(
        color='blue',
        title='edit size',
        ax=ax
    )

    ax.set_xlabel('timestamp')
    ax.set_ylabel('edit size')

    plt.tight_layout()
    plt.show()
    plt.close(fig)

with open('data.json', 'r', encoding='utf-8') as file:
    # aaa = edit_size_change_analysis(json.load(file))
    
    aaa = edit_size_delta_analysis(json.load(file))
    # show_plot(aaa['final_dataframe'])
    print(aaa['dataframe_averages'])
    # print(aaa['final_dataframe'])