3/5 Metrics Implemented so Far

import psutil
import time
import subprocess
# Need to Update PIDOF for More Command Variations
stressPID = list(map(int, subprocess.check_output(["pidof", "stress-ng-hdd"]).decode().split()))

# Monitor Indefinately 
while True:
    cpu = []
    memory = []
    io = []
    net = []
    disk = []
    for pid in stressPID:
        # Identify Specific Process
        process = psutil.Process(pid)
        # Sometimes Garbage Values are Recorded
        # We Ignore These
        if (process.cpu_percent(interval=1) != 0):
            # Add Each Benchmark to the Lists According to PID
            cpu.append(process.cpu_percent(interval=1))
            memory.append(process.memory_percent())
            io.append(process.io_counters()[3])
    # Timer
    time.sleep(3)
    # Average Benchmarks of all Stress Processes
    print("CPUdisk Percent Average: " + str(float(sum(cpu)/len(cpu))) + "%")
    print("Memory Percent Average: " + str(float(sum(memory)/len(memory))) + "%")
    print("I/O Write Average: " + str(float(sum(io)/len(io))) + " Bytes")
