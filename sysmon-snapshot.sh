#!/usr/bin/env bash
set -euo pipefail

# conservative PATH for cron (change directory to whichever you use.)
PATH=/home/jeremyrios711/sysmon

URL="${SYS_MON_URL:-http://127.0.0.1:5000/metrics}"
LOG="${SYS_MON_LOG:-/var/log/sysmon/metrics-snapshots.log}"
LOCKFILE="${SYS_MON_LOCK:-/run/sysmon-snapshot.lock}"

# ensure dirs exist (ignore errors if already exist)
mkdir -p "$(dirname "$LOG")" /run || true

# single-writer lock to avoid clobber when overlapping cron runs
exec 9>"$LOCKFILE"
if ! flock -w 5 9; then
  echo "[$(date --iso-8601=seconds)] sysmon-snapshot: could not acquire lock." >&2
  exit 1
fi

TS="$(date --iso-8601=seconds)"

# Fetch metrics; on failure, log an error line so gaps are visible in history.
if METRICS="$(curl -fsS "$URL" 2>/dev/null)"; then
  printf '%s %s\n' "$TS" "$METRICS" >>"$LOG"
else
  printf '%s %s\n' "$TS" '{"error":"metrics_unavailable"}' >>"$LOG"
  echo "[$TS] sysmon-snapshot: curl failed for $URL" >&2
fi

exit 0
