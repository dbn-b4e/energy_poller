import minimalmodbus
import socket
import serial

###		PROGRAM FLOW:
###			- Collect Data from Solis-4G inverter
###			- Convert to individual bytes
###			- Construct 2 messages 
###				- KWH Totals only sent when inverter is running, so they are not reset to zero
###				- All other 'live' data set to zero when inverter shuts down
###			- Send Packets to EMONHUB
###	
###		EmonHub Node IDs:
###			- NodeID 3: All time energy KWH	/ Today KWH (not sent overnight)
###			- NodeID 4: Live Data Readings - Zeros sent overnight 


### COLLECT DATA FROM SOLIS-4G INVERTER ###

instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1) # port name, slave address 

instrument.serial.baudrate = 9600   # Baud
instrument.serial.bytesize = 8
instrument.serial.parity   = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout  = 0.5   # seconds

success = False # Intialise Success/Failure Flag to ensure full data is only uploaded if all data is received.

try:
	Realtime_ACW = instrument.read_long(3004, functioncode=4, signed=False)	#Read AC Watts as Unsigned 32-Bit 
	print('AC power', Realtime_ACW,'W')

	Realtime_DCW = instrument.read_long(3006, functioncode=4, signed=False)	#Read AC Watts as Unsigned 32-Bit 
	print('DC power', Realtime_DCW,'W')

	print('Efficiency:', Realtime_ACW/Realtime_DCW*100.0)

	AlltimeEnergy_KW = instrument.read_long(3008, functioncode=4, signed=False) # Read All Time Energy (KWH Total) as Unsigned 32-Bit 
	print('Total energy', AlltimeEnergy_kWh, 'kWh')


	# Year_kWh = instrument.read_register(3017, functioncode=4, signed=False)	#Read AC Watts as Unsigned 32-Bit 
	# Month_kWh = instrument.read_register(3011, functioncode=4, signed=False)	#Read AC Watts as Unsigned 32-Bit 
	# Today_kWh = instrument.read_register(3014, functioncode=4, signed=False)	#Read AC Watts as Unsigned 32-Bit 


	# Realtime_AC_A = instrument.read_register(3033, functioncode=4, signed=False) #Read AC Current as Unsigned 16-Bit
	# Realtime_AC_B = instrument.read_register(3034, functioncode=4, signed=False) #Read AC Current as Unsigned 16-Bit
	# Realtime_AC_C = instrument.read_register(3035, functioncode=4, signed=False) #Read AC Current as Unsigned 16-Bit
	# Realtime_ACI_A = instrument.read_register(3036, functioncode=4, signed=False) #Read AC Current as Unsigned 16-Bit
	# Realtime_ACI_B = instrument.read_register(3037, functioncode=4, signed=False) #Read AC Current as Unsigned 16-Bit
	# Realtime_ACI_C = instrument.read_register(3038, functioncode=4, signed=False) #Read AC Current as Unsigned 16-Bit
	# Inverter_C = instrument.read_register(3041, functioncode=4, signed=True) #Read Inverter Temperature as Signed 16-Bit

	# Realtime_DC_V1 = instrument.read_register(3020, functioncode=4, signed=False) #Read DC Volts as Unsigned 16-Bit
	# Realtime_DC_V2 = instrument.read_register(3022, functioncode=4, signed=False) #Read DC Volts as Unsigned 16-Bit
	# Realtime_DC_I1 = instrument.read_register(3021, functioncode=4, signed=False) #Read DC Volts as Unsigned 16-Bit
	# Realtime_DC_I2 = instrument.read_register(3023, functioncode=4, signed=False) #Read DC Volts as Unsigned 16-Bit

	# #GridFreq = instrument.read_register(3041, functioncode=4, signed=True) #Read Inverter Temperature as Signed 16-Bit


	

	# print('Year energy', Year_kWh, 'kWh')
	# print('Month energy', Month_kWh, 'kWh')
	# print('Today energy', Today_kWh/10.0, 'kWh')

	# print('VAC-A', Realtime_AC_A/10.0, 'V')
	# print('VAC-B', Realtime_AC_B/10.0, 'V')
	# print('VAC-C', Realtime_AC_C/10.0, 'V')
	# print('AC-A current', Realtime_ACI_A/10.0, 'A')
	# print('AC-B current', Realtime_ACI_B/10.0, 'A')
	# print('AC-C current', Realtime_ACI_C/10.0, 'A')
	# print('Inverter Temp', Inverter_C/10.0, 'C')
	# print('DC String 1:', Realtime_DC_V1/10.0, 'V -', Realtime_DC_I1/10.0, 'A')
	# print('DC String 2:', Realtime_DC_V2/10.0, 'V -', Realtime_DC_I2/10.0, 'A')
	# #print('Grid frequency:', GridFreq/100.0, 'Hz')


	# Realtime_DCV = instrument.read_register(3021, numberOfDecimals=0, functioncode=4, signed=False) #Read DC Volts as Unsigned 16-Bit
	
	# Realtime_DCI = instrument.read_register(3022, numberOfDecimals=0, functioncode=4, signed=False) #Read DC Current as Unsigned 16-Bit
	# Realtime_ACI = instrument.read_register(3038, numberOfDecimals=0, functioncode=4, signed=False) #Read AC Current as Unsigned 16-Bit
	# Realtime_ACF = instrument.read_register(3042, numberOfDecimals=0, functioncode=4, signed=False) #Read AC Frequency as Unsigned 16-Bit
	
	# Inverter_C = instrument.read_register(3041, numberOfDecimals=0, functioncode=4, signed=True) #Read Inverter Temperature as Signed 16-Bit
	

	success = True

except:
	##EXCEPTION WILL OCCUR WHEN INVERTER SHUTS DOWN WHEN PANELS ARE OFF
	print('No response from slave...')
	A1 = 0
	A2 = 0
	A3 = 0
	A4 = 0

	## Not sent when inverter turns off
	## B1 = 0
	## B2 = 0
	## B3 = 0
	## B4 = 0
	
	## C1 = 0
	## C2 = 0
	## END NOT SENT WHEN INVERTER TURNS OFF

	D1 = 0
	D2 = 0
	
	E1 = 0
	E2 = 0

	F1 = 0
	F2 = 0

	G1 = 0
	G2 = 0

	H1 = 0
	H2 = 0
	
	I1 = 0
	I2 = 0	
	
	##Flag to stream restricted data to EmonHub
	success = False

### END COLLECT DATA FROM SOLIS-4G INVERTER ###

	
### STREAM RESULT TO EMONHUB ###
#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Initialise Socket
# s.connect(('localhost', 8080)) #Connect to Local EmonHub

# ## NOT SENT WHEN INVERTER TURNS OFF
# if success == True:
# 	s.sendall('03 ' + str(B1) + ' ' + str(B2) + ' ' + str(B3) + ' ' + str(B4) + ' ' + str(C1) + ' ' + str(C2) + '\r\n')

# s.sendall('04 ' + str(A1) + ' ' + str(A2) + ' ' + str(A3) + ' ' + str(A4) + ' ' + str(D1) + ' ' + str(D2) + ' ' + str(E1) + ' ' + str(E2) + ' ' + str(F1) + ' ' + str(F2) + ' ' + str(G1) + ' ' + str(G2) + ' ' + str(H1) + ' ' + str(H2) + ' ' + str(I1) + ' ' + str(I2) + '\r\n')
# s.close()