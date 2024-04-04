#!/bin/bash

# Variables
IDRAC_IP="IP address of iDRAC"
IDRAC_USER="user"
IDRAC_PASSWORD="passowrd"
INTERVAL_SEC=5
INITIAL_START_DELAY_SEC=60
MAX_MANUAL_FAN=40

#IPMITOOL=ipmitool -I lanplus -H $IDRAC_IP -U $IDRAC_USER -P $IDRAC_PASSWORD
IPMITOOL=ipmitool

TEMP_THRESHOLD=65
#TEMP_SENSOR="04h"   # Inlet Temp
#TEMP_SENSOR="01h"  # Exhaust Temp
TEMP_SENSOR="0Eh"  # CPU 1 Temp
#TEMP_SENSOR="0Fh"  # CPU 2 Temp

FCTRL=0 #disabled, enabled=1
LAST_PCT=0


toggle() {
    $IPMITOOL raw 0x30 0x30 0x01 $1 2>&1 >/dev/null
}

reset_manual() {
    echo "Setting Control To Automatic"
    toggle 0x01
    FCTRL=0 #disabled
}

set_manual() {
    echo "Setting Control To Manual"
    toggle 0x00
    FCTRL=1 #enabled
}

graceful_exit() {
    reset_manual
    exit 0
}

trap graceful_exit SIGINT SIGTERM


# need the reset in case the system boots up with the last set value
reset_manual

#start delay
sleep $INITIAL_START_DELAY_SEC


while [ 1 ]
do

    # Get temperature from iDARC.
    T=$($IPMITOOL sdr type temperature 2>/dev/null | grep $TEMP_SENSOR | cut -d"|" -f5 | cut -d" " -f2)

    # If temperature is above TEMP_THRESHOLD C enable dynamic control and exit, if below set manual control.
    if [[ $T -ge $TEMP_THRESHOLD ]]
    then
        if [[ $FCTRL -ne 0 ]]
        then
            reset_manual
        fi
    else
        
        # This gives a fan percent that is a multiple of 5, up to MAX_MANUAL_FAN
        PCT=$((((T * 20 * MAX_MANUAL_FAN) / (TEMP_THRESHOLD * 100) + 1) * 5))
        # Min PCT Allowed is 10
        PCT=$(( PCT < 10 ? 10 : PCT ))
        
        if [[ $LAST_PCT -ne $PCT ]]
        then
            if [[ $FCTRL -eq 0 ]]
            then
                set_manual
            fi

            echo "Temp:" $T "- Fan %" $PCT
            PCTHEX=$(printf '0x%02x' $PCT)
            $IPMITOOL raw 0x30 0x30 0x02 0xff $PCTHEX 2>&1 >/dev/null
            LAST_PCT=$PCT
        fi
    fi
    
    sleep $INTERVAL_SEC
done
