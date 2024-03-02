#!/bin/bash
echo 'Updating packages...'
sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386
sudo apt update
echo 'Downloading steamcmd...'
sudo apt install steamcmd -y
./steamcmd.sh +login anonymous +force_install_dir /opt/zomboid +app_update 380870 validate +quit
echo 'Project Zomboid installed.'
