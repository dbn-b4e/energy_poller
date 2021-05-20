

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# how-to add float support to ModbusClient

import time
import os
from os import system
import sys
import json
import requests
import copy
from mapping_tools import testmap
from dashing import *
import math
from emoncms import Myemon
import json


DashEnabled = False
DashingEnabled = False

if DashEnabled:
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    import plotly.express as px
    import pandas as pd
else:
    DashMeas1 = None

import threading


# --------------------------------------------------------------------------- #
# Load config file
# --------------------------------------------------------------------------- #
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        print('Found config version {} for board {}'.format( config['board']['cfg_version'], config['board']['app_name']))
        _emoncms = config['emoncms']
except OSError as e:
    if e.args[0] == uerrno.ENOENT:
        print('Config file not found, defaults used!')

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
#from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.register_read_message import ReadInputRegistersResponse, ReadHoldingRegistersResponse
from pymodbus.pdu import ExceptionResponse
from pymodbus.client.sync import ModbusSerialClient as ModbusRtuClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient as ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.compat import iteritems
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor

system('clear')


if DashingEnabled:
    ui = HSplit(
        VSplit(
            Log(title='logs', border_color=5),
            Log(title='Errors', border_color=5),
        ),
        VSplit(
            Log(title='Meas. slave 1', border_color=5),
        ),
        VSplit(
            HChart(border_color=2, color=2),
            HBrailleChart(border_color=2, color=2),
        ),
        title='Dashing',
    )
    Dashlog = ui.items[0].items[0]
    DashErrors = ui.items[0].items[1]

    DashMeas1 = ui.items[1].items[0]
    
    hchart = ui.items[2].items[0]
    bchart = ui.items[2].items[1]
    # bfchart = ui.items[1].items[5]
    Dashlog.append("")
    DashErrors.append("")
    DashMeas1.append("")
    hchart.append(55)

    ui.display()

# --------------------------------------------------------------------------- #
# Import dash style-sheet
# --------------------------------------------------------------------------- #
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# --------------------------------------------------------------------------- #
# Dash web interface
# --------------------------------------------------------------------------- #
def dash_frontend():
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    if DashingEnabled:
        Dashlog.append("Starting frontend")
        ui.display()
    else:
        log.info("Starting frontend")

    # assume you have a "long-form" data frame
    # see https://plotly.com/python/px-arguments/ for more options
    df = pd.DataFrame({
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    })

    fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

    app.layout = html.Div(children=[
        html.H1(children='Hello Dash'),

        html.Div(children='''
            Dash: A web application framework for Python.
        '''),

        dcc.Graph(
            id='example-graph',
            figure=fig
        )
    ])

    if __name__ == '__main__':
        app.run_server(debug=True, use_reloader=True)

# --------------------------------------------------------------------------- #
# EmonCms initialisation
# --------------------------------------------------------------------------- #
MyEmon = Myemon(_emoncms['emon_host'],
                _emoncms['emon_url'],
                _emoncms['emon_privateKey'],
                _emoncms['emon_node'])

# --------------------------------------------------------------------------- #
# Modbus device polling
# --------------------------------------------------------------------------- #
def device_polling():

    if DashingEnabled:
        Dashlog.append("Starting device poller")
        ui.display()
    else:
        log.info("Starting device poller")

    CONF_ORNO = False
    CONF_EM370 = True
    CONF_SOLIS_4G_3P = True
    CONF_JANITZA_B23 = True
    CONF_EMONCMS = True
    RtuclientState = False

    QuerryNb = 0

    HostName = 'emoncms.powerdale.com'
    ModbusHost = "10.10.10.101"
    ModbusPort = 502

    emon_host = "emoncms.powerdale.com";
    emon_url = "/input/post.json?node=";
    emon_privateKey="4dbf608f20eab1ad1d1bf4512dc85d1c"
    emon_node="B4E"

    # for cycle in range(0, 2000):
    #     vchart.append(50 + 50 * math.sin(cycle / 16.0))
    #     hchart.append(99.9 * abs(math.sin(cycle / 26.0)))
    #     bchart.append(50 + 50 * math.sin(cycle / 6.0))
    #     ui.display()

    
    OR_WE_514_Registers = testmap.generate_device_dict('./mapping_tools/or_we_514-v1-1_1.json')
    EEM_MA370_Registers = testmap.generate_device_dict('./mapping_tools/eem_ma370-v1-1_1.json')
    SOLIS_4G_Registers = testmap.generate_device_dict('./mapping_tools/solis_4g_3p-v1-1_1.json')
    JANITZA_B23_Registers = testmap.generate_device_dict('./mapping_tools/janitza_b23-v1-1_1.json')
    #print(OR_WE_514_Registers)
    #print(json.dumps(EEM_MA370_Registers, indent='\t'))
    #print(OR_WE_514_Registers)
    #print(EEM_MA370_Registers)
    print(SOLIS_4G_Registers)

    SolarInverter = copy.deepcopy(SOLIS_4G_Registers)
    Grid = copy.deepcopy(EEM_MA370_Registers)
    Evse = copy.deepcopy(JANITZA_B23_Registers)

    SOLIS_Config =  {
        'Solar': { "NAME": "Inverter", "PORT": "/dev/ttyUSB0", "ADDRESS": 1, "DATA": SolarInverter}
    }

    EEM_Config =    {
        'Grid': { "NAME": "Grid", "PORT": "", "ADDRESS": 1, "DATA": Grid}
    }

    B23_Config =    {
        'Evse': { "NAME": "Evse", "PORT": "/dev/ttyUSB1", "ADDRESS": 2, "DATA": Evse}
    }
    # Create modbus clients
    if CONF_EM370:
        try:
            TcpClient = ModbusTcpClient(host=ModbusHost, port=ModbusPort, auto_open=True, timeout=5)
            if DashingEnabled:
                Dashlog.append( f"Modbus TCP client connected: {TcpClient.connect()}" )
            else:
                log.info(f"Modbus TCP client connected: {TcpClient.connect()}" )
        except Exception as e:
            if DashingEnabled:
                DashErrors.append("Exception %s" % str(e))
                ui.display()
            else:
                log.info("Exception %s" % str(e))
                pass

    if CONF_SOLIS_4G_3P:
        try:
            Rtuclient = ModbusRtuClient(method='rtu', port='/dev/ttyUSB0', stopbits = 1, bytesize = 8, parity = 'N', baudrate = 9600 , timeout=1)
            if DashingEnabled:
                Dashlog.append( f"Modbus RTU port open: {Rtuclient.connect()}")
            else:
                print(f"Modbus RTU port open: {Rtuclient.connect()}")
        except Exception as e:
            if DashingEnabled:
                DashErrors.append("Exception %s" % str(e))
                ui.display()
            else:
                log.info("Exception %s" % str(e))
                pass

    if CONF_JANITZA_B23:
        try:
            Rtuclient2 = ModbusRtuClient(method='rtu', port='/dev/ttyUSB1', stopbits = 1, bytesize = 8, parity = 'N', baudrate = 9600 , timeout=1)
            if DashingEnabled:
                Dashlog.append( f"Modbus RTU port open: {Rtuclient.connect()}")
            else:
                print(f"Modbus RTU port open: {Rtuclient.connect()}")
        except Exception as e:
            if DashingEnabled:
                DashErrors.append("Exception %s" % str(e))
                ui.display()
            else:
                log.info("Exception %s" % str(e))
                pass
    

    try:
        while True:
            #os.system('cls' if os.name == 'nt' else 'clear')
            QuerryNb = QuerryNb+1
            

            if CONF_EM370 and TcpClient.is_socket_open():

                if DashingEnabled:
                    Dashlog.append("Read EEM_MA370")
                    ui.display()
                else:
                    log.info("Read EEM_MA370")

                for x, z in EEM_Config.items():
                    if DashingEnabled:
                        Dashlog.append(f"Reading slave {z['NAME']}")
                    MyDict = z['DATA']
                    #print (MyDict)
                    for k, y in MyDict.items(): 
                        #Log.append(y['Name'])
                        if  (y['Name'] == 'Active power'):
                            if DashingEnabled:
                                Dashlog.append( f"Active power: {y['Value']:.01f}W")
                                hchart.title = f"Active power: {y['Value']:.0f}W"
                                hchart.append(100*y['Value']/5000)
                                ui.display()
                        rr = None
                        try:
                            rr = TcpClient.read_holding_registers(y['Address'], y['Size'])
                        except Exception as e:
                            if DashingEnabled:
                                DashErrors.append("Exception %s" % str(e))
                                ui.display()
                            else:
                                log.info("Exception %s" % str(e))
                        if(isinstance(rr, ReadHoldingRegistersResponse) and (len(rr.registers) == y['Size'])):
                            decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, byteorder=Endian.Big, wordorder=Endian.Little)
                            decoded = OrderedDict([
                                ('string', decoder.decode_string),
                                ('bits', decoder.decode_bits),
                                ('8int', decoder.decode_8bit_int),
                                ('8uint', decoder.decode_8bit_uint),
                                ('16int', decoder.decode_16bit_int),
                                ('16uint', decoder.decode_16bit_uint),
                                ('32int', decoder.decode_32bit_int),
                                ('32uint', decoder.decode_32bit_uint),
                                ('16float', decoder.decode_16bit_float),
                                ('16float2', decoder.decode_16bit_float),
                                ('32float', decoder.decode_32bit_float),
                                ('32float2', decoder.decode_32bit_float),
                                ('64int', decoder.decode_64bit_int),
                                ('64uint', decoder.decode_64bit_uint),
                                ('ignore', decoder.skip_bytes),
                                ('64float', decoder.decode_64bit_float),
                                ('64float2', decoder.decode_64bit_float),
                            ])
                            y['Value'] = decoded[y['Type']]() * y['Scale']
                            #print ( "Register: " + y['Name'] + " = " + str(y['Value']) + " " + y['Units'])
                            #print ( f"Register: {y['Name']} = {y['Value']:.02f} {y['Units']}")
            #print("HOME")

            Rtuclient.connect()
            if CONF_SOLIS_4G_3P and Rtuclient.is_socket_open():
                if DashingEnabled:
                    Dashlog.append("Read Solis-4G inverter")
                    ui.display()
                else:
                    log.info("Read Solis-4G inverter")

                for x, z in SOLIS_Config.items():
                    if DashingEnabled:
                        Dashlog.append(f"Reading slave {z['NAME']}")
                        DashMeas1.append("")
                        DashMeas1.append(f"Reading slave {z['NAME']}")
                        ui.display()
                    else:
                        log.info(f"Reading slave {z['NAME']}")

                    MyDict = z['DATA']
                    #print (MyDict)
                    for k, y in MyDict.items(): 
                        #print(z['ADDRESS'],  y['Address'], y['Size'])
                        rr = None
                        try:
                            rr = Rtuclient.read_input_registers(y['Address'], y['Size'], unit=z['ADDRESS'])
                        except Exception as e:
                            if DashingEnabled:
                                DashErrors.append("Exception %s" % str(e))
                                ui.display()
                            else:
                                log.info("Exception %s" % str(e))
                                pass                
                        if(isinstance(rr, ReadInputRegistersResponse) and (len(rr.registers) == y['Size'])):
                            decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, byteorder=Endian.Big, wordorder=Endian.Big)
                            decoded = OrderedDict([
                                ('string', decoder.decode_string),
                                ('bits', decoder.decode_bits),
                                ('8int', decoder.decode_8bit_int),
                                ('8uint', decoder.decode_8bit_uint),
                                ('16int', decoder.decode_16bit_int),
                                ('16uint', decoder.decode_16bit_uint),
                                ('32int', decoder.decode_32bit_int),
                                ('32uint', decoder.decode_32bit_uint),
                                ('16float', decoder.decode_16bit_float),
                                ('16float2', decoder.decode_16bit_float),
                                ('32float', decoder.decode_32bit_float),
                                ('32float2', decoder.decode_32bit_float),
                                ('64int', decoder.decode_64bit_int),
                                ('64uint', decoder.decode_64bit_uint),
                                ('ignore', decoder.skip_bytes),
                                ('64float', decoder.decode_64bit_float),
                                ('64float2', decoder.decode_64bit_float),
                            ])
                            y['Value'] = decoded[y['Type']]() * y['Scale']
                            #print ( "Register: " + y['Name'] + " = " + str(y['Value']) + " " + y['Units'])
                            if DashingEnabled:
                                DashMeas1.append(f"{y['Name']} = {y['Value']:.02f} {y['Units']}")
                                ui.display()
                            #print ( f"Register: {y['Name']} = {y['Value']:.02f} {y['Units']}")
#                Rtuclient.close()
            Rtuclient2.connect()
            if CONF_JANITZA_B23 and Rtuclient2.is_socket_open():
                if DashingEnabled:
                    Dashlog.append("Read EVSE charger")
                    ui.display()
                else:
                    log.info("Read EVSE charger")

                for x, z in B23_Config.items():
                    if DashingEnabled:
                        Dashlog.append(f"Reading slave {z['NAME']}")
                        DashMeas1.append("")
                        DashMeas1.append(f"Reading slave {z['NAME']}")
                        ui.display()
                    else:
                        log.info(f"Reading slave {z['NAME']}")

                    MyDict = z['DATA']
                    #print (MyDict)
                    for k, y in MyDict.items(): 
                        #print(z['ADDRESS'],  y['Address'], y['Size'])
                        rr = None
                        try:
                            rr = Rtuclient.read_input_registers(y['Address'], y['Size'], unit=z['ADDRESS'])
                        except Exception as e:
                            if DashingEnabled:
                                DashErrors.append("Exception %s" % str(e))
                                ui.display()
                            else:
                                log.info("Exception %s" % str(e))
                                pass                
                        if(isinstance(rr, ReadInputRegistersResponse) and (len(rr.registers) == y['Size'])):
                            decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, byteorder=Endian.Big, wordorder=Endian.Big)
                            decoded = OrderedDict([
                                ('string', decoder.decode_string),
                                ('bits', decoder.decode_bits),
                                ('8int', decoder.decode_8bit_int),
                                ('8uint', decoder.decode_8bit_uint),
                                ('16int', decoder.decode_16bit_int),
                                ('16uint', decoder.decode_16bit_uint),
                                ('32int', decoder.decode_32bit_int),
                                ('32uint', decoder.decode_32bit_uint),
                                ('16float', decoder.decode_16bit_float),
                                ('16float2', decoder.decode_16bit_float),
                                ('32float', decoder.decode_32bit_float),
                                ('32float2', decoder.decode_32bit_float),
                                ('64int', decoder.decode_64bit_int),
                                ('64uint', decoder.decode_64bit_uint),
                                ('ignore', decoder.skip_bytes),
                                ('64float', decoder.decode_64bit_float),
                                ('64float2', decoder.decode_64bit_float),
                            ])
                            y['Value'] = decoded[y['Type']]() * y['Scale']
                            #print ( "Register: " + y['Name'] + " = " + str(y['Value']) + " " + y['Units'])
                            if DashingEnabled:
                                DashMeas1.append(f"{y['Name']} = {y['Value']:.02f} {y['Units']}")
                                ui.display()
                            #print ( f"Register: {y['Name']} = {y['Value']:.02f} {y['Units']}")
#                Rtuclient.close()

            #print("HOME")
            if DashingEnabled:
                bchart.append(QuerryNb)
            else:
                log.info(f"Poller querry : {QuerryNb}")
            #print ( "Querry %s" % QuerryNb)

            if (CONF_EMONCMS and CONF_SOLIS_4G_3P):
                SolarPower = 0
                for x, z in SOLIS_Config.items():
                    if Rtuclient.is_socket_open():
                        reqdata = {}
                        #print("Slave: " + z['NAME'])
                        MyDict = z['DATA']
                        #print (z['DATA'])
                        for k, y in MyDict.items():
                            #DashErrors.append(y['Name'])
                            if  (y['Name'] == 'Freq'):
                                vchart.append(50 + QuerryNb)
                            reqdata[f"{z['NAME']}{y['Name']}"] = y['Value']
                        #print('reqdata = {reqdata}')
                        req = MyEmon.senddata(reqdata)
                        reqstr = f'http://{emon_host}{emon_url}{emon_node}&json={json.dumps(reqdata)}&apikey={emon_privateKey}'

                        try:
                            r=requests.get(reqstr, timeout=10)
                            r.raise_for_status()
                        except requests.exceptions.HTTPError as errh:
                            print ("Http Error:",errh)
                        except requests.exceptions.ConnectionError as errc:
                            print ("Error Connecting:",errc)
                        except requests.exceptions.Timeout as errt:
                            print ("Timeout Error:",errt)
                        except requests.exceptions.RequestException as err:
                            print ("OOps: Something Else",err)

                        #print (r.status_code)
                        #log.info( f"EmonCMS send status {r.status_code}" )
                        if DashingEnabled:
                            Dashlog.append(f"EmonCMS slave {z['NAME']} push status {r.status_code}")
                            ui.display()
                        else:
                            log.info(f"EmonCMS slave {z['NAME']} push status {r.status_code}")
                        #print (r.content)

                    else:
                        #log.info( "EmonCMS ORNO unable to send" )
                        if DashingEnabled:
                            Dashlog.append(f"EmonCMS slave {z['NAME']} nothing to push")
                            ui.display()
                        else:
                            log.info(f"EmonCMS slave {z['NAME']} nothing to push")

            if (CONF_EMONCMS and CONF_JANITZA_B23):
                for x, z in B23_Config.items():
                    if Rtuclient2.is_socket_open():
                        reqdata = {}
                        #print("Slave: " + z['NAME'])
                        MyDict = z['DATA']
                        #print (z['DATA'])
                        for k, y in MyDict.items():
                            #DashErrors.append(y['Name'])
                            if  (y['Name'] == 'Freq'):
                                vchart.append(50 + QuerryNb)
                            reqdata[f"{z['NAME']}{y['Name']}"] = y['Value']
                        #print('reqdata = {reqdata}')
                        req = MyEmon.senddata(reqdata)
                        reqstr = f'http://{emon_host}{emon_url}{emon_node}&json={json.dumps(reqdata)}&apikey={emon_privateKey}'

                        try:
                            r=requests.get(reqstr, timeout=10)
                            r.raise_for_status()
                        except requests.exceptions.HTTPError as errh:
                            print ("Http Error:",errh)
                        except requests.exceptions.ConnectionError as errc:
                            print ("Error Connecting:",errc)
                        except requests.exceptions.Timeout as errt:
                            print ("Timeout Error:",errt)
                        except requests.exceptions.RequestException as err:
                            print ("OOps: Something Else",err)

                        #print (r.status_code)
                        #log.info( f"EmonCMS send status {r.status_code}" )
                        if DashingEnabled:
                            Dashlog.append(f"EmonCMS slave {z['NAME']} push status {r.status_code}")
                            ui.display()
                        else:
                            log.info(f"EmonCMS slave {z['NAME']} push status {r.status_code}")
                        #print (r.content)

                    else:
                        #log.info( "EmonCMS ORNO unable to send" )
                        if DashingEnabled:
                            Dashlog.append(f"EmonCMS slave {z['NAME']} nothing to push")
                            ui.display()
                        else:
                            log.info(f"EmonCMS slave {z['NAME']} nothing to push")

            if (CONF_EMONCMS and CONF_EM370):
                for x, z in EEM_Config.items():
                    if TcpClient.is_socket_open():
                        reqdata = {}
                        #print("Slave: " + z['NAME'])
                        MyDict = z['DATA']
                        #print (z['DATA'])
                        for k, y in MyDict.items():
                            #DashErrors.append(y['Name'])
                            reqdata[f"{z['NAME']}{y['Name']}"] = y['Value']
                        #print('reqdata = {reqdata}')
                        reqstr = f'http://{emon_host}{emon_url}{emon_node}&json={json.dumps(reqdata)}&apikey={emon_privateKey}'

                        try:
                            r=requests.get(reqstr, timeout=10)
                            r.raise_for_status()
                        except requests.exceptions.HTTPError as errh:
                            print ("Http Error:",errh)
                        except requests.exceptions.ConnectionError as errc:
                            print ("Error Connecting:",errc)
                        except requests.exceptions.Timeout as errt:
                            print ("Timeout Error:",errt)
                        except requests.exceptions.RequestException as err:
                            print ("OOps: Something Else",err)

                        #print (r.status_code)
                        #log.info( f"EmonCMS send status {r.status_code}" )
                        if DashingEnabled:
                            Dashlog.append(f"EmonCMS slave {z['NAME']} push status {r.status_code}")
                            ui.display()
                        else:
                            log.info(f"EmonCMS slave {z['NAME']} push status {r.status_code}")
                        #print (r.content)
                    else:
                        #log.info( "EmonCMS ORNO unable to send" )
                        if DashingEnabled:
                            Dashlog.append(f"EmonCMS slave {z['NAME']} nothing to push")
                            ui.display()
                        else:
                            log.info(f"EmonCMS slave {z['NAME']} nothing to push")
            time.sleep(5)
    except Exception as e:
        print("Exception %s" % str(e) )


class Task1(object):
    def __init__(self, interval=1):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            device_polling()


if DashingEnabled:
    Dashlog.append("Starting application")
    ui.display()
else:
    log.info("Starting application")

DevicePollerTask = Task1()

while True:
    time.sleep(1)
    if DashEnabled:
        dash_frontend()

