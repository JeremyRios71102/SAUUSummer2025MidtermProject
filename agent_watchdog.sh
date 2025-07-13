#!/usr/bin/env bash
# agent_watchdog.sh - cron job that checks service status every 5 minutes, and restarts it if any
# problems occur

SERVICE="agent.service"

if ! Systemctl is-active --quiet "$SERVICE"; then
	echo "$(date - Is) $SERVICE was down, restarting..." > /var/log/agent_watchdog.log
	systemctl restart "$SERVICE"
Fi