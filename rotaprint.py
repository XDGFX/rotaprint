#!/usr/bin/env python
"""
Copyright (c) 2020
This file is part of the TDCA rotary printer project.

Main script for running the TDCA rotary printer.
Written by Callum Morrison <callum.morrison@mac.com>, 2020

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import http.server
import socketserver
import serial
import time
import re
import asyncio
import websockets
import threading
import concurrent.futures
import logging
import sqlite3
import os
import io
import sys
import traceback
import math
from json import dumps, loads


class rotaprint:
    # Setup threading pool
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    # Initialise variables
    # Enables check mode to test gcode first
    check_mode = ""

    # Enable scanning functionality
    scan_mode = ""

    # Radius of part to print on / mm
    radius = ""

    # Length of part to print on / mm
    length = ""

    # Number of parts in batch / int
    batch = ""

    # Current batch part / int
    batch_current = ""

    # Current offset / float
    offset = ""

    # Fraction of total print remaining (where 0 is complete, 1 is not started)
    remaining = 1

    status = {
        "time_elapsed": 0,
        "parts_complete": 0,
        "time_remaining": 0,
        "operation": "Idle",

        "grbl_operation": "Idle",
        "grbl_x": "",
        "grbl_y": "",
        "grbl_z": "",
        "grbl_lockout": 1,

        "print_progress": 0
    }

    def setup_log(self):
        # Create normal logger
        log = logging.getLogger("rotaprint")
        log.setLevel(logging.DEBUG)

        # Number of characters already sent
        self.log_history = 0

        # Create variable logger for GUI
        log_capture_string = io.StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '<*>%(asctime)s<~>%(levelname)s<~>%(message)s', '%H:%M:%S')
        ch.setFormatter(formatter)
        log.addHandler(ch)

        # Decrease output of external modules
        logging.getLogger("websockets").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

        # if args.debug:
        logging.basicConfig(format='%(name)-12s: %(levelname)-8s %(message)s')

        log.info("Successfully setup logging")

        return log, log_capture_string

    def except_logger(self):
        exc_type, exc_value, tb = sys.exc_info()

        error = traceback.format_exception(exc_type, exc_value, tb)

        for line in error:
            # Replace newline to prevent issues when displaying at frontend
            log.error(line)

    def timer(self):
        # Initialise start time
        start_time = time.time()

        while self.active:
            # Do not update if on hold status
            if re.match("Hold", self.status["grbl_operation"]):
                start_time += 1

            # Update time elapsed
            time_elapsed = time.time() - start_time
            time_format = str(round(time_elapsed / 60)) + \
                "m " + str(round(time_elapsed % 60)) + "s"
            self.status["time_elapsed"] = time_format

            # Estimate time remaining
            try:
                time_remaining = self.remaining * \
                    (time_elapsed / (1 - self.remaining))
            except ZeroDivisionError:
                time_remaining = 0

            time_format = "~" + str(round(time_remaining / 60)) + \
                "m " + str(round(time_remaining % 60)) + "s"
            self.status["time_remaining"] = time_format

            time.sleep(1)

    def print_sequence(self):
        # Allow existing timers to end
        self.active = False

        time.sleep(2)

        # Indicate machine is active
        self.active = True

        # Submit timer task
        r.pool.submit(self.timer)

        # Modify gcode as required for colour change and dimensions
        gc.correct()

        # Change check mode on grbl if required
        if self.check_mode != g.check:
            g.check_mode()

        # If check mode is enabled
        if self.check_mode:
            self.batch = 1
            self.batch_current = 0
            # Send gcode once
            self.batch_new_part()
        else:
            self.batch_current = 0
            g.change_batch(self.batch_current, True)

            if r.scan_mode:
                # Setup WCS for correct scan start position
                g.offset_y(self.offset)

                # Scan for reference images
                v.initial_scan()

            self.batch_new_part()

        time.sleep(5)

    def batch_new_part(self):
        # If there are more parts to do
        if self.batch_current < self.batch:
            # Update parts complete status
            self.status["parts_complete"] = str(
                self.batch_current) + " of " + str(self.batch)

            if self.batch_current > 0:
                # Go to scanner
                g.change_batch(self.batch_current, True)

                # # Scan part
                if r.scan_mode:
                    self.offset = v.scan()

            # Setup WCS for correct print start position
            g.offset_y(self.offset)

            # Go to printer
            g.change_batch(self.batch_current)

            # Send gcode
            g.send(gc.gcode, batch=True)
            # self.pool.submit(g.send, data=gc.gcode)

        elif self.batch_current == self.batch:
            # Update parts complete status
            self.status["parts_complete"] = str(
                self.batch_current) + " of " + str(self.batch)

            self.status["print_progress"] = 100

            self.status["time_remaining"] = "0m 0s"

            # Check for final status update
            try:
                g.s.write('?\n'.encode())
                g.read()
            except:
                r.except_logger()

            self.active = False

            self.status["grbl_operation"] = "Done"


class gcode:
    gcode = ""

    def correct(self):
        for idx, line in enumerate(self.gcode):
            # Correct Y and Z commands
            self.correct_dims(idx, line)

            # Add correct colour change commands
            self.correct_colours(idx, line)

    def correct_dims(self, idx, line):
        # Correct y and z values to take radius into account

        # Alter Y value
        m = re.search("Y([\d.]+)", line)

        # If command contains Y
        if m:
            y = m.string[m.start(1):m.end(1)]
            y = float(y)

            # deg = mm * (360 / 2πr)
            y = y * 360 / (2 * math.pi * r.radius)

            y = round(y, 2)

            new_line = line[:m.start(1)] + str(y) + line[m.end(1):]

            self.gcode[idx] = new_line

        # Alter Z value
        m = re.search("Z([\d.]+)", line)

        # If command contains Z
        if m:
            z = m.string[m.start(1):m.end(1)]
            z = float(z)

            # if drawing
            if z == 1:
                # set Z to part outer radius, plus the offset
                z = db.settings["z_height"] - \
                    r.radius + db.settings["z_offset"]
            else:
                # set Z to part outer radius, plus the lift height
                z = db.settings["z_height"] - \
                    r.radius - db.settings["z_lift"]

            z = round(z, 2)

            new_line = line[:m.start(1)] + str(z) + line[m.end(1):]

            self.gcode[idx] = new_line

    def correct_colours(self, idx, line):
        # Replace generic colour change commands with correct GCODE
        m = re.search("<C(\d+?)>", line)

        # If a colour change command
        if m:
            colour = m.string[m.start(1): m.end(1)]
            colour = float(colour)

            # Update command correctly based on requested colour
            command = "G0B" + \
                str(db.settings["colour_origin"] +
                    colour * db.settings["colour_offset"])

            self.gcode[idx] = command


class webserver:
    def start(self):
        log.info("Initialising webserver")
        # Create thread to run webserver.run as a daemon (in background)
        webserverThread = threading.Thread(target=self.run)
        webserverThread.daemon = True
        webserverThread.start()
        log.info(
            "Webserver initialised, Accessible at http://localhost:8080/web/index.html")

    def run(self):
        PORT = 8080
        Handler = http.server.SimpleHTTPRequestHandler

        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            log.info(f"serving at port {PORT}")
            httpd.serve_forever()


class database:
    # General class for connection with backend database

    settings = {
        # --- GRBL specific ---
        "$0": 10,       # Length of step pulse, microseconds
        "$1": 255,      # Step idle delay, milliseconds
        "$2": 0,        # Step port invert, mask
        "$3": 0,        # Direction port invert, mask
        "$4": 0,        # Step enable invert, boolean
        "$5": 0,        # Limit pins invert, boolean
        "$6": 0,        # Probe pin invert, boolean
        "$10": 1,       # Status report, mask
        "$11": 0.010,   # Junction deviation, mm
        "$12": 0.002,   # Arc tolerance, mm
        "$13": 0,       # Report inches, boolean
        "$20": 0,       # Soft limits, boolean
        "$21": 0,       # Hard limits, boolean
        "$22": 1,       # Homing cycle, boolean
        "$23": 0,       # Homing dir invert, mask
        "$24": 25,      # Homing feed, mm/min
        "$25": 500,     # Homing seek, mm/min
        "$26": 25,      # Homing debounce, milliseconds
        "$27": 1,       # Homing pull-off, mm
        "$30": 1000,    # Max spindle speed, RPM
        "$31": 0,       # Min spindle speed, RPM
        "$32": 1,       # Laser mode, boolean
        "$33": 0,       # Camera pin invert, boolean
        "$100": 250,    # X steps/mm
        "$101": 250,    # Y steps/°
        "$102": 250,    # Z steps/mm
        "$103": 250,    # A steps/mm
        "$104": 250,    # B steps/°
        "$110": 500,    # X Max rate, mm/min
        "$111": 500,    # Y Max rate, °/min
        "$112": 500,    # Z Max rate, mm/min
        "$113": 500,    # A Max rate, mm/min
        "$114": 500,    # B Max rate, °/min
        "$120": 10,     # X Acceleration, mm/sec^2
        "$121": 10,     # Y Acceleration, °/sec^2
        "$122": 10,     # Z Acceleration, mm/sec^2
        "$123": 10,     # A Acceleration, mm/sec^2
        "$124": 10,     # B Acceleration, °/sec^2
        "$130": 200,    # X Max travel, mm
        "$131": 720,    # Y Max travel, °
        "$132": 200,    # Z Max travel, mm
        "$133": 200,    # A Max travel, mm
        "$134": 360,    # B Max travel, °

        # --- Printer specific ---
        "port": "/dev/ttyS3",

        # --- General settings ---
        "warning_percentage": 10,
        "report_interval": 1,
        "polling_interval": 100,
        "log_history": 500,
        "z_height": 20,
        "z_offset": 0,
        "z_lift": 10,

        # --- Batch settings ---
        "batch_origin": 110,
        "batch_offset": 100,
        "scanner_offset": 50,

        # --- Colour settings ---
        "colour_origin": 10,
        "colour_offset": 90,

        # --- Option defaults ---
        "length": 100,
        "radius": 10,
        "batch": 5,
        "check": False,
        "scan": True,
    }

    # Convert dictionary to list of tuples for database connection
    settings_tuple = settings.items()

    def connect(self):
        log.info("Connecting to database...")
        db_location = 'rotaprint.db'

        if not os.path.isfile(db_location):
            log.info("Database not found...")

            # Connect to database
            self.connection = sqlite3.connect(
                db_location, check_same_thread=False)
            self.cursor = self.connection.cursor()

            # Create and populate database tables
            self.create_databases()

        else:
            log.info("Database already found, using that one")

            # Connect to database
            self.connection = sqlite3.connect(
                db_location, check_same_thread=False)
            self.cursor = self.connection.cursor()

            # Update settings using database values
            self.get_settings()

    def create_databases(self):
        # Create new settings tables
        log.info("Creating new databases...")
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS \'settings\' (parameter STRING, value REAL)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS \'default_settings\' (parameter STRING, value REAL)')

        # Create default settings values
        log.debug("Inserting default settings values...")
        self.cursor.executemany(
            'INSERT INTO \'settings\' VALUES(?, ?)', self.settings_tuple)
        self.cursor.executemany(
            'INSERT INTO \'default_settings\' VALUES(?, ?)', self.settings_tuple)

        self.connection.commit()
        log.debug("Settings updated successfully")

    def get_settings(self):
        # Select and retrieve all settings
        log.debug("Fetching settings from database...")
        self.cursor.execute('SELECT * FROM \'settings\'')
        self.settings = dict(self.cursor.fetchall())

        self.cursor.execute('SELECT * FROM \'default_settings\'')
        default_settings = dict(self.cursor.fetchall())

        return self.settings, default_settings

    def set_settings(self, settings):
        log.debug("Updating database settings...")
        self.cursor.executemany(
            'UPDATE \'settings\' SET value=? WHERE parameter=?', settings)
        self.connection.commit()
        log.debug("Database successfully updated")


class websocket:
    # Class for interacting with front end GUI over websocket (to receive data)
    def connect(self):
        logging.info("Initialising websocket instance")
        # Create thread to run websocket.listen
        listenThread = threading.Thread(target=self.listen)
        listenThread.start()

        # r.pool.submit(self.listen)

        logging.info("Websocket initialised")

    def listen(self):
        # Zero connections to start with
        self.connected = 0

        # Listen always for messages over websocket
        async def listener(websocket, path):
            self.connected += 1

            try:
                while True:
                    # Listen for new messages
                    data = await websocket.recv()

                    # Send incoming messages to the handler, in parallel with main process
                    response = self.handler(data)
                    await websocket.send(response)
                    # future = r.pool.submit(self.handler, data)
                    # response = future.result()
                    # await websocket.send(response)
            finally:
                # Decriment connection counter when disconnected
                self.connected -= 1

        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(listener, 'localhost', 8765, max_size=None)
        log.warning(
            "No file size limit set on websocket connection. This may cause issues when trying to upload large files.")

        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def payloader(self, command, payload):
        # Used to combine a command and payload into a single JSON style string
        data = {
            "command": str(command),
            "payload": str(payload)
        }

        # Convert to JSON string and return
        data = dumps(data)
        return data

    def handler(self, data):
        def print_settings(self, payload):
            try:
                settings = loads(payload)

                r.check_mode = settings["check_mode"]
                r.scan_mode = settings["scan_mode"]
                r.radius = float(settings["radius"])
                r.length = float(settings["length"])
                r.batch = int(settings["batch"])
                r.offset = float(settings["offset"])

                return "DONE"
            except:
                log.error("Could not assign print settings")
                r.except_logger()
                return "ERROR"

        def database_set(self, payload):
            # Update a database setting

            # Load JSON string input to Python list
            settings = loads(payload)

            # Convert to (reversed) tuple for SQL query
            db_settings = [(v, k) for k, v in settings.items()]
            db.set_settings(db_settings)

            if g.connected:
                g.send_settings()
            else:
                log.error(
                    "Not connected to printer - could not update settings. Restart rotaprint!")

            return "DONE"

        def send_manual(self, payload):
            # Send manual command to grbl
            if g.connected:
                try:
                    data = payload + "\n"
                    g.s.write(data.encode())
                    log.info(f"GRBL > {g.read()}")
                    return "DONE"
                except:
                    r.except_logger()
                    return "ERROR"
            else:
                log.error(
                    "Not connected to printer - could not update settings. Restart rotaprint!")
                return "ERROR"

        def receive_gcode(self, payload):
            # Receive gcode, and load into global variable
            gc.gcode = [line.strip() for line in payload.splitlines()
                        if not line.startswith('#')]

            return "DONE"

        def print_now(self, payload):
            # Send all supplied GCODE to printer
            if gc.gcode == "":
                log.error("No GCODE supplied; cannot print")
                return "ERROR"
            else:
                log.info("Sending gcode to printer...")

                # r.pool.submit(r.print_sequence())
                thread = threading.Thread(target=r.print_sequence())
                thread.start()
                # r.print_sequence()
                return "DONE"

        def home(self, payload):
            g.home()
            return "DONE"

        def fetch_settings(self, payload):
            # Return all database settings in JSON format
            log.debug("Retrieving database settings")
            current_settings, default_settings = db.get_settings()
            return dumps(current_settings) + "~<>~" + dumps(default_settings)

        def fetch_value(self, payload):
            # Get current value of variable
            variable = {
                "grbl": g.connected,
                "websocket": w.connected,
            }
            return self.payloader(payload, str(variable[payload]))

        def reconnect_printer(self, payload):
            # Reconnect to printer incase of issue
            g.reconnect()
            return "DONE"

        def return_logs(self, payload):
            # Return current log data to frontend
            log_contents = logs.getvalue()

            new_logs = log_contents[r.log_history:]

            r.log_history += len(new_logs)

            return new_logs

        def reset_logs_counter(self, payload):
            r.log_history = 0

            return "DONE"

        def get_current_status(self, payload):
            data = dumps(r.status)

            return data

        def toggle_lighting(self, payload):
            g.toggle_lighting()

            return "DONE"

        def change_batch(self, payload):
            payload = int(payload)
            if payload in range(5):
                g.change_batch(payload, True)
            elif payload == -1:
                g.send(["G0A0"], True)
            else:
                return "ERROR"

            return "DONE"

        def feed_hold(self, payload):
            g.s.write("!".encode())
            return "DONE"

        def feed_release(self, payload):
            g.s.write("~".encode())
            return "DONE"

        switcher = {
            "SET": print_settings,
            "DBS": database_set,
            "GRB": send_manual,
            "GCD": receive_gcode,
            "PRN": print_now,
            "HME": home,
            "FTS": fetch_settings,
            "RQV": fetch_value,
            "RCN": reconnect_printer,
            "LOG": return_logs,
            "RLC": reset_logs_counter,
            "GCS": get_current_status,
            "LGT": toggle_lighting,
            "BTC": change_batch,
            "FHD": feed_hold,
            "FRL": feed_release,
        }

        # Separate JSON string into command and payload
        data = loads(data)
        command = data["command"].upper()
        payload = data["payload"]

        if not (command == "LOG" or command == "GCS"):
            if len(payload) < 50:
                log.debug(f'WSKT > {command} \"{payload}\"')
            else:
                log.debug(f'WSKT > {command} (long payload)')

        # Call respective command using switcher
        try:
            response = switcher[command](self, payload)
        except:
            r.except_logger()
            response = "ERROR"

        if not (command == "LOG" or command == "GCS"):
            if len(response) < 50:
                log.debug(f'WSKT < {command} \"{response}\"')
            else:
                log.debug(f'WSKT < {command} (long payload)')

        return self.payloader(command, response)


class vision:
    def scan(self):
        pass


class grbl:
    """
    Object for control and configuration of grbl firmware and connection.
    """

    startup = {
        "$N0": ""  # GCODE to run on every startup of grbl  TODO
    }

    # Checkmode toggle
    check = False

    # Connected flag
    connected = False

    # Lighting toggle
    lighting = False

    def __init__(self):
        # Get GRBL settings
        self.settings, _ = db.get_settings()
        self.port = self.settings["port"]
        self.settings = {x: self.settings[x]
                         for x in self.settings if x.find("$") >= 0}

    def reconnect(self):
        log.debug("Reconnecting to printer...")

        try:
            self.s.close()
            self.connected = False
        except:
            r.except_logger()
            log.warning("Could not disconnect")
        self.connect()

    def connect(self):
        log.info("Connecting to printer...")
        try:
            # Connect to serial
            log.debug(f"Connecting on port {self.port}...")
            # self.s = serial.Serial(self.port, 115200, timeout=1)
            self.s = serial.Serial(self.port, 115200, timeout=10)

            log.info("Connection success!")

            # Wake up grbl
            log.debug("GRBL < \"\\r\\n\\r\\n\"")
            self.s.write("\r\n\r\n".encode())

            time.sleep(2)  # Wait for grbl to initialize

            for i in range(3):
                log.debug(self.read())

            self.s.flushInput()  # Flush startup text in serial input
            self.connected = True

            self.send_settings()

        except:
            log.error("Unable to connect to printer!")
            r.except_logger()

    def send_settings(self):
        log.info("Checking if firmware settings need updating...")

        log.debug("GRBL <* $$")
        self.s.write("$$\n".encode())

        # # In testing, GRBL would often take several lines to start responding,
        # # this should flush that so program will not hang
        # for i in range(0, 20):
        #     self.s.write("\n".encode())

        # Wait until current settings are received
        temp_out = ""
        force_settings = False

        timeout_counter = 0
        while not temp_out.startswith("$"):
            # Wait for settings to start receiving

            if timeout_counter > 15:
                # Timeout condition
                log.error("Printer communication timeout while reading settings")
                log.info("Will reconnect in an attempt to fix")
                self.reconnect()
                log.warning(
                    "Attempting to continue by forcing settings update, if this doesn't work restart the machine and try again!")
                force_settings = True
                break

            if temp_out.find('error:9') >= 0:
                log.warning(
                    "Lockout error detected while attempting to send settings!")
                force_settings = True
            elif temp_out.find('error') >= 0:
                log.debug(f"GRBL > {temp_out}")
                log.error(
                    "Error occured with printer communication during settings setup")
                log.warning("Forcing settings send...")
                force_settings = True
                break

            temp_out = self.read()
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
                    temp_out = self.read()
            else:
                log.debug(f"GRBL > {temp_out}")
                log.error("Unexpected data received from GRBL")
                log.info("All settings will be forced instead")
                force_settings = True

        send_settings = list()

        # Get required settings from Database
        self.settings, _ = db.get_settings()

        # Convert received settings to directionary
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
        self.send(["$H"], True)

    def toggle_lighting(self, manual=None):
        # Turn lights and laser on or off
        log.info("Toggling the lights...")

        I = db.settings["$33"]
        X = manual == None
        L = self.lighting
        M = manual

        # Turn lights on if:
        #   - lighting is off already, and manual is not true or
        #   - manual is true
        if (M and not I) or (X and not I and not L) or (M == 0 and I) or (X and I and not L):
            # Turn lights on
            self.send(["M9"], True)
            self.lighting = True
        else:
            # Turn lights off
            self.send(["M8"], True)
            self.lighting = False

    def change_batch(self, batch, scan=False):
        if not scan:
            # Generate GCODE to move requested part under printhead
            command = "G0A" + \
                str(db.settings["batch_origin"] +
                    batch * db.settings["batch_offset"])
        else:
            # Generate GCODE to move requested part under scanner
            command = "G0A" + \
                str(db.settings["batch_origin"] +
                    batch * db.settings["batch_offset"] + db.settings["scanner_offset"])

        # Send to grbl
        self.send([command], True)

    def offset_y(self, offset):
        log.debug(f"Setting Y offset to {offset}")
        # Setup offset value
        command = "G10 L2 P1 Y" + str(offset)

        # Send command to grbl
        self.send([command], True)

    def send_status_query(self):
        # Built in GRBL status report, in format:
        # <Idle|MPos:0.000,0.000,0.000|FS:0.0,0>
        # Recommended query frequency no more than 5Hz
        # log.debug("Sending status query...")
        # log.debug("GRBL < ?")
        try:
            self.s.write('?\n'.encode())
        except:
            r.except_logger()

    def periodic_timer(self):
        while True:
            if self.is_run:
                self.send_status_query()
            time.sleep(db.settings["report_interval"])

    def monitor(self):
        self.is_run = False
        # if enable_status_reports:
        log.info("Starting firmware log daemon...")

        timerThread = threading.Thread(target=self.periodic_timer)
        timerThread.daemon = True
        timerThread.start()

    def check_mode(self):
        log.info('Toggling grbl check-mode...')
        self.send(['$C'], True)

        # Invert checkmode variable
        self.check != self.check

        if self.check:
            log.info("Check mode enabled!")
            log.info("Inspect logs once complete if any errors occur.")
        else:
            log.info("Check mode disabled!")

        log.info(self.read())

        # while True:
        #     out = self.s.readline().strip()  # Wait for grbl response with carriage return
        #     if out.find('error') >= 0:
        #         log.debug(f"GRBL > {out}")
        #         log.error(
        #             "Failed to set Grbl check-mode. Attempting to reconnect...")
        #         self.reconnect()
        #     elif out.find('ok') >= 0:
        #         log.debug(f'GRBL > {out}')

    def read(self):
        output = self.s.readline().strip().decode()

        # Contains status report
        if re.search("^<[\\w\\W]+?>$", output):
            # Current grbl operation
            r.status["grbl_operation"] = re.findall(
                "<([\\w\\W]+?)\\|", output)[0]

            # Current grbl position
            MPos = re.findall("MPos:([\\w\\W]+?)\\|", output)
            MPos = MPos[0].split(",")

            r.status["grbl_x"] = "<b>X</b>{:.2f}".format(float(MPos[0]))
            r.status["grbl_y"] = "<b>Y</b>{:.2f}".format(float(MPos[1]))
            r.status["grbl_z"] = "<b>Z</b>{:.2f}".format(float(MPos[2]))

            return "REMOVE"

        # Lockout message warning
        if re.search("\$X", output) or re.search("error:9", output):
            r.status["grbl_lockout"] = 1

        return output

    def send(self, data, settings_mode=False, batch=False):
        def _sender(self, **args):
            l_count = 0
            error_count = 0
            start_time = time.time()

            if settings_mode:
                # Send settings file via simple call-response streaming method. Settings must be streamed
                # in this manner since the EEPROM accessing cycles shut-off the serial interrupt.

                self.is_run = True

                for line in data:
                    l_count += 1  # Iterate the line counter
                    l_block = line.strip()  # Strip all EOL characters for consistency

                    # Asterisk indicates code is sent using settings mode
                    log.debug(f"GRBL <* {str(l_count)}: {l_block}")

                    # Send g-code block to grbl
                    self.s.write((l_block + '\n').encode())

                    while True:
                        # Wait for grbl response with carriage return
                        out = self.read()

                        if out.find('ok') >= 0:
                            log.debug(f"GRBL > {str(l_count)}: {out}")
                            break
                        elif out.find('error') >= 0:
                            log.warning(f"GRBL > {str(l_count)}: {out}")
                            error_count += 1
                            break
                        elif out.find('ALARM') >= 0:
                            log.error(f"GRBL > {str(l_count)}: {out}")
                        else:
                            if out.find('REMOVE') < 0:
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
                rx_buffer_size = 128
                gcode_length = len(data)

                for line in data:
                    l_count += 1  # Iterate line counter

                    # Calculate percentage complete
                    r.status["print_progress"] = (g_count / gcode_length) * 100

                    # Estimate time remaining
                    r.remaining = ((r.batch - 1 - r.batch_current) +
                                   (gcode_length - g_count) / gcode_length) / r.batch

                    # Strip comments/spaces/new line and capitalize
                    l_block = re.sub(r'\s|\(.*?\)', '', line).upper()

                    # Track number of characters in grbl serial read buffer
                    c_line.append(len(l_block) + 1)
                    out = ''

                    while sum(c_line) >= rx_buffer_size - 1 | self.s.inWaiting():
                        out_temp = self.read()  # Wait for grbl response

                        if out_temp.find('ok') < 0 and out_temp.find('error') < 0:
                            if out_temp.find('REMOVE') < 0:
                                # Debug response
                                log.debug(f"GRBL > {out_temp}")
                        else:
                            if out_temp.find('error') >= 0:
                                error_count += 1

                            g_count += 1  # Iterate g-code counter
                            log.debug(f"GRBL > {str(g_count)}: {out_temp}")

                            # Delete the block character count corresponding to the last 'ok'
                            del c_line[0]

                    data_to_send = l_block + '\n'

                    # Send g-code block to grbl
                    self.s.write(data_to_send.encode())

                    log.debug(f"GRBL < {str(l_count)}: {l_block}")

                # Wait until all responses have been received.
                while l_count > g_count:
                    out_temp = self.read()  # Wait for grbl response

                    if out_temp.find('ok') < 0 and out_temp.find('error') < 0:
                        if out_temp.find('REMOVE') < 0:
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

            if self.check:
                log.info("Checking response...")
                if error_count > 0:
                    log.error(
                        f"Check failed: {error_count} errors found! See output for details.")
                    quit()
                else:
                    log.info("Check passed: No errors found in g-code program.")

            # Request next batch if required
            if batch:
                r.batch_current += 1
                r.batch_new_part()

        # Submit task to pool
        if batch:
            r.pool.submit(_sender, self, data=data,
                          settings_mode=settings_mode, batch=batch)
        else:
            _sender(self, data=data, settings_mode=settings_mode)


if __name__ == "__main__":
    # --- SETUP SEQUENCE ---
    # Connect general use class
    r = rotaprint()

    # Setup logging
    log, logs = r.setup_log()

    # Connect backend database
    db = database()
    db.connect()

    # Connect gcode class
    gc = gcode()

    # Start GUI websocket
    w = websocket()
    w.connect()

    # Start webserver
    webserver().start()

    # Connect grbl
    g = grbl()  # GRBL object
    g.connect()  # Serial connection

    # Connect vision class
    v = vision()

    # Set up monitoring thread
    g.monitor()
