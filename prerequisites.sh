#!/bin/bash

# Upgrade pip
pip install --upgrade pip
 
# Install required packages
pip install flask requests ncclient paramiko lxml
# sqlite3 is included with Python standard library, no pip install needed