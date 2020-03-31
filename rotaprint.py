#!/usr/bin/env python
"""
Main script for running the TDCA rotary printer.

Copyright (C) Callum Morrison - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Callum Morrison <callum.morrison@mac.com>, 2020
"""

import socketserver
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

    # Decrease output of external modules
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

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


class webserver:
    def start(self):
        logging.info("Initialising webserver")
        # Create thread to run webserver.run as a daemon (in background)
        webserverThread = threading.Thread(target=self.run)
        webserverThread.daemon = True
        webserverThread.start()
        logging.info("Webserver initialised")
        logging.info("Accessible at http://localhost:8080")

    def run(self):
        import http.server

        PORT = 8080
        Handler = http.server.SimpleHTTPRequestHandler

        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("serving at port", PORT)
            httpd.serve_forever()


class database:
    # General class for connection with backend database

    settings = [
        # --- GRBL specific ---
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

        # --- Variable ---
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
        ("$132", 200),    # Z Max travel, mm

        # --- Printer specific ---
        ("port", "grbl-1.1h/ttyGRBL"),  # TODO CHANGE to /dev/ttyUSB1

        # --- Option defaults ---
        ("length", 100),
        ("radius", 10),
        ("batch", 5),
        ("check", False),

    ]

    def connect(self):
        log.info("Connecting to database...")
        db_location = 'rotaprint.db'

        if not os.path.isfile(db_location):
            log.info("Database not found...")

            self.connection = sqlite3.connect(
                db_location, check_same_thread=False)
            self.cursor = self.connection.cursor()
            self.create_databases()

        else:
            log.info("Database already found, using that one")

            self.connection = sqlite3.connect(
                db_location, check_same_thread=False)
            self.cursor = self.connection.cursor()

    def create_databases(self):
        # Create new settings tables
        log.info("Creating new databases...")
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS \'settings\' (parameter STRING, value REAL)')

        # Create default settings values
        log.debug("Inserting default settings values...")
        self.cursor.executemany(
            'INSERT INTO \'settings\' VALUES(?, ?)', self.settings)

        self.connection.commit()
        log.debug("Settings updated successfully")

    def get_settings(self):
        # Select and retrieve all settings
        self.cursor.execute('SELECT * FROM \'settings\'')
        settings = dict(self.cursor.fetchall())
        return settings


class websocket:
    # Class for interacting with front end GUI over websocket (to receive data)
    def connect(self):
        logging.info("Initialising websocket instance")
        # Create thread to run websocket.listen as a daemon (in background)
        listenThread = threading.Thread(target=self.listen)
        listenThread.daemon = False
        listenThread.start()
        logging.info("Websocket initialised")

    def listen(self):
        # Listen always for messages over websocket
        import asyncio
        import websockets

        async def listener(websocket, path):
            hold = False
            buffer = list()
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
                elif message == "GCD":
                    # Load next message and update GCODE
                    global gcode
                    log.info("GCODE receiving...")
                    gcode = await websocket.recv()
                    gcode = [line.strip()
                             for line in gcode.decode().split("\n")]
                    log.info("GCODE successfully received")
                    log.debug(f'WSKT < GCD~done')
                    await websocket.send("GCD~done")
                    continue

                if hold:
                    buffer.append(message)
                else:
                    if buffer:
                        # Buffer has data
                        output = self.handler(buffer)
                        log.debug(f'WSKT < {output}')
                        await websocket.send(output)

                        # Clear buffer
                        buffer = list()
                    else:
                        # Normal message (convert to list)
                        output = self.handler([message])
                        log.debug(f'WSKT < {output}')
                        await websocket.send(output)

        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(listener, 'localhost', 8765, max_size=None)
        log.warning("No file size limit set on websocket connection")
        log.warning("This may cause issues when trying to upload large files")

        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def handler(self, message):
        def emergency_stop(self):
            print("EST")
            pass

        def buffer_hold(self):
            pass

        def buffer_release(self):
            pass

        def set_length(self, data):
            pass

        def set_batch(self, data):
            pass

        def set_radius(self, data):
            pass

        def toggle_check_mode(self, data):
            pass

        def database_set(self, data):
            pass

        def send_manual(self, data):
            pass

        def print_now(self):
            # Send all supplied GCODE to printer
            if gcode == "":
                log.error("No GCODE supplied; cannot print")
                return ("ERROR~No gcode")
            else:
                g.send(gcode)
                br()

        def fetch_settings(self):
            # Return all database settings in JSON format
            from json import dumps
            current_settings = db.get_settings()
            return dumps(current_settings)

        def fetch_value(self, data):
            # Get current value of variable
            variable = {
                "connected": connected,
            }
            return str(variable[data])

        def reconnect_printer(self):
            g.reconnect()
            return "done"

        switcher = {
            "EST": emergency_stop,
            "BFH": buffer_hold,
            "BFR": buffer_release,
            "LEN": set_length,
            "BAT": set_batch,
            "RAD": set_radius,
            "CHK": toggle_check_mode,
            "DBS": database_set,
            "GRB": send_manual,
            "PRN": print_now,
            "FTS": fetch_settings,
            "RQV": fetch_value,
            "RCN": reconnect_printer,
        }

        for item in message:
            # Separate command and data
            item = item.split("~")

            # Execute command
            if len(item) == 2:
                # Message has data
                output = switcher[item[0]](self, item[1])
                output = item[0] + "~" + output
                return output
            elif item[0] == "":
                # Blank message
                pass
            elif len(item) == 1:
                # Message has no data
                output = switcher[item[0]](self)
                output = output = item[0] + "~" + output
                return output


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
        # Get GRBL settings
        self.settings = db.get_settings()
        self.port = self.settings["port"]
        self.settings = {x: self.settings[x]
                         for x in self.settings if x.find("$") >= 0}

    def reconnect(self):
        global s
        global connected

        if s != "":
            s.close()
            connected = False
        self.connect()

    def connect(self):
        global s
        global connected
        log.info("Connecting to printer...")
        try:
            # Connect to serial
            log.info(f"Connecting on port {self.port}...")
            s = serial.Serial(self.port, 115200, timeout=1)
            log.info("Connection success!")

            # Wake up grbl
            log.debug("GRBL < \"\\r\\n\\r\\n\"")
            s.write("\r\n\r\n".encode())

            temp_out = s.readline().strip().decode()
            if temp_out.find('error:9') >= 0:
                self.clear_lockout()
            time.sleep(2)  # Wait for grbl to initialize
            s.flushInput()  # Flush startup text in serial input
            connected = True

        except Exception:
            log.error("Unable to connect to printer", exc_info=True)

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
                self.reconnect()
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

        send_settings = list()

        # Get required settings from Database
        self.settings = db.get_settings()
        self.settings = {x: self.settings[x]
                         for x in self.settings if x.find("$") >= 0}

        # Iterate through received data and find outdated settings
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
            if self.is_run:
                self.send_status_query()
            time.sleep(report_interval)

    def monitor(self):
        self.is_run = False
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
            out = s.readline().strip()  # Wait for grbl response with carriage return
            if out.find('error') >= 0:
                log.debug(f"GRBL > {out}")
                log.error("Failed to set Grbl check-mode. Aborting...")
                quit()
            elif out.find('ok') >= 0:
                log.debug(f'GRBL > {out}')
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
                    out = s.readline().strip().decode()

                    if out.find('ok') >= 0:

                        log.debug(f"GRBL > {str(l_count)}: {out}")
                        break

                    elif out.find('error') >= 0:

                        log.warning(f"GRBL > {str(l_count)}: {out}")
                        error_count += 1
                        break

                    else:
                        log.debug(f"GRBL > {out}")
        else:
            # Send g-code program via a more agressive streaming protocol that forces characters into
            # Grbl's serial read buffer to ensure Grbl has immediate access to the next g-code command
            # rather than wait for the call-response serial protocol to finish. This is done by careful
            # counting of the number of characters sent by the streamer to Grbl and tracking Grbl's
            # responses, such that we never overflow Grbl's serial read buffer.
            log.debug("Stream mode")
            self.is_run = True
            g_count = 0
            c_line = []
            for line in data:
                l_count += 1  # Iterate line counter

                # Strip comments/spaces/new line and capitalize
                l_block = re.sub(r'\s|\(.*?\)', '', line).upper()

                # Track number of characters in grbl serial read buffer
                c_line.append(len(l_block) + 1)
                out = ''

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
        self.is_run = False

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
gcode = ""
s = ""
g = ""
connected = False  # Check whether backend is successfully connected to printer


# Load selected gcode file into list
# logging.debug("Loading supplied gcode")
# gcode = gcode_load(args.gcode)
# br()
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

# Start webserver
webserver().start()
br()

# # Connect grbl
g = grbl()  # GRBL object
g.connect()  # Serial connection
br()

# if connected:
#     # Set up monitoring thread
#     g.monitor()
#     br()

#     # Check for out of date grbl settings, and send if needed
#     g.send_settings()
#     br()

# Check supplied GCODE if required
# if args.check:
#     log.info("Check mode enabled")
#     log.info("Running full program check...")
#     br()
#     g.check_mode()  # Enable
#     g.send(gcode)
#     g.check_mode()  # Disable
#     br()

# Homing cycle
# g.home()

# Close serial port
# s.close()
