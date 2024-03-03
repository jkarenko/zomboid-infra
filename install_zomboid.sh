#!/bin/bash

./steamcmd.sh +login anonymous +force_install_dir /opt/zomboid +app_update 380870 validate +quit
echo 'Project Zomboid installed.'
