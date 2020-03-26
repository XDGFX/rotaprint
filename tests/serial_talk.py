#!/usr/bin/env python3

import serial
import time
import os


def gcode_send(data):
    print("Sending: " + data.strip())
    data = data.strip() + "\r"  # Strip all EOL characters for consistency
    s.write(data.encode())  # Send g-code block to grbl

    grbl_out = s.readline().decode().strip()
    print(grbl_out)


# com = os.path.join(os.getcwd(), 'grbl-1.1h/ttyGRBL')
com = os.path.join(os.getcwd(), '/dev/ttyS3')

# Open grbl serial port
s = serial.Serial(com, 115200)

s.write("\r\n\r\n".encode())  # Wake up grbl
time.sleep(2)  # Wait for grbl to initialize
s.flushInput()  # Flush startup text in serial input

try:
    while 1:
        gcode_send(input("> "))
except KeyboardInterrupt:
    pass

print("\nExiting...")
gcode_send("$")

# Close serial port
s.close()
