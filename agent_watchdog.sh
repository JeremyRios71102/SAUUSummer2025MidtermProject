#!/usr/bin/env bash

SERVICE="agent.service"
MONITOR_SCRIPT="/replace/with/path"
MONITOR_LOG="/var/log/monitor_watchdog.log"

# Check agent systemd service, if not, restart
if ! systemctl is-active --quiet "$SERVICE"; then
    echo "$(date --iso-8601=seconds) $SERVICE was down, restarting..." >> /var/log/agent_watchdog.log
    systemctl restart "$SERVICE"
fi

# Check if monitor.py is running, if not, restart
if ! pgrep -f "python3.*monitor.py" > /dev/null; then
    echo "$(date --iso-8601=seconds) monitor.py was down, restarting..." >> "$MONITOR_LOG"
    nohup python3 "$MONITOR_SCRIPT" >> /var/log/monitor_output.log 2>&1 &
fi
