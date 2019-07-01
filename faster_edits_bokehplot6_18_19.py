import bokeh

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource, show, gridplot
from bokeh.models import DatetimeTickFormatter, CustomJS
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn, Button
from bokeh.io import curdoc

import numpy as np
import pandas as pd
import datetime as dt
import serial
import re

count_7000 = [0]

def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    return True

bc_correction = 0.64 # for the ABCD
now_time = dt.datetime.now()

#UCB_ser = serial.Serial('COM7', 9600, timeout = 1, bytesize = serial.SEVENBITS)
LI7000_ser = serial.Serial('COM3', 9600) #correct COM
LI820_ser = serial.Serial('COM8', 9600)
SBA5_ser= serial.Serial('COM6', 19200)
MA300_ser= serial.Serial('COM13', 1000000)
ABCD_ser = serial.Serial('COM12', 57600)
AE33_ser = serial.Serial('COM4', 9600)

df = {"Time": [],'ABCD_BC_original':[],'ABCD_BC_corrected':[], 'ABCD_att':[], 'ABCD_flow':[],'MA300_BC':[], 'SBA5_CO2':[],'AE33_BC':[], 'LI820_CO2':[],'LI7000_CO2':[]}


source = ColumnDataSource({"Time": [],
                                'ABCD_BC_original':[],'ABCD_BC_corrected':[], 'ABCD_att':[], 'ABCD_flow':[],'MA300_BC':[], 'SBA5_CO2':[],'AE33_BC':[], 'LI820_CO2':[],'LI7000_CO2':[]})

def update():
    time_now = dt.datetime.now()

    SBA5_l1 = SBA5_ser.readline().decode('utf-8').split('\n')[0].split(' ')
    MA300_l1 = MA300_ser.readline().decode('utf-8').split('\n')[0].split(',')
    ABCD_l1 = ABCD_ser.readline().decode('utf-8').split('\n')[0].split(',')
    AE33_l1 = AE33_ser.readline().decode('utf-8').split('\n')[0].split(',')
    LI820_l1 = LI820_ser.readline().decode('utf-8')
    LI820_l1 = re.split(r'[<>]', LI820_l1)
    LI820_l2 = LI820_ser.readline().decode('utf-8')
    LI820_l2 = re.split(r'[<>]', LI820_l2)
    LI7000_l1 =LI7000_ser.readline().decode('utf-8').split('\n')[0].split('\t')
    LI7000_l2 =LI7000_ser.readline().decode('utf-8').split('\n')[0].split('\t')


    ABCD_BC_original = []
    ABCD_att = []
    ABCD_BC_corrected = []
    ABCD_flow =  []
    MA300_BC = []
    AE33_BC = []
    LI820_CO2 = []
    LI7000_CO2 = []
    SBA5_CO2 = []
    if len(ABCD_l1)>=7:
        ABCD_BC_original.append(float(ABCD_l1[4]))
        ABCD_att.append(float(ABCD_l1[3]))
        ABCD_BC_corrected.append(round(ABCD_BC_original[0]/(np.exp(-1*ABCD_att[0]/100)*bc_correction + 1-bc_correction),4))
        ABCD_flow.append(float(ABCD_l1[7]))
        #print(len(ABCD_l1))
    else:
        ABCD_BC_original.append('')
        ABCD_att.append('')
        ABCD_BC_corrected.append('')
        ABCD_flow.append('')
        print('issue with ABCD: {} length: {}, length should be: 9'.format(time_now,len(ABCD_l1)))
        print('ABCD_line: {}\n'.format(ABCD_l1))

    #print(len(MA300_l1))
    if len(MA300_l1) == 38:
        print("closing and opening MA300 port")
        MA300_ser.close()
        MA300_ser.open()
        MA300_l1 = MA300_ser.readline().decode('utf-8').split('\n')[0].split(',')
    if len(MA300_l1)==46 and is_number(MA300_l1[44]):
        MA300_BC.append(float(MA300_l1[44])/1000)
    else:
        MA300_BC.append('')
        print('issue with MA300: {} length: {}, length should be: 46'.format(time_now,len(MA300_l1)))
        print('MA300_line: {}\n'.format(MA300_l1))



    if len(SBA5_l1)>=8:
        SBA5_CO2.append(float(SBA5_l1[3]))
    else:
        SBA5_CO2.append('')
        print('issue with SBA5: {} length: {}, length should be: 8'.format(time_now,len(SBA5_l1)))
        print('SBA5_line: {}\n'.format(SBA5_l1))

    #print(len(AE33_l1))
    if len(AE33_l1)>=30 and is_number(AE33_l1[9]):
        AE33_BC.append(float(AE33_l1[9])/1000)
    else:
        AE33_BC.append('')
        print('issue with AE33: {} length: {}, length should be: 53'.format(time_now,len(AE33_l1)))
        print('AE33_line: {}\n'.format(AE33_l1))


    if len(LI820_l1)==33 and is_number(LI820_l1[14]):
        LI820_CO2.append(round(float(LI820_l1[14]),2))
        #print(len(LI820_l1))
    elif len(LI820_l2)==33 and is_number(LI820_l2[14]):
        LI820_CO2.append(round(float(LI820_l2[14]),2))
    else:
        LI820_CO2.append('')
        print('issue with LI820: {} length: {}, length should be: 33'.format(time_now,len(LI820_l1)))
        print('LI820_LINE1: {}'.format(LI820_l1))
        print('LI820_LINE2: {}\n'.format(LI820_l2))

    if len(LI7000_l1)>=25:
        LI7000_CO2.append(float(LI7000_l1[8]))
    elif len(LI7000_l2)>= 25:
        LI7000_CO2.append(float(LI7000_l2[8]))
    else:
        print('issue with LI7000: {} length: {}, length should be: 25'.format(time_now,len(LI7000_l1)))
        print('LI7000_LINE1: {}'.format(LI7000_l1))
        print('LI7000_LINE2: {}\n'.format(LI7000_l2))
        count_7000[0] +=1
        if len(count_7000)==5:
            count_7000[0] = 0
            print("closing and opening LI7000 port")
            LI7000_ser.close()
            LI7000_ser.open()
        LI7000_CO2.append('')


    new = {"Time": [time_now],'ABCD_BC_original':ABCD_BC_original,'ABCD_BC_corrected':ABCD_BC_corrected, 'ABCD_att':ABCD_att, 'ABCD_flow':ABCD_flow,'MA300_BC':MA300_BC,'SBA5_CO2':SBA5_CO2,'AE33_BC':AE33_BC, 'LI820_CO2': LI820_CO2, 'LI7000_CO2':LI7000_CO2}
    #print(pd.DataFrame(new))
    def df_extend(new):
        df['Time'].extend(new['Time'])
        df['ABCD_BC_original'].extend(new['ABCD_BC_original'])
        df['ABCD_BC_corrected'].extend(new['ABCD_BC_corrected'])
        df['ABCD_att'].extend(new['ABCD_att'])
        df['ABCD_flow'].extend(new['ABCD_flow'])
        df['MA300_BC'].extend(new['MA300_BC'])
        df['AE33_BC'].extend(new['AE33_BC'])
        df['SBA5_CO2'].extend(new['SBA5_CO2'])
        df['LI820_CO2'].extend(new['LI820_CO2'])
        df['LI7000_CO2'].extend(new['LI7000_CO2'])
        pd.DataFrame(df).to_csv(now_time.strftime('%y_%m_%d_%H_%M'+'.csv'))
    df_extend(new)
    source.stream(new,rollover = 120)


curdoc().add_periodic_callback(update, 1000)
fig1 = figure(title = 'ABCD/MA300/AE33 Black Carbon (micrograms/m^3)',sizing_mode = 'scale_width', plot_width =800,plot_height = 200 )
fig1.line(source=source,x='Time',y='ABCD_BC_corrected',line_width = 2,color ='orange',legend = 'ABCD')
fig1.xaxis.formatter=DatetimeTickFormatter(days=["%m/%d %H:%M:%S"],
    months=["%m/%d %H:%M:%S"],
    hours=["%m/%d %H:%M:%S"],
    hourmin = ["%m/%d %H:%M:%S"],
    minutes=["%m/%d %H:%M:%S"],
    seconds=["%m/%d %H:%M:%S"],
    minsec = ["%m/%d %H:%M:%S"])

fig1.line(source=source,x='Time',y='MA300_BC',line_width = 2,color ='blue',legend = 'MA300')
fig1.line(source=source,x='Time',y='AE33_BC',line_width = 2,color ='green',legend = 'AE33')
fig1.legend.location='top_left'

    #fig1.line(source=source,x='Time',y='AE33_BC',line_width = 2,color ='green',legend = 'AE33')
    #fig1.legend.location='top_left'



fig2 = figure(title = 'Carbon Dioxide (ppm)',sizing_mode = 'scale_width', plot_width =800,plot_height = 200)
fig2.line(source=source,x='Time',y='SBA5_CO2',line_width = 2,color ='red',legend = 'SBA5')
fig2.line(source=source,x='Time',y='LI820_CO2',line_width = 2,color ='purple',legend = 'LI820')
fig2.line(source=source,x='Time',y='LI7000_CO2',line_width = 2,color ='yellow',legend = 'LI7000')
fig2.xaxis.formatter=DatetimeTickFormatter(days=["%m/%d %H:%M:%S"],
    months=["%m/%d %H:%M:%S"],
    hours=["%m/%d %H:%M:%S"],
    hourmin = ["%m/%d %H:%M:%S"],
    minutes=["%m/%d %H:%M:%S"],
    seconds=["%m/%d %H:%M:%S"],
    minsec = ["%m/%d %H:%M:%S"])
fig2.legend.location='top_left'




columns = [TableColumn(field="Time", title="Time", formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S"), width = 400),
                    TableColumn(field = 'SBA5_CO2', title = 'SBA5_CO2'),
                    TableColumn(field = 'LI820_CO2', title = 'LI820_CO2'),
                    TableColumn(field = 'LI7000_CO2', title = 'LI7000_CO2'),
                    TableColumn(field = 'AE33_BC', title = 'AE33_BC'),
                    TableColumn(field = 'MA300_BC',title = 'MA300_BC'),
                    TableColumn(field='ABCD_BC_corrected', title='ABCD_BC_corrected'),
                    TableColumn(field='ABCD_BC_original', title='ABCD_BC_original'),
                    TableColumn(field='ABCD_att', title='ABCD_att'),
                    TableColumn(field='ABCD_flow', title='ABCD_flow')]
data_table = DataTable(source=source, columns=columns, width = 1200 )

def close_app():
    server.stop()
    for data in [ABCD_ser,MA300_ser,SBA5_ser,AE33_ser, LI820_ser,LI7000_ser]:
        data.close()

button = Button(label="Close Program", button_type="success")
button.on_click(close_app)
curdoc().add_root(fig1)
curdoc().add_root(fig2)
curdoc().add_root(data_table)

curdoc().add_root(button)
