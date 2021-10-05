"""A class for scanning and identifying the connected instruments.
    
   The definition of all known instrument types and how we expect them to
   appear in the USB/Serial Linux devices is also contained in this file.

   This uses the output of scan_usb_v2.sh script, which can be executed on a
   target to see what instruments are present, for debug purposes. If the
   list given by scan_usb_v2.sh is not as expected, this script will also fail.
   You can also run this script directly, which will run the detection
   and print the results in the console, which is again useful for debugging.

   List of known instruments that we scan for:

    * Tenma 72-2550: vendor is 'USB_Vir_USB_Virtual_COM', model starts with 'NT*'
    * RF Explorer:   vendor is 'Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller', model is '0001'
    * Xenon 1900:    vendor is 'Honeywell_Imaging___Mobility', model is '1900'
    * EY-001:        vendor is '1a86', model is 'NEWTOLOGIC'
    * Metrologic:    vendor is 'Metrologic', model is ' Metrologic_Scanner'
    * BK2831E:       vendor is 'Silicon_Labs_2831E_Multimeter', model is '0001'
    * Nexxtender Testbench Consoles:
                     vendor = 'FTDI', model = 'Quad_RD232-HS'
    * TD1204 Cable:  vendor is 'FTDI', model is 'TTL232R-3V3'

   Instruments that we don't (yet) need to scan:

    * SEGGER Jlink
    * Keysight 34465A (uses USBTMC and we specify VID and PID when connecting)
    * Zebra Label Printers
"""

import subprocess
import os

class InstrumentIdentity(object):
    def __init__(self, dev_path='', vendor='', model='', serial=''):
        self.serial = serial
        self.vendor = vendor
        self.model = model
        self.dev_path = dev_path

    def identify(self):
        """ Identify the instrument

            Returns a string that identifies the instrument, based on information
            that was scanned in the USB device tree. Each instrument has specific conditions
            that we can check on vendor, model and serial. The exact conditions are determined
            on a case-by-case basis.

            Returns 'Unknown' if the instrument matches none of the known instruments.
        """
        if self.vendor == 'Honeywell_Imaging___Mobility' and self.model == '1900':
            return 'Xenon 1900'
        if self.vendor == 'Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller':
            if self.model == '0001':
                return 'RF Explorer'
        if self.vendor == 'USB_Vir':
            if self.model == 'USB_Virtual_COM':
                return 'Tenma 72-2550'
        if '2831E_Multimeter' in self.vendor:
            return 'BK2831E'
        if self.vendor == '1a86' and self.model == 'NEWTOLOGIC':
            return 'EY-001'
        if self.vendor == 'Metrologic' and self.model == 'Metrologic_Scanner':
            return 'Metrologic'
        if self.vendor == 'FTDI' and self.model == 'Quad_RS232-HS':
            return 'Nexxtender Testbench Consoles'
        if self.vendor == 'FTDI' and self.model == 'TTL232R-3V3':
            return 'TD1204 Programmer'
        if self.vendor == 'FTDI' and self.model == 'FT232R_USB_UART':
            return 'TD1204 Programmer'
        if self.vendor == 'Silicon_Labs' and self.model == 'CP2108_Quad_USB_to_UART_Bridge_Controller':
            return 'Nexxtender Home Testboard Consoles'
        if self.vendor == 'Silicon_Labs' and 'PWD-031' in self.model:
            return 'Powerdale Debugger Console'
        if 'POWERDALE_RTU-IO_REV' in self.model:
            return 'Powerdale RS-485 ITF'

        return 'Unknown'

class DeviceScanner(object):
    def __init__(self):
        pass

    def scan(self):
        instruments = []
        this_dir = os.path.dirname(os.path.realpath(__file__))
        scan_result = subprocess.check_output([os.path.join(this_dir, 'scan_usb_v2.sh'),])

        if scan_result:
            for line in scan_result.decode('utf-8').strip().split('\n'):
                try:
                    (dev_path, vendor, model, serial) = line.split(' ;-; ')
                    if '/dev/usb/' not in dev_path:
                        instruments.append(InstrumentIdentity(dev_path, vendor, model, serial))
                except ValueError:
                    print("Error: no instruments found, or bad data")
        else:
            print("Error: no instruments found")
        return instruments

    def find_instrument(self, instrument_name):
        print("DeviceScanner: find instrument %s" % instrument_name)
        instruments = self.scan()
        #for i in instruments:
        #    print("Instrument: vendor = %s; model = %s; serial = %s; dev_path = %s" % (i.vendor, i.model, i.serial, i.dev_path)) 
        return [x for x in instruments if x.identify() == instrument_name]

    def find_instrument_by_class(self, instrument_class):
        print("DeviceScanner: find instrument class %s" % instrument_class)
        instruments = self.scan()
        #for i in instruments:
        #    print("Instrument: vendor = %s; model = %s; serial = %s; dev_path = %s" % (i.vendor_string, i.model, i.serial, i.dev_path))

        if instrument_class == "QRCode Scanner":
            return [x for x in instruments if x.identify() in ['EY-001', 'Xenon 1900', 'Metrologic']]

    def find_instrument_devpath(self, instrument_name):
        """Returns a list of device paths that match the given instrument names
           
           It's always a list, even if there's a single element.
        """
        instruments = self.find_instrument(instrument_name)
        if instruments:
            if len(instruments) == 1:
                print("Found %s on path %s" % (instrument_name, instruments[0].dev_path))
            else:
                print("Warning: found multiple elligible %s instruments, returning all" % (instrument_name))
            return [x.dev_path for x in instruments]

    def find_instrument_devpath_by_class(self, instrument_class):
        """Returns a list of device paths that match the given instrument class
           
           It's always a list, even if there's a single element.
        """
        instruments = self.find_instrument_by_class(instrument_class)
        if instruments:
            if len(instruments) == 1:
                print("Found %s on path %s" % (instruments[0].identify, instruments[0].dev_path))
            else:
                print("Warning: found multiple elligible %s instruments, returning all" % (instrument_class))
            return [x.dev_path for x in instruments]

if __name__ == '__main__':
    import argparse

    args_parser = argparse.ArgumentParser(description='Testbench Device Scanner')
    args_parser.add_argument('-d', '--device_type', help='Filter for a particular device type')
    args_parser.add_argument('-c', '--device_class', help='Filter for a particular device class')
    args = args_parser.parse_args()

    scanner = DeviceScanner()

    if args.device_type:
        for i in scanner.find_instrument(args.device_type):
            print("Identified Instrument with vendor = %s, model = %s; serial = %s; dev_path = %s: %s" % (i.vendor, i.model, i.serial, i.dev_path, i.identify()))
    elif args.device_class:
        for i in scanner.find_instrument_by_class(args.device_class):
            print("Identified Instrument of Class %s with vendor = %s, model = %s; serial = %s; dev_path = %s: %s" % (args.device_class, i.vendor, i.model, i.serial, i.dev_path, i.identify()))
    else:
        for i in scanner.scan():
            print("Identify Instrument with vendor = %s, model = %s; serial = %s; dev_path = %s: %s" % (i.vendor, i.model, i.serial, i.dev_path, i.identify()))
