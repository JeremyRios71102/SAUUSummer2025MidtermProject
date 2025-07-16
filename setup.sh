#!/bin/bash

# Named Pipe
mkfifo data

# User/Group
useradd -m PyApi

# Change Named Piped File Ownership + Permissions
chown PyApi:PyApi data
chmod 660 data

# Import Python API
API="agent.py"

# Change Python API Ownership + Permissions
chown PyApi:PyApi $API
chmod 440 $API
chmod 440 monitor.py

# Move to PyApi 
mv data /home/PyApi
mv $API /home/PyApi
mv monitor.py /home/PyApi
