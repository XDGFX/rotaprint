#!/usr/bin/env python3

import serial
import time


def send_gcode(data):
    data = data.strip() + '\n'  # Strip all EOL characters for consistency
    print('Sending: ' + data)
    s.write(data.encode())  # Send g-code block to grbl

    # Wait for grbl response with carriage return
    grbl_out = s.readline().decode().strip()
    return grbl_out


com = '/dev/cu.usbmodem14201'

# Open grbl serial port
s = serial.Serial(com, 115200)

# Open g-code file
f = open('sample.gcode', 'r')

s.write("\r\n\r\n".encode())  # Wake up grbl
time.sleep(2)  # Wait for grbl to initialize
s.flushInput()  # Flush startup text in serial input

grbl_out = send_gcode("$")
print(grbl_out)

# Wait here until grbl is finished to close serial port and file.
input("  Press <Enter> to exit and disable grbl. ")

# Close file and serial port
f.close()
s.close()
