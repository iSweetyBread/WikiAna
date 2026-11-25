import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from misc_utils.datetime_utils import (convert_to_datetime)
from user_type_detection import (is_temp, is_bot)

import json

# Function for analysing the size changes of articles over time
# raw_data -> array of dicts containing revisions data
# exclude_minor -> bool value to skip minor edits
def edit_size_change_analysis(raw_data, exclude_minor = False):
    data = []
    
    # transforms the api data into a standardised format, filters out entries, and populates the dataset
    for i in raw_data:
        if exclude_minor and 'minor' in i: continue
        
        # NOTE: certain data fields are commented until they are needed
        entry = {
            # 'text': i.get('*', ''),
            # 'comment': i.get('comment', ''),
            # 'contentformat': i.get('contentformat', ''),
            # 'contentmodel': i.get('contentmodel', ''),
            # 'parentid': i.get('parentid', ''),
            # 'revid': i.get('revid', ''),
            'size': i.get('size', ''),
            'edit_type': ('minor' if 'minor' in i else 'major'),
            # 'tags': i.get('tags', ''),
            'timestamp': convert_to_datetime(i.get('timestamp', ''),),
            # 'user': i.get('user', ''),
            # 'userid': i.get('userid', ''),
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
        'final_dataframe': preprocessed_data[['timestamp', 'size']].drop_duplicates(),
        'entry_amount': len(preprocessed_data)
    }

# Function for calculating relative and absolute deltas of article edits
# raw_data -> array of dicts containing revisions data
# time_span -> string deciding a time span for aggregating changes. Default = 'hour'
# possible values: 'minute', 'hour', 'day', 'week', 'month', 'year'
# exclude -> key and value for removing certain data from initial dataset
# keys and values are comgined with " = " symbol, key-value pairs are combined " & " symbol
# possible keys: 'edit_type'
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
        if 'edit_type' in filters:
            if obj['edit_type'] in filters['edit_type']: return False
        
        return True
    
    data = []
    
    # transforms the api data into a standardised format, filters out entries, and populates the dataset
    for i in raw_data:
        # NOTE: certain data fields are commented until they are needed
        
        entry = {
            # 'text': i.get('*', ''),
            # 'comment': i.get('comment', ''),
            # 'contentformat': i.get('contentformat', ''),
            # 'contentmodel': i.get('contentmodel', ''),
            # 'parentid': i.get('parentid', ''),
            'revid': i.get('revid', ''),
            'size': i.get('size', ''),
            'edit_type': ('minor' if 'minor' in i else 'major'),
            # 'tags': i.get('tags', ''),
            'timestamp': convert_to_datetime(i.get('timestamp', ''),),
            # 'user': i.get('user', ''),
            # 'userid': i.get('userid', ''),
            'usertype': ('temp' if is_temp(i.get('user', ''),) else 'bot' if is_bot(i.get('user', ''),) else 'user')
        }
        if _exclude(entry, filters): data.append(entry)
        
    data = sorted(data, key=lambda x: x['timestamp'])
            
    preprocessed_data = pd.DataFrame(data)
    # returns an empty final dict, if the dataset is empty
    if preprocessed_data.empty:
        return {
            'final_dataframe': pd.DataFrame(),
            'dataframe_averages': {},
            'entry_amount': 0
        }
    
    # delta calculations
    preprocessed_data['rel_delta'] = preprocessed_data['size'].diff().fillna(preprocessed_data['size'])
    preprocessed_data['abs_delta'] = preprocessed_data['rel_delta'].abs()
            
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
    
    final_dataframe = preprocessed_data[['timestamp'] + _deltas].drop_duplicates()
    
    # Precalculated aggregations for the loop below
    overall_avgs = final_dataframe[_deltas].mean()
    time_avgs = preprocessed_data.groupby('time_group')[_deltas].mean().reindex(all_groups, fill_value=0).mean()
    user_timestamp_avgs = preprocessed_data[['timestamp', 'usertype'] + _deltas].drop_duplicates().groupby('usertype')[_deltas].mean()
    user_time_avgs = preprocessed_data.groupby(['time_group', 'usertype'])[_deltas].mean().reindex(pd.MultiIndex.from_product([all_groups, preprocessed_data['usertype'].unique()], names=['time_group', 'usertype']), fill_value=0).groupby(level='usertype').mean()    
    
    for delta in _deltas:
        # average relative and absolute delta for entire dataset
        averages[f'average_{delta}'] = overall_avgs[delta]
    
        # average relative and absolute delta per time period
        averages[f'average_{delta}_per_{time_span}'] = time_avgs[delta]
        
        # average relative and absolute delta per user type for entire dataset
        for usertype, value in user_timestamp_avgs[delta].items():
           averages[f'average_{usertype}_{delta}'] = np.float64(value)
    
        # average relative and absolute delta per user type per time period      
        for usertype, value in user_time_avgs[delta].items():
            averages[f'average_{usertype}_{delta}_per_{time_span}'] = np.float64(value)
            
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