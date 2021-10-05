#!/bin/bash

for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do

        syspath="${sysdevpath%/dev}"
        devname="$(udevadm info -q name -p $syspath)"
        if [[ "$devname" == bus/* ]]
          then
            continue
        fi
        eval "$(udevadm info -q property --export -p $syspath)"
        [[ -z "$ID_SERIAL" ]] && continue
        echo "/dev/$devname ;-; $ID_VENDOR ;-; $ID_MODEL ;-; $ID_SERIAL"

done
