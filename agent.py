#!/usr/bin/env python3
"""
agent.py – lightweight HTTP agent that reads the latest metrics sample
emitted by monitor.py through the named pipe /tmp/sysmon_pipe and exposes it
via /metrics in the exact JSON schema expected by the dashboard:

    {
        "cpu": <float>,    # % CPU usage (2‑dp)
        "memory": <float>, # % RAM used (2‑dp)
        "disk": <float>,   # % rootfs used (2‑dp)
        "diskio": <float>, # aggregate read+write B/s (2‑dp)
        "net": <float>     # network throughput B/s (2‑dp)
    }

Running both of these processes is required:
    $ python3 monitor.py   # writes metrics to the FIFO
    $ python3 agent.py     # serves the /metrics endpoint on port 5000

Ubuntu 24.02 (terminal‑only) | Google Cloud Console
"""
import json
import os
import re
import time
import threading
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict

PIPE_PATH = "/tmp/sysmon_pipe"
HTTP_PORT = 5000

#This is the format used by monitor.py to collect the data, the format will change for the JSON file
_PATTERNS: dict[str, re.Pattern[str]] = {
    "cpu":      re.compile(r"CPU Percent:\s*([\d.]+)"),
    "memory":   re.compile(r"Memory Percent:\s*([\d.]+)"),
    "disk":     re.compile(r"Disk Usage:\s*([\d.]+)"),
    "io_write": re.compile(r"IO Write:\s*(\d+)"),
    "io_read":  re.compile(r"IO Read:\s*(\d+)"),
    "net":      re.compile(r"Network Throughput:\s*([\d.]+)"),
}

#These are the number of lines used by the given data from monitor.py
_LINES_PER_SAMPLE = 6


class PipeReader(threading.Thread):
    #Continuously reads the FIFO and keeps the most recent sample.
    def __init__(self, pipe_path: str = PIPE_PATH) -> None:
        super().__init__(daemon=True)
        self.pipe_path = pipe_path
        self.current: Dict[str, float] = OrderedDict([
            ("cpu", 0.0),
            ("memory", 0.0),
            ("disk", 0.0),
            ("diskio", 0.0),
            ("net", 0.0),
        ])

        self._prev_io_total: int | None = None
        self._prev_ts: float | None = None

        #If a FIFO does not exist, a new one will be created.
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)

    #Helper functions
    @staticmethod
    def _parse_block(lines: list[str]) -> dict[str, str] | None:
        #This helper will extract the information given by monitor.py
        parsed: dict[str, str] = {}
        for key, regex in _PATTERNS.items():
            for ln in lines:
                m = regex.search(ln)
                if m:
                    parsed[key] = m.group(1)
                    break
            if key not in parsed:  #Will return nothing if the field is blank.
                return None
        return parsed

    def _process_block(self, lines: list[str]) -> None:
        #This helper wiLl process the given info to fit into the five attributes used by the dashboard
        data_raw = self._parse_block(lines)
        if not data_raw:
            return  #If there is no data, return nothing.

        try:
            #Assigns variable types to each given data value.
            cpu_pct = float(data_raw["cpu"])
            mem_pct = float(data_raw["memory"])
            disk_pct = float(data_raw["disk"])
            io_write = int(data_raw["io_write"])
            io_read = int(data_raw["io_read"])
            net_bps  = float(data_raw["net"])
        except ValueError:
            return  #Malformed numbers will be ignored.

        #This portion will calculate the value for the diskio attribute.
        now = time.time()
        io_total = io_write + io_read
        if self._prev_io_total is not None and self._prev_ts is not None:
            delta_bytes = io_total - self._prev_io_total
            delta_t     = max(now - self._prev_ts, 1e-6)
            diskio_bps  = delta_bytes / delta_t
        else:
            diskio_bps = 0.0

        self._prev_io_total = io_total
        self._prev_ts       = now

        #Reformatted monitor.py data to be used by the dashboard.
        self.current = OrderedDict([
            ("cpu",    round(cpu_pct, 2)),
            ("memory", round(mem_pct, 2)),
            ("disk",   round(disk_pct, 2)),
            ("diskio", round(diskio_bps, 2)),
            ("net",    round(net_bps, 2)),
        ])

    #This loop will create the pipe which will process the data to the dashboard.
    def run(self) -> None:
        while True:
            try:
                with open(self.pipe_path, "r") as fifo:
                    buffer: list[str] = []
                    for line in fifo:
                        line = line.strip()
                        if not line:
                            continue
                        buffer.append(line)
                        if len(buffer) == _LINES_PER_SAMPLE:
                            self._process_block(buffer)
                            buffer.clear()
            except (FileNotFoundError, OSError):
                #If the pipes haven't been opened yet or if there's no statistics, we retry every half-second.
                time.sleep(0.5)

#HTTP communication
class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        #This will send the system metrics over to the dashboard. It will send 404 if there's an error.
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(reader.current).encode())
        else:
            self.send_error(404)

    def log_message(self, *_):  #This will remove the default log noise.
        pass

#Main function
def main() -> None:
    global reader
    reader = PipeReader()
    reader.start()

    print(f"[agent] /metrics on :{HTTP_PORT} | fifo {PIPE_PATH}")
    try:
        HTTPServer(("0.0.0.0", HTTP_PORT), MetricsHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nExiting…")


if __name__ == "__main__":
    main()