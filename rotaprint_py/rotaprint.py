#!/usr/bin/env python
"""
Main script for running the TDCA rotary printer.

Copyright (C) Callum Morrison - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Callum Morrison <callum.morrison@mac.com>, 2020
"""

import serial
import time
import re
import threading
import logging


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
        '-p', '--port', type=str, help='Serial port to connect to. See: bit.ly/2U8aFvV',
        default='grbl-1.1h/ttyGRBL')
    parser.add_argument('-v', '--verbose',
                        help='Show verbose information', action='store_true')
    parser.add_argument('-d', '--debug',
                        help='Show debug information', action='store_true')
    parser.add_argument(
        '-c', '--check', help='Check GCODE only, do not run', action='store_true')

    args = parser.parse_args()
    return args


class websocket:
    def __init__(self):
        # Create thread to run websocket.listen as a daemon (in background)
        timerThread = threading.Thread(target=self.listen)
        timerThread.daemon = True
        timerThread.start()

    def listen(self):
        import asyncio
        import websockets

        async def listen(websocket, path):
            while True:
                message = await websocket.recv()
                log.debug(f'WEBSOCKET > {message}')

        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(listen, 'localhost', 8765)

        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()


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


class grbl:
    """
    Full control and configuration of grbl firmware and connection.
    """

    # GRBL settings (see: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration)
    settings = {
        "$0": 10,       # Length of step pulse, microseconds
        "$1": 255,      # Step idle delay, milliseconds
        # "$2": 0,        # Step port invert, mask
        "$3": 0,        # Direction port invert, mask
        "$4": 0,        # Step enable invert, boolean
        "$5": 0,        # Limit pins invert, boolean
        # "$6": 0,        # Probe pin invert, boolean
        # "$10": 1,       # Status report, mask
        # "$11": 0.010,   # Junction deviation, mm
        # "$12": 0.002,   # Arc tolerance, mm
        # "$13": 0,       # Report inches, boolean
        "$20": 0,       # Soft limits, boolean !!! Should be enabled for real use
        # "$21": 0,       # Hard limits, boolean
        "$22": 1,       # Homing cycle, boolean
        "$23": 0,       # Homing dir invert, mask
        "$24": 25,      # Homing feed, mm/min
        "$25": 500,     # Homing seek, mm/min
        "$26": 25,      # Homing debounce, milliseconds
        # "$27": 1,       # Homing pull-off, mm
        # "$30": 1000,    # Max spindle speed, RPM
        # "$31": 0,       # Min spindle speed, RPM
        "$32": 1,       # Laser mode, boolean
        # ---
        "$100": 250,    # X steps/mm
        "$101": 250,    # Y steps/mm  !!!VARIES
        "$102": 250,    # Z steps/mm
        "$110": 500,    # X Max rate, mm/min
        "$111": 500,    # Y Max rate, mm/min
        "$112": 500,    # Z Max rate, mm/min
        "$120": 10,     # X Acceleration, mm/sec^2
        "$121": 10,     # Y Acceleration, mm/sec^2
        "$122": 10,     # Z Acceleration, mm/sec^2
        "$130": 200,    # X Max travel, mm  !!!VARIES
        "$131": 200,    # Y Max travel, mm  !!!VARIES
        "$132": 200  # Z Max travel, mm
    }

    startup = {
        "$N0": ""  # GCODE to run on every startup of grbl
    }

    def __init__(self):
        pass

    def connect(self):
        log.info("Connecting to printer...")
        try:
            # Connect to serial
            s = serial.Serial(args.port, 115200)
            s.write("\r\n\r\n".encode())  # Wake up grbl
            time.sleep(2)  # Wait for grbl to initialize
            s.flushInput()  # Flush startup text in serial input

        except Exception:
            log.error("Unable to connect to printer", exc_info=True)
            quit()

        return s

    def send_settings(self):
        log.info("Checking if firmware settings need updating...")
        log.debug("GRBL < $$")

        s.write("$$".encode())
        s.write("\n".encode())
        s.write("\n".encode())

        # while True:
        #     print(s.readline().strip().decode())

        # if args.verbose:
        #     print("Sending settings to firmware...")

        # temp_settings = list()

        # for key in self.settings:
        #     temp_settings.append(key + "=" + str(self.settings[key]))

        # self.send(temp_settings, True)

    def home(self):
        s.write('$H\n'.encode())
        log.debug("GRBL < $H")

    def send_status_query(self):
        log.debug("Sending status query...")
        log.debug("GRBL < ?")
        s.write('?'.encode())

    def periodic_timer(self):
        while True:
            if is_run:
                self.send_status_query()
            time.sleep(report_interval)

    def monitor(self):
        if enable_status_reports:
            timerThread = threading.Thread(target=self.periodic_timer)
            timerThread.daemon = True
            timerThread.start()

    def check_mode(self):
        log.debug('Enabling grbl check-mode...')
        log.debug("GRBL < $C")
        s.write('$C\n')

        while True:
            grbl_out = s.readline().strip()  # Wait for grbl response with carriage return
            if grbl_out.find('error') >= 0:
                log.debug(f"GRBL > {grbl_out}")
                log.error("Failed to set Grbl check-mode. Aborting...")
                quit()
            elif grbl_out.find('ok') >= 0:
                log.debug(f'GRBL > {grbl_out}')
                break

    def send(self, data, settings_mode=False):
        l_count = 0
        error_count = 0
        start_time = time.time()
        if settings_mode:
            # Send settings file via simple call-response streaming method. Settings must be streamed
            # in this manner since the EEPROM accessing cycles shut-off the serial interrupt.

            log.debug("Settings mode")

            for line in data:
                l_count += 1  # Iterate the line counter
                l_block = line.strip()  # Strip all EOL characters for consistency

                log.debug("GRBL < "+str(l_count)+": \"" + l_block + "\"")

                # Send g-code block to grbl
                s.write((l_block + '\n').encode())

                while 1:
                    # Wait for grbl response with carriage return
                    grbl_out = s.readline().strip().decode()

                    if grbl_out.find('ok') >= 0:

                        log.debug("GRBL > "+str(l_count)+": \""+grbl_out+"\"")
                        break

                    elif grbl_out.find('error') >= 0:

                        log.warning("GRBL > "+str(l_count) +
                                    ": \""+grbl_out+"\"")
                        error_count += 1
                        break

                    else:
                        log.debug("GRBL > \"" + grbl_out + "\"")
        else:
            # Send g-code program via a more agressive streaming protocol that forces characters into
            # Grbl's serial read buffer to ensure Grbl has immediate access to the next g-code command
            # rather than wait for the call-response serial protocol to finish. This is done by careful
            # counting of the number of characters sent by the streamer to Grbl and tracking Grbl's
            # responses, such that we never overflow Grbl's serial read buffer.
            log.debug("Stream mode")
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
                        log.debug("GRBL > \""+out_temp+"\"")  # Debug response

                    else:
                        if out_temp.find('error') >= 0:
                            error_count += 1

                        g_count += 1  # Iterate g-code counter

                        log.debug("GRBL > "+str(g_count)+": \""+out_temp+"\"")

                        # Delete the block character count corresponding to the last 'ok'
                        del c_line[0]

                data_to_send = l_block + '\n'

                # Send g-code block to grbl
                s.write(data_to_send.encode())

                log.debug("GRBL < " + str(l_count) +
                          ": \"" + l_block + "\"")

            # Wait until all responses have been received.
            while l_count > g_count:
                out_temp = s.readline().strip().decode()  # Wait for grbl response

                if out_temp.find('ok') < 0 and out_temp.find('error') < 0:
                    log.debug("GRBL > \""+out_temp+"\"")  # Debug response

                else:
                    if out_temp.find('error') >= 0:
                        error_count += 1

                    g_count += 1  # Iterate g-code counter

                    log.debug("GRBL > "+str(g_count) +
                              ": \""+out_temp + "\"")

                    # Delete the block character count corresponding to the last 'ok'
                    del c_line[0]

        end_time = time.time()
        log.info("Time elapsed: " + end_time-start_time + "\n")

        if args.check:
            if error_count > 0:
                log.error(
                    f"Check failed: {error_count} errors found! See output for details.\n")
                quit()
            else:
                log.info("Check passed: No errors found in g-code program.\n")
        else:
            log.info(
                "Wait until Grbl completes buffered g-code blocks before exiting.")


# Get input arguments
args = get_args()
log = logging.getLogger("logger")

if args.debug:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)-12s: %(levelname)-8s %(message)s')
elif args.verbose:
    logging.basicConfig(level=logging.INFO,
                        format='%(name)-12s: %(levelname)-8s %(message)s')
else:
    logging.basicConfig(level=logging.WARNING,
                        format='%(name)-12s: %(levelname)-8s %(message)s')


# --- SETTINGS ---

# GCODE parser settings
settings_mode = False  # Default False, must be True for settings
rx_buffer_size = 128
enable_status_reports = True  # Default True, can toggle monitoring
report_interval = 1.0  # In seconds, if enable_status_reports is True


# Load selected gcode file into list
gcode = gcode_load(args.gcode)
# Convert commands where printing to G1 to indicate printing
# gcode = g0_g1_conversion(gcode)

# Assign grbl object to variable
g = grbl()
s = websocket()

# Connect grbl
s = g.connect()

# Send grbl settings
# g.send_settings()

# # Toggle check mode if activated
# if args.check:
#     g.check_mode()  # Enable
#     g.send(gcode)
#     g.check_mode()  # Disable

# Homing cycle
# g.home()

# Turns on monitoring
is_run = True
g.monitor()

g.send(gcode)
is_run = False  # Turns off monitoring

# Close serial port
s.close()
