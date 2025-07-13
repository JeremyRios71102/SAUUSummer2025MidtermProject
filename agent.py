#!/usr/bin/env python3
"""
This python script contains the API/agents that will collect the system statistics from the
Ubuntu 24.02 virtual machine from Google Cloud Console, and send those statistics to our website
which will display the statistics graphically.

Setup

Before you run this script, be sure to do the following on your virtual machine:
Install any package updates and Python 3 and dependencies
sudo apt update && sudo apt install python3-pip -y
pip install psutil fastapi uvicorn

Then, run the code:
sudo -u python3 agent.py
Note: You can alternatively create a system service file if you would like to start the program
on bootup.
"""
#Required Libraries and Frameworks
import os
import time
import json
import shutil
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import OrderedDict

#Configuration
SAMPLE_INTERVAL = 5 #Time (in seconds) between each data collection
HTTP_PORT = 5000 #Load program at a specific port
PIPE_PATH = "/tmp/sysmon_pipe" #A basic FIFO for other users
PRIMARY_DISK = "sda" #Change the rootdisk to the one you're using if needed
PRIMARY_IFACE = None #None is used to auto-detect which interface to use

#Low Level Helpers - these functions collect the data manually instead of using psutil

#Returns the first line of the file
def _read_first_line(path):
    with open(path, "r") as f:
        return f.readline()

#Returns the CPU times from /proc/stat
def _read_proc_stat():
    return list(map(int, _read_first_line("/proc/stat").split()[1:]))

#Returns the percentage of used memory with a precision of two decimals.
def _memory_usage():
    m = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, v, *_ = line.split()
            m[k.rstrip(":")] = int(v)
    total = m["MemTotal"] * 1024
    free = (m["MemFree"] + m["Buffers"] + m["Cached"]) * 1024
    used = total - free
    return round(used / total * 100, 2)

#Returns the percentage of disk usage with a precision of two decimals.
def _disk_usage(path="/"):
    total, used, _ = shutil.disk_usage(path)
    return round(used / total * 100, 2)

#This will map out block devices to a tuple
def _diskstats():
    s ={}
    with open("/proc/diskstats") as f:
        for line in f:
            _, _, name, *vals = line.split()
            s[name] = (int(vals[2]), int(vals[6]))
        return s

#Returns mapping interface from /proc/net/dev
def _netdev():
    d = {}
    with open("/proc/net/dev") as f:
        for line in f:
            if ':' not in line:
                continue
            iface, rest = line.split(':', 1)
            vals = list(map(int, rest.split()))
            d[iface.strip()] = (vals[0], vals[8])
    return d

#This will pick the best possible interface heuristically
def _detect_iface():
    for iface in _netdev():
        if iface not in ("lo", "docker0"):
            return iface
    raise RuntimeError("There are no suitable network interfaces found. Please try again later. If problems persist, check your network configuration")

#Sampler Thread (background) - The sampler will collect metrics from the background so HTTP requests are served instantly
class Sampler(threading.Thread):
    def __init__(self, interval=SAMPLE_INTERVAL):
        super().__init__(daemon=True)
        self.interval = interval
        self.current = {}

        #Initializations of counters to be used in delta calculations
        self._prev_cpu = _read_proc_stat()
        self._prev_disk = _diskstats()
        self._prev_net = _netdev()

        #Ensures a basic data pipe is only created once
        if not os.path.exists(PIPE_PATH):
            os.mkfifo(PIPE_PATH)

    def run(self):
        global PRIMARY_IFACE
        if PRIMARY_IFACE is None:
            PRIMARY_IFACE = _detect_iface()

        while True:
            start = time.time()

            #CPU
            cpu_now = _read_proc_stat()
            delta = [b - a for a, b in zip(self._prev_cpu, cpu_now)]
            idle, total = delta[3] + delta[4], sum(delta)
            cpu_pct = 0.0 if total == 0 else 100 * (total - idle) / total
            self._prev_cpu = cpu_now

            #Disk I/O in B/s
            disk_now = _diskstats() [PRIMARY_DISK]
            rd, wr = disk_now
            prev_rd, prev_wr = self._prev_disk[PRIMARY_DISK]
            disk_bps = ((rd - prev_rd) + (wr - prev_wr)) * 512 / self.interval
            self._prev_disk = _diskstats()

            #Net Throughput B/s
            net_now = _netdev() [PRIMARY_IFACE]
            rx, tx = net_now
            prev_rx, prev_tx = self._prev_net[PRIMARY_IFACE]
            net_bps = ((rx - prev_rx) + (tx - prev_tx)) / self.interval
            self._prev_net = _netdev()

            #Sample Assembly
            sample = OrderedDict([
                ("cpu", round(cpu_pct, 2)),
                ("memory", _memory_usage()),
                ("disk", _disk_usage("/")),
                ("diskio", round(disk_bps, 2)),
                ("net", round(net_bps, 2)),
            ])

            #Save the new results of the metrics
            self.current = sample

            #This write command will be written to FIFO so 'tail -f' can be used to read the most recent entires.
            try:
                with open(PIPE_PATH, "w") as fifo:
                    fifo.write(json.dumps(sample) + "\n")
            except BrokenPipeError:
                #Occurs when no reader is attached.
                pass

            #Sleep until next statistic collection occurs.
            time.sleep(max(0, self.interval - (time.time() - start)))

#HTTP Handler
class MetricsHandler(BaseHTTPRequestHandler):
    #Generates the results in a JSON file to be sent to the dashboard.
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(sampler.current).encode())
        else:
            self.send_error(404)

    def log_message(self, *_):
        pass

#Main function
if __name__ == '__main__':
    #The main program that requests the statistic and to send them to the dashboard.
    sampler = Sampler(); sampler.start()
    print(f" [agent] ∆{SAMPLE_INTERVAL}s | /metrics on :{HTTP_PORT} | fifo {PIPE_PATH}")
    try:
        HTTPServer(("0.0.0.0", HTTP_PORT), MetricsHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nExiting...")
