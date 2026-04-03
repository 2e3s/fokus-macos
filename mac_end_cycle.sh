#!/bin/bash

sleep 3

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit

month=$(date '+%Y-%m')
day=$(date '+%d')
logfile="logs/$month/$day.txt"
mkdir -p "logs/$month"

if [ -f "$logfile" ]; then
    lines=$(wc -l < "$logfile" | tr -d ' ')
else
    lines=0
fi

lines=$((lines+1))

report=$(osascript \
    -e 'tell application "System Events"' \
    -e 'activate' \
    -e 'set theResponse to display dialog "What have you done in this focus?" default answer "" with title "Pomodoro report"' \
    -e 'text returned of theResponse' \
    -e 'end tell' 2>/dev/null)

if [ -n "$report" ]; then
    echo "$lines) $report" >> "$logfile"
fi

sleep 1

if [ -f "$logfile" ]; then
    logs=$(cat "$logfile")

    osascript -e 'on run argv' \
              -e 'tell application "System Events"' \
              -e 'activate' \
              -e 'display dialog (item 1 of argv) with title "Pomodoro Report" buttons {"Close"} default button "Close" giving up after 10' \
              -e 'end tell' \
              -e 'end run' \
              "$logs"
fi
