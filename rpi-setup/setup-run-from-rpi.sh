#!/bin/bash

# Set the fountain python program to start as a service
sudo cp fountain.service /etc/systemd/system/fountain.service
sudo systemctl daemon-reload
sudo systemctl enable fountain.service
sudo systemctl start fountain.service
sudo systemctl status fountain.service

