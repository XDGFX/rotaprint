#!/usr/bin/env python

# Main script for running the TDCA rotary printer.

# Copyright (C) Callum Morrison - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Callum Morrison <callum.morrison@mac.com>, 2020

import serial
import time
import re


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

    f.close()
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


def send_status_query():
    s.write('?'.encode())


def periodic_timer():
    while is_run:
        send_status_query()
        time.sleep(report_interval)


class grbl:
    """
    Full control and configuration of grbl firmware and connection.
    """

    # GRBL settings (see: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration)
    g0 = 10       # Length of step pulse, microseconds
    g1 = 255      # Step idle delay, milliseconds
    # g2 = 0        # Step port invert, mask
    g3 = 0        # Direction port invert, mask
    g4 = 0        # Step enable invert, boolean
    g5 = 0        # Limit pins invert, boolean
    # g6 = 0        # Probe pin invert, boolean
    # g10 = 1       # Status report, mask
    # g11 = 0.010   # Junction deviation, mm
    # g12 = 0.002   # Arc tolerance, mm
    # g13 = 0       # Report inches, boolean
    g20 = 1       # Soft limits, boolean
    # g21 = 0       # Hard limits, boolean
    g22 = 1       # Homing cycle, boolean
    g23 = 0       # Homing dir invert, mask
    g24 = 25      # Homing feed, mm/min
    g25 = 500     # Homing seek, mm/min
    g26 = 25      # Homing debounce, milliseconds
    # g27 = 1       # Homing pull-off, mm
    # g30 = 1000    # Max spindle speed, RPM
    # g31 = 0       # Min spindle speed, RPM
    g32 = 1       # Laser mode, boolean
    # ---
    g100 = 250    # X steps/mm
    g101 = 250    # Y steps/mm  !!!VARIES
    g102 = 250    # Z steps/mm
    g110 = 500    # X Max rate, mm/min
    g111 = 500    # Y Max rate, mm/min
    g112 = 500    # Z Max rate, mm/min
    g120 = 10     # X Acceleration, mm/sec^2
    g121 = 10     # Y Acceleration, mm/sec^2
    g122 = 10     # Z Acceleration, mm/sec^2
    g130 = 200    # X Max travel, mm  !!!VARIES
    g131 = 200    # Y Max travel, mm  !!!VARIES
    g132 = 200  # Z Max travel, mm
    

    def __init__(self):
        

        self.send()


    def send(self, data, verbose, check_mode):
        l_count = 0
        error_count = 0
        start_time = time.time()
        if settings_mode:
            # Send settings file via simple call-response streaming method. Settings must be streamed
            # in this manner since the EEPROM accessing cycles shut-off the serial interrupt.
            print("SETTINGS MODE")
            for line in data:

                l_count += 1  # Iterate the line counter
                l_block = line.strip()  # Strip all EOL characters for consistency

                if verbose:
                    print("SND>"+str(l_count)+": \"" + l_block + "\"")

                s.write((l_block + '\n').encode())  # Send g-code block to grbl

                while 1:
                    # Wait for grbl response with carriage return
                    grbl_out = s.readline().strip().decode()

                    if grbl_out.find('ok') >= 0:
                        if verbose:
                            print("  REC<"+str(l_count)+": \""+grbl_out+"\"")
                        break

                    elif grbl_out.find('error') >= 0:
                        if verbose:
                            print("  REC<"+str(l_count)+": \""+grbl_out+"\"")
                        error_count += 1
                        break

                    else:
                        print("    MSG: \"" + grbl_out + "\"")
        else:
            # Send g-code program via a more agressive streaming protocol that forces characters into
            # Grbl's serial read buffer to ensure Grbl has immediate access to the next g-code command
            # rather than wait for the call-response serial protocol to finish. This is done by careful
            # counting of the number of characters sent by the streamer to Grbl and tracking Grbl's
            # responses, such that we never overflow Grbl's serial read buffer.
            g_count = 0
            c_line = []
            for line in data:
                l_count += 1  # Iterate line counter

                # Strip comments/spaces/new line and capitalize
                l_block = re.sub(r'\s|\(.*?\)', '', line).upper()

                # Track number of characters in grbl serial read buffer
                c_line.append(len(l_block) + 1)
                grbl_out = ''

                while sum(c_line) >= rx_buffer_size - 1 | s.inWaiting():
                    out_temp = s.readline().strip().decode()  # Wait for grbl response

                    if out_temp.find('ok') < 0 and out_temp.find('error') < 0:
                        print("    MSG: \""+out_temp+"\"")  # Debug response

                    else:
                        if out_temp.find('error') >= 0:
                            error_count += 1

                        g_count += 1  # Iterate g-code counter

                        if verbose:
                            print("  REC<"+str(g_count)+": \""+out_temp+"\"")

                        # Delete the block character count corresponding to the last 'ok'
                        del c_line[0]

                data_to_send = l_block + '\n'
                s.write(data_to_send.encode())  # Send g-code block to grbl

                if verbose:
                    print("SND>" + str(l_count) + ": \"" + l_block + "\"")

            # Wait until all responses have been received.
            while l_count > g_count:
                out_temp = s.readline().strip().decode()  # Wait for grbl response

                if out_temp.find('ok') < 0 and out_temp.find('error') < 0:
                    print("    MSG: \""+out_temp+"\"")  # Debug response

                else:
                    if out_temp.find('error') >= 0:
                        error_count += 1

                    g_count += 1  # Iterate g-code counter

                    if verbose:
                        print("  REC<"+str(g_count)+": \""+out_temp + "\"")

                    # Delete the block character count corresponding to the last 'ok'
                    del c_line[0]

        end_time = time.time()
        print(" Time elapsed: ", end_time-start_time, "\n")

        if check_mode:
            if error_count > 0:
                print("CHECK FAILED:", error_count,
                      "errors found! See output for details.\n")
            else:
                print("CHECK PASSED: No errors found in g-code program.\n")
        else:
            print(
                "WARNING: Wait until Grbl completes buffered g-code blocks before exiting.")
            input("  Press <Enter> to exit and disable Grbl.")


# Get input arguments
args = get_args()

# Connect to serial
s = serial.Serial(args.com, 115200)

print("Connecting to printer...")
s.write("\r\n\r\n".encode())  # Wake up grbl
time.sleep(2)  # Wait for grbl to initialize
s.flushInput()  # Flush startup text in serial input


# --- SETTINGS ---

# GCODE parser settings
settings_mode = False  # Default, must be True for settings
rx_buffer_size = 128
enable_status_reports = True  # Default True, can toggle monitoring
report_interval = 1.0  # In seconds, if enable_status_reports is True


# Load selected gcode file into list
gcode = gcode_load(args.gcode)
# Convert commands where printing to G1 to indicate printing
# gcode = g0_g1_conversion(gcode)

is_run = True  # Turns on monitoring
grbl.send(gcode, True, True, False)
is_run = False  # Turns off monitoring

# Close serial port
s.close()
