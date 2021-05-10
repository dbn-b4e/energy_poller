# Imports
import requests
import json
import time


# from emoncms import Myemon
# MyEmon = Myemon(emon_host, emon_url, emon_privateKey, emon_node)
# MyEmon.senddata(reqdata)

class Myemon(object):

    def __init__(self, emon_host, emon_url, emon_privateKey, emon_node):
        self.emon_host          = emon_host
        self.emon_url           = emon_url
        self.emon_privateKey    = emon_privateKey
        self.emon_node          = emon_node
        self.emon_base_url      = 'http://{}{}{}'.format(self.emon_host,self.emon_url,self.emon_node ) + '&json={'
        self.reqstr             = ''

    def senddata(self, reqdata):
        self.reqstr = self.emon_base_url + json.dumps(reqdata) + '}&apikey=' + '{}'.format(self.emon_privateKey )
        self.reqstr=self.reqstr.replace(" ", "")
        print('Sending: {}'.format(self.reqstr))
        
        for attempt in range(10):
            try:
                r=requests.get(self.reqstr, timeout=10)
                r.raise_for_status()
                return r.status_code

            except requests.exceptions.HTTPError as errh:
                print ("Http Error:",errh)
            except requests.exceptions.ConnectionError as errc:
                print ("Error Connecting:",errc)
            except requests.exceptions.Timeout as errt:
                print ("Timeout Error:",errt)
            except requests.exceptions.RequestException as err:
                print ("OOps: Something Else",err)
            else:
                break


