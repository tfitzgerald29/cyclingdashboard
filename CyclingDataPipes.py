import json
import matplotlib.pyplot as plt
import datetime
from datetime import date
from datetime import datetime,timedelta
from math import sqrt, floor
import numpy as np
import pandas as pd
# import pathlib
import plotly.graph_objs as go
from datetime import datetime, timedelta
from typing import Dict, Union, Optional,Tuple
from plotly.subplots import make_subplots
from dash import Dash, html, dash_table, dcc

import os
import shutil
from garmin_fit_sdk import Decoder,Stream,profile
import sys
from dateutil import tz
from pytz import timezone
import seaborn as sns
import matplotlib.dates as md
import plotly.express as px
from threading import Timer
import webbrowser

def processnewfiles() -> list:
    mega_list = []
    with os.scandir(f"/Users/tylerfitzgerald/Downloads/") as path:
        for entry in path:
            if entry.name.endswith(".fit") and entry.is_file():
                stream = Stream.from_file(entry.path)
                decoder = Decoder(stream)
                messages, errors = decoder.read()

                for dic in messages['session_mesgs']:
                    new_dict = {}
                    for k,v in dic.items():
                        if not str(k).isdigit():
                            if k == 'timestamp':
                                new_dict[str(k)]=str(v.astimezone(timezone('America/Denver')).date())
                                new_dict['yr']=v.astimezone(timezone('America/Denver')).year
                                new_dict['week_num']=v.astimezone(timezone('America/Denver')).isocalendar().week
                                new_dict['mnth'] = v.astimezone(timezone('America/Denver')).month
                                new_dict['week_num_yr'] = str(str(new_dict['yr']) + "_" + str(new_dict['week_num']))
                                new_dict['yrmo'] = int((v.astimezone(timezone('America/Denver')).date().year)*100 + v.astimezone(timezone('America/Denver')).date().month)
                            elif k == 'start_time':
                                new_dict[str(k)]=str(v.astimezone(timezone('America/Denver'))) #want time hours, minutes, and seconds here
                            elif k == 'total_distance':
                                new_dict['Distance_miles']=(v / 1000) * .621371
                            elif k=='total_elapsed_time':
                                new_dict['RidingTime'] = str(timedelta(seconds=round(v)))
                            elif k=='total_timer_time':
                                new_dict[k]=v
                                new_dict['PedalTime'] = str(timedelta(seconds=round(v)))
                            elif k == 'total_ascent':
                                new_dict['total_ascent_feet'] = v * 3.28084
                            elif k == 'total_descent':
                                new_dict['total_descent_feet'] = v * 3.28084
                            elif k == 'avg_temperature':
                                new_dict['avg_temp_f'] = round((v * 9/5) + 32)
                            elif k == 'avg_speed':
                                new_dict['avg_MPH'] = v * 2.23694
                            elif k == 'total_work':
                                new_dict['Kjs'] = v / 1000
                            elif k == 'left_right_balance': #this is not right
                                new_dict['PowerBalance'] = f"{v / (32768 + v):.0%}" + " R" + " | " + f"{1 - (v / (32768 + v)):.0%}" + " L"
                            else:
                                new_dict[str(k)]=v
                    try:
                         new_dict.pop("total_grit")
                         new_dict.pop("avg_flow")
                    except:
                         pass
                    mega_list.append(new_dict)
    return mega_list

def readin_existingFiles() -> json:
    path = "/Users/tylerfitzgerald/Documents/activities/output/Data_files/"
    files = os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    currentfile = max(paths, key=os.path.getctime)
    currentdatafile = os.path.basename(currentfile).replace("'","")
    z = open(f'''/Users/tylerfitzgerald/Documents/activities/output/Data_files/{currentdatafile}''')
    all_activities=json.load(z)
    return all_activities

def create_new_file(newFile,ExistingFile) -> list:
    seen=[]
    for i in newFile:
        ExistingFile.append(i)

    for x in ExistingFile:
        if x not in seen:
            seen.append(x)
    return seen

def write_out_file(outfile) -> json:
    MaxDateGetter=[]
    for k in outfile:
        MaxDateGetter.append(datetime.strptime(k['timestamp'],'%Y-%m-%d').date())
    maxDate = str(np.max(MaxDateGetter)).replace("-","")
    with open(f"/Users/tylerfitzgerald/Documents/activities/output/Data_files/HL_Summary_{maxDate}.json", "w") as of: 
        json.dump(outfile, of)

def FutureDates(startdt,enddt) -> object:
    df = pd.DataFrame({"timestamp": pd.date_range(startdt,enddt)})
    #df["Day"] = df.timestamp.dt.day_name()
    #df["Week"] = df.timestamp.dt.day_of_week
    #df["Quarter"] = df.timestamp.dt.quarter
    df["Year"] = df.timestamp.dt.year
    #df["Year_half"] = (df.Quarter + 1) // 2
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    return df

def createDataFrame(inputFile: json) -> object:
    return pd.DataFrame(inputFile)

def MergedDataFrames(DateFrame,ActualFrame):
    DF_merged = pd.merge(DateFrame,ActualFrame,how='left',on='timestamp')
    DF_merged = DF_merged.sort_values(by=['timestamp'])
    DF_merged['training_stress_score']=DF_merged['training_stress_score'].fillna(0)
    # DF_merged['CTL'] = DF_merged['training_stress_score'].rolling(window=42,center=False).mean()
    DF_merged['CTL'] = DF_merged['training_stress_score'].rolling(window=42).mean()
    DF_merged['timestamp']=pd.to_datetime(DF_merged['timestamp'])
    return DF_merged

def monthlyDistance(mg):
    aggregate_df = mg.groupby(['yrmo'])[['Distance_miles','total_timer_time']].sum().reset_index().sort_values(by=['yrmo'])
    aggregate_df['total_timer_time'] = round(aggregate_df['total_timer_time'] / 3600,2)
    aggregate_df['yrmo']= aggregate_df['yrmo'].astype(int)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=aggregate_df['yrmo'].astype(str),y=aggregate_df.Distance_miles,name="Distance In Miles"                 
            ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=aggregate_df['yrmo'].astype(str),y=aggregate_df.total_timer_time,name="Riding Time",mode='lines+markers'),
        secondary_y=True
    )

    # Add figure title
    fig.update_layout(
        # title_text="Miles and hours by month"
        legend=dict(
        orientation="h"        
        ,yanchor="auto"
        ,y=.99
        ,xanchor="auto"
        ,x=.01
    )
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Year and Month")

    # Set y-axes titles
    fig.update_yaxes(title_text="Distance Ridden", secondary_y=False)
    fig.update_yaxes(title_text="Hours Ridden", secondary_y=True)

    return fig

def CTL_Graph(DF_merged,startdt,enddt):
    derp = DF_merged[(pd.to_datetime(DF_merged['timestamp'])>=startdt) & (pd.to_datetime(DF_merged['timestamp'])<=enddt)]
    fig = px.line(derp,x='timestamp',y='CTL',width=1400, height=800,markers=True)
    return fig

def annualdistance(mg):
    aggregate_df = mg.groupby(['yr'])[['Distance_miles','total_timer_time']].sum().reset_index().sort_values(by=['yr'])
    aggregate_df['total_timer_time'] = round(aggregate_df['total_timer_time'] / 3600,2)
    aggregate_df['yr'] = aggregate_df['yr'].astype(int)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=round(aggregate_df['yr']).astype(str),y=aggregate_df.Distance_miles,name="Distance In Miles",text=round(aggregate_df.Distance_miles)
            ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=round(aggregate_df['yr']).astype(str),y=aggregate_df.total_timer_time,name="Riding Time",mode='lines+markers'),
        secondary_y=True
    )

    # Add figure title
    fig.update_layout(
        # title_text="Miles and hours by month"
        legend=dict(
        orientation="h"        
        ,yanchor="auto"
        ,y=.99
        ,xanchor="auto"
        ,x=.01
    )
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Year")

    # Set y-axes titles
    fig.update_yaxes(title_text="Distance Ridden", secondary_y=False)
    fig.update_yaxes(title_text="Hours Ridden", secondary_y=True,range=[0,400])

    return fig

def recentrides(mg):
    incl = f'''{date.today()+timedelta(days=-14)}'''
    recent_rides = mg[(mg['timestamp'] >= incl) & (mg['RidingTime'].notnull() ) ].copy()
    recent_rides['date'] = recent_rides['timestamp'].dt.date
    recent_rides['Distance_miles'] = round(recent_rides['Distance_miles'],2)
    recent_rides['total_ascent_feet'] = round(recent_rides['total_ascent_feet'],2)
    recent_rides['total_descent_feet'] = round(recent_rides['total_descent_feet'],2)
    recent_rides['hours'] = recent_rides['total_timer_time'] / 3600
    recent_rides['Kjs'] = round(recent_rides['Kjs'],0)

    recent_rides = recent_rides[['yr','sub_sport','hours','date','RidingTime','PedalTime','Distance_miles','Kjs','avg_power','max_power','normalized_power'
         ,'training_stress_score','intensity_factor','PowerBalance','avg_cadence','total_ascent_feet','total_descent_feet'
         ]].sort_values(by = 'date',ascending = False)
    recent_rides = recent_rides.rename(columns = {'Distance_miles':'Distance'
                                                  ,'training_stress_score':'TSS'
                                                  ,'total_ascent_feet':'ascent'
                                                  ,'total_descent_feet':'descent'
                                                  ,'sub_sport':'sport'
                                                  ,'normalized_power':'NP'
                                                  ,'intensity_factor':'IF'
                                                  })
    vals = recent_rides.columns.to_list()
    vals.remove('hours')

    fig_tbl = go.Figure(data = go.Table(
                                    columnwidth = [400,400]
                                    ,header=dict(values=vals)
                                    ,cells=dict(values=[recent_rides[col] for col in vals])
                        )
                    
                    )
    
    fig_grph = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig_grph.add_trace(
        go.Bar(x=round(recent_rides['date']).astype(str),y=recent_rides.Distance,name="Distance In Miles",text=recent_rides.Distance           
            ),
        secondary_y=False,
    )

    fig_grph.add_trace(
        go.Scatter(x=round(recent_rides['date']).astype(str),y=recent_rides.hours,name="Riding Time",mode='lines+markers'),
        secondary_y=True
    )

    # Add figure title
    fig_grph.update_layout(
        # title_text="Miles and hours by month"
        legend=dict(
        orientation="h"        
        ,yanchor="auto"
        ,y=.99
        ,xanchor="auto"
        ,x=.01
    )
    )

    # Set x-axis title
    fig_grph.update_xaxes(title_text="Day")

    # Set y-axes titles
    fig_grph.update_yaxes(title_text="Distance Ridden", secondary_y=False)
    fig_grph.update_yaxes(title_text="Hours Ridden", secondary_y=True,range=[0,5])

    hrs = round(np.sum(recent_rides.hours),1)
    dst = np.sum(recent_rides.Distance)
    
    return fig_tbl,fig_grph,hrs,dst
