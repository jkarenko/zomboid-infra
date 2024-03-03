#!/bin/bash
echo 'Updating packages...'
sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386 -y
sudo apt update -y
echo 'Downloading steamcmd...'
sudo apt install steamcmd -y
echo 'Stemcmd installed.'
