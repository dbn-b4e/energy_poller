
#!/usr/bin/env python3

import sys
import os
import argparse
import json


def noprint(*args, **kwargs):
    pass 

verbmsg = noprint
infomsg = print


LUT_TYPE = {
	'uint8'  : {'mbsize': 1, 'altname': '8uint'},
	'uint16' : {'mbsize': 1, 'altname': '16uint'},
	'uint32' : {'mbsize': 2, 'altname': '32uint'},
	'uint64' : {'mbsize': 4, 'altname': '64uint'},
	'int8'   : {'mbsize': 1, 'altname': '8int'},
	'int16'  : {'mbsize': 1, 'altname': '16int'},
	'int32'  : {'mbsize': 2, 'altname': '32int'},
	'int64'  : {'mbsize': 4, 'altname': '64int'},
	'float'  : {'mbsize': 2, 'altname': '32float'},
}


def getkeyval(d:dict, key:str, default):
	if key in d:
		return d[key]
	else:
		return default


if __name__ == '__main__':
	retcode = 0

	# Args parser config
	parser = argparse.ArgumentParser()
	parser.add_argument('jsonmap', help='Modbus JSON map')
	parser.add_argument('-v', '--verbose', help='Print more info', action='store_true')
	parser.add_argument('-q', '--quiet', help='Don\'t print anything', action='store_true')
	args = parser.parse_args()

	# Parse args
	if args.verbose:
		verbmsg = print
		infomsg = print
	if args.quiet:
		verbmsg = noprint
		infomsg = noprint

	jsonmap = {}
	with open(args.jsonmap, 'r') as fd:
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
				rdesc  = getkeyval(r, '$description,', f'reg{counter}')
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
				else:
					rsize  = 1

				reg = {
					'Name'    : rdesc,
					'Address' : f'0x{raddr:04X}',
					'Type'    : rsize,
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

	infomsg(json.dumps(reglist, indent='  '))