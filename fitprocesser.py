
import matplotlib.pyplot as plt
import datetime
from datetime import date
from math import sqrt, floor
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from typing import Dict, Union, Optional,Tuple
import os
from garmin_fit_sdk import Decoder,Stream,profile
import sys

def processFile(fname):
    stream = Stream.from_file(fname)
    decoder = Decoder(stream)
    messages, errors = decoder.read()
    summarydata1 = pd.DataFrame(messages['session_mesgs'])
    summarydata1['Exercise_Day']=summarydata1['timestamp'].dt.date
    summarydata=summarydata1[['timestamp'
                                ,'start_time','start_position_lat','start_position_long','total_elapsed_time','total_timer_time','total_distance'
                                ,'total_cycles','end_position_lat','end_position_long','total_work','sport_profile_name','training_load_peak'
                                ,'message_index','total_calories','avg_speed','max_speed','avg_power','max_power','total_ascent','total_descent','first_lap_index'
                                ,'num_laps','normalized_power','training_stress_score','intensity_factor','left_right_balance','threshold_power','event'
                                ,'event_type','sport','sub_sport','avg_heart_rate','max_heart_rate','avg_cadence','trigger','avg_temperature','max_temperature','Exercise_Day']]
    return summarydata
    #recordhistory = pd.dataframe()
    #recordhistory = pd.DataFrame(messages["record_mesgs"])

def fileidmessages(fname):
    stream = Stream.from_file(fname)
    decoder = Decoder(stream)
    messages, errors = decoder.read()
    return messages

def convert_to_preferred_format(sec):
   sec = sec % (24 * 3600)
   hour = sec // 3600
   sec %= 3600
   min = sec // 60
   sec %= 60
   return "%02d:%02d:%02d" % (hour, min, sec) 

def TransformFile(infile):
    infile['Elapsed_Time']=infile['total_elapsed_time'].apply(convert_to_preferred_format)
    infile['Timer_Time']=infile['total_timer_time'].apply(convert_to_preferred_format)
    infile['Miles']=(infile['total_distance']*0.621371) / 1000
    #outfile = pd.melt(infile)
    outfile = infile
    return outfile
