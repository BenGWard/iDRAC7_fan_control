import argparse
import datetime
import logging
import os
import signal
import sys
import time

import iDRAC_IPMI_Interface

LOG_DIRECTORY="./logs/"

MINIMUM_PROCESSOR_TEMP = 30
MAXIMUM_MANUAL_PROCESSOR_TEMP = 65
POLLING_INTERVAL_SECONDS = 3.0
FAN_PERCENT_FLOOR = 5.0
FAN_PERCENT_STEP = 3

PROPORTIONAL_GAIN = 1.1
INTEGRAL_GAIN = 0.0
DERIVATIVE_GAIN = 5.0

def ExitHandler(signalNumber, stackFrame):
    logger = logging.getLogger(__name__)
    iDRAC_IPMI_Interface.IpmiInterface().SetAutomatic()
    logger.debug(f"Signal Number: {signal.Signals(signalNumber).name} - Stack: {stackFrame}")
    logger.info("Exiting.")
    logging.shutdown()
    sys.exit(0)

def SetupLogger(verbose):
    if not os.path.exists(LOG_DIRECTORY):
        os.mkdir(LOG_DIRECTORY)

    logLevel = logging.INFO
    logHandlers = [
        logging.FileHandler(
            filename=datetime.datetime.now().strftime(f"{LOG_DIRECTORY}fancontrol.service.%Y_%b_%d_%H_%M_%S.log"),
            mode='w')
    ]
    
    if verbose:
        logLevel = logging.DEBUG
        logHandlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
       handlers=logHandlers,
       level=logLevel,
       format='%(asctime)s %(levelname)-8s %(message)s',
       datefmt='%Y-%m-%d %H:%M:%S')

# Keep a list of previous commanded percentages
# Use last few to decide up / down command
    
def main():
    logger = logging.getLogger(__name__)
    logger.info("Starting.")
    ipmi = iDRAC_IPMI_Interface.IpmiInterface()

    previousError = MINIMUM_PROCESSOR_TEMP
    previousCommandedFanPercent = 0
    integral = 0

    while True:
        processorTemp = ipmi.GetMaximumProcessorTemperature()

        if processorTemp < MAXIMUM_MANUAL_PROCESSOR_TEMP:
            error = processorTemp - MINIMUM_PROCESSOR_TEMP
            #proportionalPortion = error
            #integral = integral + error * POLLING_INTERVAL_SECONDS
            #derivativePortion = (error - previousError) / POLLING_INTERVAL_SECONDS
            #previousError = error
            # absolute value the deriviative portion to slope up faster and down slower?
            # commandedFanPercent = int(FAN_PERCENT_FLOOR + PROPORTIONAL_GAIN * proportionalPortion + INTEGRAL_GAIN * integral + abs(DERIVATIVE_GAIN * derivativePortion))
            commandedFanPercent = int(FAN_PERCENT_FLOOR + PROPORTIONAL_GAIN * error)
            
            #if commandedFanPercent != previousCommandedFanPercent:
            if abs(commandedFanPercent - previousCommandedFanPercent) > FAN_PERCENT_STEP:
                previousCommandedFanPercent = commandedFanPercent
                ipmi.SetFanPercent(commandedFanPercent)
                logger.info(f"Temp: {processorTemp} - Fan: {commandedFanPercent} %")
        else:
            logger.info(f"Temp: {processorTemp} exceededs {MAXIMUM_MANUAL_PROCESSOR_TEMP} threshold.")
            ipmi.SetAutomatic()
        time.sleep(POLLING_INTERVAL_SECONDS)

# class RecordKeeper:
#     def __init__(self, size):
#         self._list = []

#         for i in range(size):
#             self._list.append(MAXIMUM_MANUAL_PROCESSOR_TEMP)

#     def AddTemperature(self, temperature):
#         for i in range(len(self._list) - 1, 0, -1):
#             self._list[i] = self._list[i - 1]

#         self._list[0] = temperature

#     def GetGreatestSlope(self):
#         currentTemp = self._list[0]
#         greatestSlope = 0

#         for i in range(1, len(self._list)):
#             slopeI = (currentTemp - self._list[i]) / i
#             if slopeI > greatestSlope:
#                 greatestSlope = slopeI

#         return greatestSlope


# def main():
#     logger = logging.getLogger(__name__)
#     logger.info("Starting.")
#     ipmi = iDRAC_IPMI_Interface.IpmiInterface()
#     records = RecordKeeper(5)
#     previousCommandedFanPercent = 0

#     while True:
#         processorTemp = ipmi.GetMaximumProcessorTemperature()

#         if processorTemp < MAXIMUM_MANUAL_PROCESSOR_TEMP:
#             records.AddTemperature(processorTemp)
#             temperatureError = processorTemp - MINIMUM_PROCESSOR_TEMP
#             commandedFanPercent = int(FAN_PERCENT_FLOOR + PROPORTIONAL_GAIN * (temperatureError + records.GetGreatestSlope()))
#             logger.debug(f"Calculated Temp: {processorTemp + records.GetGreatestSlope()} - Temp Error: {temperatureError} - Temp Slope: {records.GetGreatestSlope()}")
            
#             if commandedFanPercent != previousCommandedFanPercent:
#                 previousCommandedFanPercent = commandedFanPercent
#                 ipmi.SetFanPercent(commandedFanPercent)
#                 logger.info(f"Temp: {processorTemp} - Fan: {commandedFanPercent} %")
#         else:
#             logger.info(f"Temp: {processorTemp} exceededs {MAXIMUM_MANUAL_PROCESSOR_TEMP} threshold.")
#             ipmi.SetAutomatic()
#         time.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Control fans for Dell PowerEdge servers.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Writes debug level log to file and standard out.")
    args = parser.parse_args()
    SetupLogger(args.verbose)

    # Register Handlers
    signal.signal(signal.SIGINT, ExitHandler)
    signal.signal(signal.SIGTERM, ExitHandler)

    # logging.getLogger().info("Test 2")

    main()