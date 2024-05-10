import subprocess

def SetFanPercent(percentage):
    subprocess.run(["ipmitool", "raw", "0x30", "0x30", "0x02", "0xFF", hex(int(percentage))], stdout=subprocess.PIPE)

def SetManual():
    print("Setting to manual control.")
    subprocess.run(["ipmitool", "raw", "0x30", "0x30", "0x01", "0x00"], stdout=subprocess.PIPE)

def SetAutomatic():
    print("Setting to automatic control.")
    subprocess.run(["ipmitool", "raw", "0x30", "0x30", "0x01", "0x01"], stdout=subprocess.PIPE)

def GetProcessor1Temperature(temperatureTable = None):
    if temperatureTable is None:
        temperatureTable = GetTemperatureTable()

    return GetTemperature("0Eh", temperatureTable)

def GetProcessor2Temperature(temperatureTable = None):
    if temperatureTable is None:
        temperatureTable = GetTemperatureTable()

    return GetTemperature("0Fh", temperatureTable)

def GetInletTemperature(temperatureTable = None):
    if temperatureTable is None:
        temperatureTable = GetTemperatureTable()

    return GetTemperature("04h", temperatureTable)

def GetExhaustTemperature(temperatureTable = None):
    if temperatureTable is None:
        temperatureTable = GetTemperatureTable()

    return GetTemperature("01h", temperatureTable)

def GetMaximumProcessorTemperature():
    table = GetTemperatureTable()
    return max(GetProcessor1Temperature(table), GetProcessor2Temperature(table))

def GetTemperature(identifier, temperatureTable):
    temperature = 0

    for line in temperatureTable.splitlines():
        if identifier in line:
            temperature = int(line.split("|")[-1].strip("degrees C"))

    return temperature

def GetTemperatureTable():
    return subprocess.run(["ipmitool", "sdr", "type", "temperature"], stdout=subprocess.PIPE).stdout.decode()

def GetAverageFanRPM():
    count = 0
    sum = 0

    for line in GetFanRPMTableLines():
        count = count + 1
        rpm = int(line.split("|")[-1].strip("RPM"))
        sum = sum + rpm

    return sum / count

def GetFanRPMTableLines():
    table = subprocess.run(["ipmitool", "sdr", "type", "fan"], stdout=subprocess.PIPE).stdout.decode()
    return [line for line in table.splitlines() if "RPM" in line ]


if __name__ == '__main__':
    print(GetTemperatureTable())
    print(f"Processor 1: {GetProcessor1Temperature()}")
    print(f"Processor 2: {GetProcessor2Temperature()}")
    print(f"Inlet: {GetInletTemperature()}")
    print(f"Exhaust: {GetExhaustTemperature()}")
    print(f"Max Processor: {GetMaximumProcessorTemperature()}")
    print(f"Fan RPM: {GetAverageFanRPM()}")

    choice = "b"

    while choice != "E":
        choice = input("[A]uto, [M]anual, [P]ercent [E]xit: ").upper()[0]

        if choice == "A":
            SetAutomatic()
        elif choice == "M":
            SetManual()
        elif choice == "P":
            percent = input("Enter Percent: ")
            SetFanPercent(float(percent))