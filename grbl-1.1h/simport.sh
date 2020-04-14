#!/bin/bash

# Prompt for sudo and execute as root
(( EUID != 0 )) && exec sudo -- "$0" "$@"

# Change directory to script location
cd $(dirname "$0")

FAKETTY=ttyGRBL
GRBLSIM="./grbl_sim.exe"

# Kill the socat process running in background
trap "ctrl_c" 2
ctrl_c() {
  printf "\nTerminating grbl-sim.\n"
  for child in $(jobs -p); do
    kill $child
  done
  exit
}

if [ ! -e $GRBLSIM ];then
  printf "Build grbl-sim with 'make' first.\nIf the output is not named $GRBLSIM this script needs to be updated.\n"
  exit
fi

socat PTY,raw,link=$FAKETTY,echo=0 "EXEC:'$GRBLSIM -n -r 0.01 -s step.out -b block.out',pty,raw,echo=0"&

# Wait for socat to setup the link then change permission
sleep 1
chmod a+rw $FAKETTY

printf "grbl-sim running on $FAKETTY\n"
printf "Press [CTRL+C] to stop.\n"

while true
do
  sleep 100
done