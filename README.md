# Cloud-Based Linux Server Performance Remote Dashboard

**Midterm project for COP3604 – System Administration using UNIX**\
**Group Members:** \
**Instructor:** Dr. Christian Navarro

## Project Overview

This project implements a complete, cloud-based Linux server performance monitoring solution. Each group member deploys a personal GCP-hosted Linux VM, which is stress-tested and monitored in real-time by a custom-built remote dashboard hosted on a separate server.

The dashboard visualizes key system metrics (CPU, memory, disk usage, disk i/o, and network traffic), issues alerts when thresholds are exceeded, and handles real-time and historical data collection.

## Features

- Real-Time Dashboard: Live graphs for all monitored metrics using Plotly Dash
- Historical Data: Metrics are logged per-VM and saved to CSV
- Alerts and Notifications: Customizable thresholds with UI warnings
- Agent Auto-Restart: Cron job ensures agent recovery if it fails
- Secure Access: API endpoints are locked to specific IPs via firewalld
- Named Pipes: Agent uses FIFO-based communication internally (Linux IPC)
- Stress-ng Automation: Custom Bash script stress-tests CPU, IO, memory, filesystem, and VM
- Dashboard Server: Fully separated Oracle-hosted VM to prevent interference from stress loads

## System Architecture

Each member deploys a VM running:

- `stress-ng` via a systemd service
- A custom Flask-based metrics API
- A named pipe (`/tmp/metrics`) for IPC between collectors and the agent
- A cron watchdog for failure handling

A separate VM hosts the Dash dashboard, which polls the VMs over HTTP, aggregates the metrics, logs them, and displays live/historical charts.

## Metrics Monitored

- CPU Usage (%)
- Memory Usage (%)
- Disk Usage (%)
- Disk I/O (bytes)
- Network Throughput (bytes)

## Getting Started

## Alerts

You can adjust thresholds using the sliders in the UI. Alerts are triggered if usage exceeds thresholds for more than 30 seconds. They show up in red with timestamped messages.

## Security

Each agent restricts access to its API using `firewalld`:

## Auto-Restart (Failure Handling)

A cron job on each VM runs every 5 minutes:

```bash
*/5 * * * * /home/user/check_agent.sh
```

If the agent process is dead, it restarts it using `systemctl`.

## Team Contributions

## Screenshots

See the `report/screenshots/` folder for examples of the live dashboard, alert system, and stress-ng results.

## Video Demo

One-minute demonstration includes:

- Live dashboard
- Stress load in action
- Agent failure and automatic recovery

File location: `report/video.mp4`

## References

- [stress-ng Wiki](https://wiki.ubuntu.com/Kernel/Reference/stress-ng)
- [psutil Python Docs](https://psutil.readthedocs.io/)
- [Plotly Dash Docs](https://dash.plotly.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## Future Work

- Add container support (Dockerized monitoring)
- Expand metrics to GPU or thermal sensors
- Enable dynamic VM discovery from config

