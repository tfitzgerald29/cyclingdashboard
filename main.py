from frontend import CyclingDataPipes,fitprocesser
import datetime
import json
import pandas as pd
from dash import Dash, html, dash_table, dcc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from threading import Timer
import webbrowser
import os
from dash import Dash, html, dash_table, dcc

def create_app(startdt,enddt,datset,brwsr):

    recentrides_tbl,recentrides_grph,hrs,dst = CyclingDataPipes.recentrides(datset)
    app = Dash(__name__,title="Cycling performance metrics")

    #app layout
    app.layout = html.Div(children=[
    # All elements from the top of the page
    dcc.Tabs([dcc.Tab(label = 'Recent Ride KPIs',children = [

        html.Div([
            html.H1(children='Daily volume last 14 days')
            ,html.Div(children=f'''Distance: {dst}''')
            ,html.Div(children=f'''Hours: {hrs}''')
            ,dcc.Graph(id='graph_0',figure=recentrides_grph)
        ]),

        html.Div([
                html.H1(children = 'Recent rides')
                ,dcc.Graph(id='table1',figure=recentrides_tbl)
        ])
    ]),

    dcc.Tab(label = 'Over time KPIs',children = [

        html.Div([
            html.H1(children='Miles and Hours Ridden Per Year')
            ,html.Div(children='''''')
            ,dcc.Graph(id='graph0',figure=CyclingDataPipes.annualdistance(datset))
        ]),

    html.Div([
            html.H1(children='Miles and Hours Ridden Per month')
            ,html.Div(children='''''')
            ,dcc.Graph(id='graph1',figure=CyclingDataPipes.monthlyDistance(datset))
    ]),

    # New Div for all elements in the new 'row' of the page
        html.Div([
            html.H1(children='Chronic Training Load')
            ,html.Div(children='''moving average of last 42 days of training stress score''')
        ,dcc.Graph(id='graph2',figure=CyclingDataPipes.CTL_Graph(datset,startdt,enddt))
        ])
    ])
    
    ])])

    
    brw = webbrowser.open(brwsr, new=0, autoraise=False)
    srv = app.run_server(debug=True, port=8050)
    return brw,srv

futuredate = f''' '{datetime.date.today() + datetime.timedelta(days=90)}' '''

new_files=CyclingDataPipes.processnewfiles()
existing_files = CyclingDataPipes.readin_existingFiles()

if len(os.listdir(f"/Users/tylerfitzgerald/Downloads/"))>0:
    finalfile = CyclingDataPipes.create_new_file(newFile=new_files,ExistingFile=existing_files)
    CyclingDataPipes.write_out_file(finalfile)
    fd = CyclingDataPipes.FutureDates('2022-01-01',futuredate)
    cd = CyclingDataPipes.createDataFrame(finalfile)
    mg = CyclingDataPipes.MergedDataFrames(fd,cd)
else:
    mg = CyclingDataPipes.FutureDates('2022-01-01',futuredate)

# Run the app
if __name__ == '__main__':
    create_app(startdt='2023-01-01',enddt=futuredate,datset=mg,brwsr='http://127.0.0.1:8050/')
