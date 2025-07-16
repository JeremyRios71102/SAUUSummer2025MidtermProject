import psutil
import time
import sys

# Named Pipe Output
sys.stdout = open('data', 'w', buffering = 1)

while True:
    # Network Throughput (Data Out per Second)
    start = psutil.net_io_counters()
    time.sleep(1)
    finish = psutil.net_io_counters()
    # CPU
    print("CPU Percent: " + str(psutil.cpu_percent(1)) + "%" )
    # Memory
    print("Memory Percent: " + str(psutil.virtual_memory().percent) + "%")
    # Disk
    print("Disk Usage: " + str(psutil.disk_usage('/').percent) + "%")
    # IO
    print("IO Write: " + str(psutil.disk_io_counters().write_bytes) + " Bytes")
    print("IO Read: " + str(psutil.disk_io_counters().read_bytes) + " Bytes")
    # Network
    print("Network Throughput: " + str(finish.bytes_sent - start.bytes_sent) + " B/s")
