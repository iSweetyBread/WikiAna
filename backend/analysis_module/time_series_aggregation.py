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
# possible values: 'default', 'usertype', 'editsize'; can be combined
def group_edits(raw_data, time_span = None, mode = None, filter = None):
    data = []
        
    for i in raw_data:
        entry = {}
        entry['revid'] = i['revid']
        entry['user'] = i['user']
        entry['userid'] = i['userid']
        entry['timestamp'] = convert_to_datetime(i['timestamp'])
        if 'temp' in list(i.keys()):
            entry['usertype'] = 'temp'
        elif 'bot' in list(i.keys()):
            entry['usertype'] = 'bot'
        else:
            entry['usertype'] = 'user'
        if 'minor' in list(i.keys()):
            entry['edit_size'] = 'minor'
        else:
            entry['edit_size'] = 'major'
        data.append(entry)
    
    preprocessed_data = pd.DataFrame(data)
    
    time_span_index = None
    match time_span:
        case 'minute':
            time_span_index = preprocessed_data['timestamp'].dt.minute
        case 'hour':
            time_span_index = preprocessed_data['timestamp'].dt.hour
        case 'day':
            time_span_index = preprocessed_data['timestamp'].dt.day
        case 'week':
            time_span_index = preprocessed_data['timestamp'].dt.week
        case 'month':
            time_span_index = preprocessed_data['timestamp'].dt.month
        case 'year':
            time_span_index = preprocessed_data['timestamp'].dt.year
        case _:
            time_span_index = preprocessed_data['timestamp'].dt.hour
            
    grouped = preprocessed_data.groupby([time_span_index, 'usertype', 'edit_size'])['revid'].count()
    grouped = pd.DataFrame(grouped)
    
    averages = {}
    
    result = {
        'final_dataframe': grouped,
        'dataframe_averages': averages,
        'entry_amount': len(data)
    }
    
    return result
    
def show_plot(dataframe):
    ax = dataframe.plot(kind='bar', color='blue', title='Hourly edits')
    ax.set_xlabel('Hour')
    ax.set_ylabel('Hourly Edits')
    
    plt.show()

with open('data.json', 'r', encoding='utf-8') as file:
    show_plot(group_edits(json.load(file))['final_dataframe'])