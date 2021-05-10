ss
0. Setup
pip3 install -r requirements.txt

1. Open both modbus_defs.xlsx and modbus_devices.xlsx
(in case of renammed files, un-hide the __Config tab in modbus_devices.xlsx, then adapt the target file replacing modbus_defs.xlsx)

2. Edit section and devices, then save


3. List available section and devices

$ ./mapgen.py modbus_defs_dbnpoller.xlsx modbus_devices_dbnpoller.xlsx -l

============
SECTION LIST

ID   (dec)     Name                     # Version
--------------------------------------------------
0x01 (1)       __InfoHeader             1
0x02 (2)       __SectionList            1
0x0A (10)      EEM_MA370                1
0x0B (11)      OR_WE_514_part1          1
0x0C (12)      OR_WE_514_part2          1

===========
DEVICE LIST

OR_WE_514



4. Show device info
$ ./mapgen.py modbus_defs_dbnpoller.xlsx modbus_devices_dbnpoller.xlsx -d OR_WE_514 -i

===========
DEVICE INFO

OR_WE_514
> Name                 = or_we_514
> Default Output       = or_we_514-v1-1_1.json
> HW rev               = v1 - None
> MB map               = 1 - 1
> Section              = 2/2

   MBADDR    NAME                                   MODE    EXTRA
------------------------------------------------------------------------------------------
===
SEC    304    OR_WE_514_part1_v1 (0x0B,0x01)         R       size=1*41=41
REG    304    Freq                                   R       size=1    unit=0.01 Hz
REG    305    Vrms                                   R       size=1    unit=0.01 V
REG    306    _stub                                  R       size=7    unit=1
REG    313    Irms                                   R       size=2    unit=0.001 A
REG    315    _stub                                  R       size=5    unit=1
REG    320    APwr                                   R       size=2    unit=1 W
REG    322    _stub                                  R       size=6    unit=1
REG    328    RPwr                                   R       size=2    unit=1 var
REG    330    _stub                                  R       size=6    unit=1
REG    336    SPwr                                   R       size=2    unit=1 VA
REG    338    _stub                                  R       size=6    unit=1
REG    344    PF                                     R       size=1    unit=0.001
===
SEC  40960    OR_WE_514_part2_v1 (0x0C,0x01)         R       size=1*2=2
REG  40960    Energy                                 R       size=2    unit=0.01 kWh

5. Generate device mapping
$ ./mapgen.py modbus_defs_dbnpoller.xlsx modbus_devices_dbnpoller.xlsx -d OR_WE_514

Generate mapping 'or_we_514-v1-1_1.json' from device definition 'OR_WE_514'


6. Use the mapping file
$ ./testmap.py or_we_514-v1-1_1.json
