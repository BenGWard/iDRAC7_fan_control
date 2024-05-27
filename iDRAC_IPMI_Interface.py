import logging
import subprocess
import sys
import time

STALE_DATA_TIMEOUT_SECONDS = 1

class IpmiInterface:
    def __init__(self):
        self.automaticMode = True
        self.logger = logging.getLogger(__name__)
        self.temperatureTable = ""
        self.temperatureTableTime = 0.0

    def SetFanPercent(self,percentage):
        if self.automaticMode:
            self.SetManual()

        subprocess.run(["ipmitool", "raw", "0x30", "0x30", "0x02", "0xFF", hex(max(min(int(percentage), 100), 0))], stdout=subprocess.PIPE)

    def SetManual(self):
        self.logger.info("Setting to manual control.")
        self.automaticMode = False
        subprocess.run(["ipmitool", "raw", "0x30", "0x30", "0x01", "0x00"], stdout=subprocess.PIPE)

    def SetAutomatic(self):
        self.logger.info("Setting to automatic control.")
        self.automaticMode = True
        subprocess.run(["ipmitool", "raw", "0x30", "0x30", "0x01", "0x01"], stdout=subprocess.PIPE)

    def GetProcessor1Temperature(self):
        return self.GetTemperature("0Eh")

    def GetProcessor2Temperature(self):
        return self.GetTemperature("0Fh")

    def GetInletTemperature(self):
        return self.GetTemperature("04h")

    def GetExhaustTemperature(self):
        return self.GetTemperature("01h")

    def GetMaximumProcessorTemperature(self):
        return max(self.GetProcessor1Temperature(), self.GetProcessor2Temperature())

    def GetTemperature(self, identifier):
        temperature = 0

        for line in self.GetTemperatureTable().splitlines():
            if identifier in line:
                temperature = int(line.split("|")[-1].strip("degrees C"))

        return temperature

    def GetTemperatureTable(self):
        if (time.time_ns() - self.temperatureTableTime) > (STALE_DATA_TIMEOUT_SECONDS * 1000000000.0):
            self.temperatureTable = subprocess.run(["ipmitool", "sdr", "type", "temperature"], stdout=subprocess.PIPE).stdout.decode()
            self.temperatureTableTime = time.time_ns()
        
        return self.temperatureTable

    def GetAverageFanRPM(self):
        count = 0
        sum = 0

        for line in self.GetFanRPMTableLines():
            count = count + 1
            rpm = int(line.split("|")[-1].strip("RPM"))
            sum = sum + rpm

        return sum / count

    def GetFanRPMTableLines(self):
        table = subprocess.run(["ipmitool", "sdr", "type", "fan"], stdout=subprocess.PIPE).stdout.decode()
        return [line for line in table.splitlines() if "RPM" in line ]

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    impi = IpmiInterface()
    print(impi.GetTemperatureTable())
    print(f"Processor 1: {impi.GetProcessor1Temperature()}")
    print(f"Processor 2: {impi.GetProcessor2Temperature()}")
    print(f"Inlet: {impi.GetInletTemperature()}")
    print(f"Exhaust: {impi.GetExhaustTemperature()}")
    print(f"Max Processor: {impi.GetMaximumProcessorTemperature()}")
    print(f"Fan RPM: {impi.GetAverageFanRPM()}")

    choice = "b"

    while choice != "E":
        choice = input("[A]uto, [M]anual, [P]ercent [E]xit: ").upper()[0]

        if choice == "A":
            impi.SetAutomatic()
        elif choice == "M":
            impi.SetManual()
        elif choice == "P":
            percent = input("Enter Percent: ")
            impi.SetFanPercent(float(percent))