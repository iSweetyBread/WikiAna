import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from misc_utils.datetime_utils import (convert_to_datetime)

import json

# Function for time-series aggregation of an array of article edits
# raw_data -> array of dicts containing recent_changes data
# time_span -> string deciding a time span for aggregating changes. Default = 'hour'
# possible values: 'minute', 'hour', 'day', 'week', 'month', 'year'
# mode -> key for additional aggregation. Default = 'default'
# possible values: 'usertype', 'edit_size'; can be combined with " | " pipe symbol
# exclude -> key and value for removing certain data from initial dataset
# keys and values are comgined with " = " symbol, key-value pairs are combined " & " symbol
# possible keys: 'username', 'usertype', 'edit_size'
# possible values: for 'username' -> username, for 'usertype' -> 'bot' 'temp' 'user', for 'edit_size' -> 'major' 'minor'
# values can be combined with " | " pipe symbol
# returns a dict with: final DataFrame, total amount of entries, dict with totals for different categories, dict with averages for different categories
def group_edits(raw_data, time_span = 'hour', mode = '', exclude = ''):
    # processes the exclude filter string into a python dict
    filters = {}
    if exclude:
        for i in exclude.split('&'):
            if '=' not in i: continue
            
            key, value = i.split('=', 1)
            filters[key.strip()] = [v.strip() for v in value.split('|') if v.strip()]
            
    # helper function to exclude certain objects from the dataset
    def _exclude(obj, filters):
        if 'usertype' in filters:
            if obj['usertype'] in filters['usertype']: return False
            
        if 'edit_size' in filters:
            if obj['edit_size'] in filters['edit_size']: return False
            
        if 'user' in filters: 
            if obj['username'] in filters['username']: return False
        
        return True
    
    data = []
    
    # transforms the api data into a standardised format, filters out entries, and populates the dataset
    for i in raw_data:
        entry = {
            'revid': i['revid'],
            'user': i['user'],
            'userid': i['userid'],
            'timestamp': convert_to_datetime(i['timestamp']),
            'usertype': ('temp' if 'temp' in i else 'bot' if 'bot' in i else 'user'),
            'edit_size': ('minor' if 'minor' in i else 'major')
        }
        if _exclude(entry, filters): data.append(entry)
    
    preprocessed_data = pd.DataFrame(data)
    # returns an empty final dict, if the dataset is empty
    if preprocessed_data.empty:
        return {
            'final_dataframe': pd.DataFrame(),
            'dataframe_averages': {},
            'dataframe_totals': {},
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

    # gathers aggregation modes if provided
    modes = [i.strip() for i in mode.split('|') if i.strip()] if mode else []
    
    # raises an exception if unhandled aggregation modes are provided
    for i in modes:
        if i not in ['usertype', 'edit_size']:
            raise Exception(f"Invalid aggregation mode: {i}")
                
    averages, totals = {}, {}
    
    # gathers averages and totals for the entire data set
    # .reindex(all_groups, fill_value=0) part is responsible for creating "0" values, if there were no edits in a certain time frame fraction
    # i. e. if there were no edits at 10 AM, in the average gathering its amount of edits would be included as "0"
    # same for _period_means() helper func
    averages[f'{time_span}_average'] = preprocessed_data.groupby('time_group').size().reindex(all_groups, fill_value=0).mean()
    totals['total_amount'] = len(preprocessed_data)
    
    # helper function to generate a dict key for categorie averages and totals
    def _key(index):
        if not isinstance(index, tuple): index = (index,)
        return '_'.join(str(x) for x in index)
    
    # helper function to get a DataFrame used to gather averages by given categories per given time frame
    def _period_means(cols):
        counts = preprocessed_data.groupby(['time_group'] + cols).size().unstack(cols, fill_value=0)
        return counts.reindex(all_groups, fill_value=0).mean()
    
    # gathers averages and totals per aggregation modes per time frame
    # example: average bot edits per hour
    for i in modes:                
        for index, value in _period_means([i]).items():
            averages[f"average_{_key(index)}"] = value
        for index, value in preprocessed_data.groupby(i).size().items():
            totals[f"total_{_key(index)}"] = value
    
    # gathers averages and totals per combinations of aggregation modes per time frame
    # example: average bot minor edits per hour  
    if len(modes) > 1:                        
        for index, value in _period_means(modes).items():
            averages[f"average_{_key(index)}"] = value
        for index, value in preprocessed_data.groupby(modes).size().items():
            totals[f"totals_{_key(index)}"] = value
            
    return {
        'final_dataframe': preprocessed_data.groupby(['time_group'] + modes).agg(revid=('revid', 'count')),
        'dataframe_averages': averages,
        'dataframe_totals': totals,
        'entry_amount': len(preprocessed_data)
    }
    
def show_plot(dataframe):
    ax = dataframe.plot(kind='bar', color='blue', title='Hourly edits')
    ax.set_xlabel('Hour')
    ax.set_ylabel('Hourly Edits')
    
    plt.show()

with open('data_debug/time_series_data.json', 'r', encoding='utf-8') as file:
    aaa = group_edits(json.load(file), mode='usertype|edit_size', exclude='usertype=bot|temp&edit_size=major')
    print(aaa['dataframe_averages'])
    # show_plot(aaa['final_dataframe'])
    
    # show_plot(group_edits(json.load(file), mode='usertype')['final_dataframe'])