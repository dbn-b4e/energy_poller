
#!/usr/bin/env python3

import sys
import os
import json


def noprint(*args, **kwargs):
    pass 

verbmsg = noprint
infomsg = print


LUT_TYPE = {
	'uint8'  	: {'mbsize': 1, 'altname': '8uint'},
	'uint16' 	: {'mbsize': 1, 'altname': '16uint'},
	'uint32' 	: {'mbsize': 2, 'altname': '32uint'},
	'uint64' 	: {'mbsize': 4, 'altname': '64uint'},
	'int8'   	: {'mbsize': 1, 'altname': '8int'},
	'int16'  	: {'mbsize': 1, 'altname': '16int'},
	'int32'  	: {'mbsize': 2, 'altname': '32int'},
	'int64'  	: {'mbsize': 4, 'altname': '64int'},
	'float32'  	: {'mbsize': 2, 'altname': '32float'},
}


def getkeyval(d:dict, key:str, default = None):
	if key in d:
		return d[key]
	else:
		return default


def generate_device_dict(jsonfile:str) -> dict:

	jsonmap = {}
	with open(jsonfile, 'r') as fd:
		jsonmap = json.loads(fd.read())
	
	verbmsg(f'jsonmap = ')
	verbmsg(json.dumps(jsonmap, indent='  '))
	verbmsg('')

	reglist = {}
	for s in jsonmap['sections']:
		sname  = s['name']
		soff   = s['address']
		sinst  = s['instance']
		sisize = s['isize']
		counter = 0
		for i in range(s['instance']):
			for r in s['regs']:
				if r['name'].startswith('_'):
					continue
				counter = counter + 1
				rname  = getkeyval(r, 'name', f'reg{counter}')
				rdesc  = getkeyval(r, 'description', f'reg{counter}')
				roff   = getkeyval(r, 'offset', 0)
				rtype  = getkeyval(r, 'type', 'uint16')
				rfact  = getkeyval(r, 'fact', 1)
				rexp   = getkeyval(r, 'exp', 0)
				runit  = getkeyval(r, 'unit', '')
				rdef   = getkeyval(r, 'default', 0)
				raddr  = soff + (i * sisize) + roff
				rscale = rfact * (10**rexp)
				if rtype in LUT_TYPE:
					rsize = LUT_TYPE[rtype]['mbsize']
					rtype = LUT_TYPE[rtype]['altname']
				else:
					rsize  = 1

				reg = {
					'Name'    : rdesc,
					'Address' : raddr,
					'Type'    : rtype,
					'Size'    : rsize,
					'Units'   : runit,
					'Scale'   : rscale,
					'Value'   : rdef,
				}

				reglist[rname] = reg
			# end for r
		# end for i
	# end for s

	verbmsg('reglist = ')
	verbmsg(reglist)
	verbmsg('')

	return reglist