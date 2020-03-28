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
import sqlite3
import os


def get_args():
    # Setup argument parser
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


def setup_log():
    # Set log level
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

    return log


def gcode_load(path):
    # Load supplied GCODE file into list
    gcode = list()

    with open(path, "r") as f:
        for line in f:
            # Remove blank lines completely
            if not line.strip() == "":
                gcode.append(line.strip())
    return gcode


def g0_g1_conversion(gcode):
    # Convert all GCODE where printing (indicated by a feedrate change command) to G1
    printing = 0

    for idx, command in enumerate(gcode):
        if command.startswith("G1 F"):
            # Start of printing
            printing = 1
        elif command.startswith("G0 F"):
            # End of printing
            printing = 0

        # Replace [G]0 with [G]1 on current line
        if printing:
            gcode[idx] = command[:1] + "1" + command[2:]  # Replace G0 with G1
    return gcode


def br():
    log.info("------")


class database:
    # General class for connection with backend database

    default_settings = [
        ("$0", 10),       # Length of step pulse, microseconds
        ("$1", 255),      # Step idle delay, milliseconds
        ("$2", 0),        # Step port invert, mask
        ("$3", 0),        # Direction port invert, mask
        ("$4", 0),        # Step enable invert, boolean
        ("$5", 0),        # Limit pins invert, boolean
        ("$6", 0),        # Probe pin invert, boolean
        ("$10", 1),       # Status report, mask
        ("$11", 0.010),   # Junction deviation, mm
        ("$12", 0.002),   # Arc tolerance, mm
        ("$13", 0),       # Report inches, boolean
        ("$20", 0),       # Soft limits, boolean !!! Should be enabled for real use
        ("$21", 0),       # Hard limits, boolean
        ("$22", 1),       # Homing cycle, boolean
        ("$23", 0),       # Homing dir invert, mask
        ("$24", 25),      # Homing feed, mm/min
        ("$25", 500),     # Homing seek, mm/min
        ("$26", 25),      # Homing debounce, milliseconds
        ("$27", 1),       # Homing pull-off, mm
        ("$30", 1000),    # Max spindle speed, RPM
        ("$31", 0),       # Min spindle speed, RPM
        ("$32", 1),       # Laser mode, boolean
        ("$100", 250),    # X steps/mm
        ("$101", 250),    # Y steps/mm  TODO VARIES
        ("$102", 250),    # Z steps/mm
        ("$110", 500),    # X Max rate, mm/min
        ("$111", 500),    # Y Max rate, mm/min  TODO VARIES
        ("$112", 500),    # Z Max rate, mm/min
        ("$120", 10),     # X Acceleration, mm/sec^2
        ("$121", 10),     # Y Acceleration, mm/sec^2
        ("$122", 10),     # Z Acceleration, mm/sec^2
        ("$130", 200),    # X Max travel, mm  TODO VARIES
        ("$131", 200),    # Y Max travel, mm  TODO VARIES
        ("$132", 200)     # Z Max travel, mm
    ]

    def connect(self):
        log.info("Connecting to database...")
        db_location = 'rotaprint.db'

        if not os.path.isfile(db_location):
            log.info("Database not found...")

            self.connection = sqlite3.connect(db_location)
            self.cursor = self.connection.cursor()
            self.create_database()

        else:
            log.info("Database already found, using that one")

            self.connection = sqlite3.connect(db_location)
            self.cursor = self.connection.cursor()

    def create_database(self):
        # Create new settings table
        log.info("Creating new database...")
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS settings (parameter STRING, value REAL)')

        # Create default settings values
        log.debug("Inserting default settings values...")
        self.cursor.executemany(
            'INSERT INTO settings VALUES(?, ?)', self.default_settings)

        self.connection.commit()
        log.debug("Settings updated successfully")

    def get_settings(self):
        # Select and retrieve all settings
        self.cursor.execute('SELECT * FROM settings')
        settings = dict(self.cursor.fetchall())
        return settings


class websocket:
    # Class for interacting with front end GUI over websocket (to receive data)
    def connect(self):
        logging.info("Initialising websocket instance")
        # Create thread to run websocket.listen as a daemon (in background)
        listenThread = threading.Thread(target=self.listen)
        listenThread.daemon = True
        listenThread.start()
        logging.info("Websocket initialised")

    def listen(self):
        # Listen always for messages over websocket
        import asyncio
        import websockets

        async def listener(websocket, path):
            hold = False
            while True:
                # Listen for new messages
                message = await websocket.recv()
                log.debug(f'WSKT > {message}')

                if message == "BFH":
                    # Buffer hold condition
                    hold = True
                    buffer = list()
                elif message == "BFR":
                    # Buffer release condition
                    hold = False

                if hold:
                    buffer.append(message)
                else:
                    if buffer:
                        # Buffer has data
                        threading.Thread(target=self.handler, args=(buffer, ))
                    else:
                        # Normal message (convert to list)
                        threading.Thread(target=self.handler,
                                         args=([message], ))

        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(listener, 'localhost', 8765)

        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def handler(self, message):
        pass


class grbl:
    """
    Object for control and configuration of grbl firmware and connection.
    """

    # GRBL settings (see: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration)
    # Unimportant settings are commented out, program will only update altered settings
    # settings = {
    #     "$0": 10,       # Length of step pulse, microseconds
    #     "$1": 255,      # Step idle delay, milliseconds
    #     # "$2": 0,        # Step port invert, mask
    #     "$3": 0,        # Direction port invert, mask
    #     "$4": 0,        # Step enable invert, boolean
    #     "$5": 0,        # Limit pins invert, boolean
    #     # "$6": 0,        # Probe pin invert, boolean
    #     "$10": 1,       # Status report, mask
    #     # "$11": 0.010,   # Junction deviation, mm
    #     # "$12": 0.002,   # Arc tolerance, mm
    #     # "$13": 0,       # Report inches, boolean
    #     "$20": 0,       # Soft limits, boolean !!! Should be enabled for real use
    #     # "$21": 0,       # Hard limits, boolean
    #     "$22": 1,       # Homing cycle, boolean
    #     "$23": 0,       # Homing dir invert, mask
    #     "$24": 25,      # Homing feed, mm/min
    #     "$25": 500,     # Homing seek, mm/min
    #     "$26": 25,      # Homing debounce, milliseconds
    #     # "$27": 1,       # Homing pull-off, mm
    #     # "$30": 1000,    # Max spindle speed, RPM
    #     # "$31": 0,       # Min spindle speed, RPM
    #     "$32": 1,       # Laser mode, boolean
    #     # ---
    #     "$100": 250,    # X steps/mm
    #     "$101": 250,    # Y steps/mm  TODO VARIES
    #     "$102": 250,    # Z steps/mm
    #     "$110": 500,    # X Max rate, mm/min
    #     "$111": 500,    # Y Max rate, mm/min  TODO VARIES
    #     "$112": 500,    # Z Max rate, mm/min
    #     "$120": 10,     # X Acceleration, mm/sec^2
    #     "$121": 10,     # Y Acceleration, mm/sec^2
    #     "$122": 10,     # Z Acceleration, mm/sec^2
    #     "$130": 200,    # X Max travel, mm  TODO VARIES
    #     "$131": 200,    # Y Max travel, mm  TODO VARIES
    #     "$132": 200  # Z Max travel, mm
    # }

    startup = {
        "$N0": ""  # GCODE to run on every startup of grbl  TODO
    }

    def __init__(self):
        self.settings = db.get_settings()

    def connect(self):
        global s
        log.info("Connecting to printer...")
        try:
            # Connect to serial
            log.debug(f"Connecting on port {args.port}...")
            s = serial.Serial(args.port, 115200, timeout=1)
            log.debug("Connection success!")

            # Wake up grbl
            log.debug("GRBL < \"\\r\\n\\r\\n\"")
            s.write("\r\n\r\n".encode())

            temp_out = s.readline().strip().decode()
            if temp_out.find('error:9') >= 0:
                self.clear_lockout()
            time.sleep(2)  # Wait for grbl to initialize
            s.flushInput()  # Flush startup text in serial input

        except Exception:
            log.error("Unable to connect to printer", exc_info=True)
            quit()

        return s

    def clear_lockout(self):
        log.warning("Lockout error detected! Overriding...")
        log.debug("GRBL < $X")
        s.write("$X".encode())

    def send_settings(self):
        log.info("Checking if firmware settings need updating...")
        log.debug("GRBL < $$")
        s.write("$$".encode())

        # In testing, GRBL would often take several lines to start responding,
        # this should flush that so program will not hang
        for _ in range(1, 20):
            s.write("\n".encode())

        # Wait until current settings are received
        temp_out = ""
        force_settings = False

        timeout_counter = 0
        while not temp_out.startswith("$"):

            if timeout_counter > 10:
                # Timeout condition
                log.error("Printer communication timeout while reading settings")
                log.info("Will reconnect in an attempt to fix")
                log.debug("Disconnecting...")
                s.close()
                self.connect()
                log.warning(
                    "Attempting to continue by forcing settings update")
                force_settings = True
                break

            if temp_out.find('error:9') >= 0:
                self.clear_lockout()
            elif temp_out.find('error') >= 0:
                log.debug(f"GRBL > {temp_out}")
                log.error(
                    "Error occured with printer communication during settings setup")
                log.warning("Forcing settings send...")
                force_settings = True
                break

            temp_out = s.readline().strip().decode()
            log.debug(f"GRBL > {temp_out}")

            timeout_counter += 1

        current_settings = dict()
        if not force_settings:
            # Read all current settings
            if temp_out.startswith("$"):
                while temp_out.startswith("$"):
                    log.debug(f"GRBL > {temp_out}")

                    # Convert received data to dictionary format
                    dict_out = {str(temp_out.split("=")[0]): float(
                        temp_out.split("=")[1])}
                    current_settings.update(dict_out)

                    # Update read
                    temp_out = s.readline().strip().decode()
            else:
                log.debug(f"GRBL > {temp_out}")
                log.error("Unexpected data received from GRBL")
                log.info("All settings will be forced instead")
                force_settings = True

        # Iterate through received data and find outdated settings
        send_settings = list()
        self.settings = db.get_settings()  # Get required settings from Database
        for key in self.settings:
            if self.settings[key] != current_settings.get(key):
                log.debug(f"Out of date setting: {key}")
                send_settings.append(
                    key + "=" + str(self.settings[key]))
            else:
                log.debug(f"Up to date setting: {key}")

        # Send new settings if required
        if len(send_settings) > 0 or force_settings:
            log.info(f"{len(send_settings)} setting(s) need updating!")
            log.info("Sending updated settings...")
            self.send(send_settings, True)
        else:
            log.info("No settings need updating")

    def home(self):
        # Built-in GRBL homing functionality
        log.info("Homing machine...")
        log.debug("GRBL < $H")
        s.write('$H\n'.encode())

    def send_status_query(self):
        # Built in GRBL status report, in format:
        # <Idle|MPos:0.000,0.000,0.000|FS:0.0,0>
        # Recommended query frequency no more than 5Hz
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
            log.info("Starting firmware log daemon...")
            timerThread = threading.Thread(target=self.periodic_timer)
            timerThread.daemon = True
            timerThread.start()
        else:
            log.info("Logging disabled by <enable_status_reports>")

    def check_mode(self):
        log.info('Toggling grbl check-mode...')
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
        log.info("Sending data to printer...")
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

                log.debug(f"GRBL < {str(l_count)}: {l_block}")

                # Send g-code block to grbl
                s.write((l_block + '\n').encode())

                while 1:
                    # Wait for grbl response with carriage return
                    grbl_out = s.readline().strip().decode()

                    if grbl_out.find('ok') >= 0:

                        log.debug(f"GRBL > {str(l_count)}: {grbl_out}")
                        break

                    elif grbl_out.find('error') >= 0:

                        log.warning(f"GRBL > {str(l_count)}: {grbl_out}")
                        error_count += 1
                        break

                    else:
                        log.debug(f"GRBL > {grbl_out}")
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
                        log.debug(f"GRBL > {out_temp}")  # Debug response

                    else:
                        if out_temp.find('error') >= 0:
                            error_count += 1

                        g_count += 1  # Iterate g-code counter

                        log.debug(f"GRBL > {str(g_count)}: {out_temp}")

                        # Delete the block character count corresponding to the last 'ok'
                        del c_line[0]

                data_to_send = l_block + '\n'

                # Send g-code block to grbl
                s.write(data_to_send.encode())

                log.debug(f"GRBL < {str(l_count)}: {l_block}")

            # Wait until all responses have been received.
            while l_count > g_count:
                out_temp = s.readline().strip().decode()  # Wait for grbl response

                if out_temp.find('ok') < 0 and out_temp.find('error') < 0:
                    log.debug(f"GRBL > {out_temp}")  # Debug response

                else:
                    if out_temp.find('error') >= 0:
                        error_count += 1

                    g_count += 1  # Iterate g-code counter

                    log.debug(f"GRBL > {str(g_count)}: {out_temp}")

                    # Delete the block character count corresponding to the last 'ok'
                    del c_line[0]

        end_time = time.time()
        log.info(f"Time elapsed: {str(end_time-start_time)}")

        if args.check:
            log.info("Checking response...")
            if error_count > 0:
                log.error(
                    f"Check failed: {error_count} errors found! See output for details.")
                quit()
            else:
                log.info("Check passed: No errors found in g-code program.")
        else:
            log.debug(
                "Wait until Grbl completes buffered g-code blocks before exiting.")


# Get input arguments
args = get_args()

log = setup_log()


# --- SETTINGS ---

# GCODE parser settings
settings_mode = False  # Default False, must be True for settings
rx_buffer_size = 128
enable_status_reports = True  # Default True, can toggle monitoring
report_interval = 1.0  # In seconds, if enable_status_reports is True


# Load selected gcode file into list
logging.debug("Loading supplied arguments")
gcode = gcode_load(args.gcode)
br()
# Convert commands where printing to G1 to indicate printing
# gcode = g0_g1_conversion(gcode)

# Connect backend database
db = database()
db.connect()
br()

# Start GUI websocket
w = websocket()
w.connect()
br()

# Connect grbl
g = grbl()
s = g.connect()
br()

# Check for out of date grbl settings, and send if needed
g.send_settings()
br()

# Check supplied GCODE if required
if args.check:
    log.info("Check mode enabled")
    log.info("Running full program check...")
    br()
    g.check_mode()  # Enable
    g.send(gcode)
    g.check_mode()  # Disable
    br()

# Homing cycle
# g.home()

is_run = True  # Turns on monitoring

# Set up monitoring thread
g.monitor()
br()

# Send all supplied GCODE to printer
g.send(gcode)
br()
is_run = False  # Turns off monitoring

# Close serial port
s.close()
