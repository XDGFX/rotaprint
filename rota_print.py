#!/usr/bin/env python

# Main script for running the TDCA rotary printer.

# Copyright (C) Callum Morrison - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Callum Morrison, 2020

import serial
import time


def get_args():
    import argparse

    desc = "Print on cylindrical components!"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('gcode', type=str, help='Input GCODE file')
    parser.add_argument('length', type=float,
                        help='Length of part to print on')
    parser.add_argument('radius', type=float,
                        help='Radius of part to print on')
    parser.add_argument(
        '-c', '--com', type=str, help='Serial port to connect to. See: bit.ly/2U8aFvV',
        default='grbl-1.1h/ttyGRBL')

    args = parser.parse_args()

    return args


def gcode_load(path):
    gcode = list()  # Initiate gcode variable

    # Load file and convert lines to list variable
    with open(path, "r") as f:
        for line in f:
            if not line.strip() == "":  # Remove blank lines completely
                gcode.append(line.strip())
    return gcode


def g0_g1_conversion(gcode):
    printing = 0

    for idx, command in enumerate(gcode):
        if command.startswith("G1 F"):
            # Start of printing
            printing = 1
        elif command.startswith("G0 F"):
            # End of printing
            printing = 0

        if printing:
            gcode[idx] = command[:1] + "1" + command[2:]  # Replace G0 with G1
    return gcode


def gcode_send(data):
    print("Sending: " + data.strip())
    data = data.strip() + "\n"  # Strip all EOL characters for consistency
    s.write(data.encode())  # Send g-code block to grbl

    grbl_out = s.readline().decode().strip()
    print(grbl_out)


# Get input arguments
args = get_args()
# Connect to serial
s = serial.Serial(args.com, 115200)

s.write("\r\n\r\n".encode())  # Wake up grbl
time.sleep(2)  # Wait for grbl to initialize
s.flushInput()  # Flush startup text in serial input


# Load selected gcode file into list
gcode = gcode_load(args.gcode)
# Convert commands where printing to G1 to indicate printing
#gcode = g0_g1_conversion(gcode)

for command in gcode:
    gcode_send(command)

# Write to output file for testing purposes
# with open("output.gcode", "w+") as f:
#     for command in gcode:
#         f.write("%s\n" % command)
