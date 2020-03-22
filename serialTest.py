#!/usr/bin/env python3

import serial
import time


def send_gcode(data):
    data = data.strip() + "\n"  # Strip all EOL characters for consistency
    print("Sending: " + data)
    s.write(data.encode())  # Send g-code block to grbl

    # Wait for grbl response with carriage return
    time.sleep(0.1)
    grbl_out = s.readline().decode().strip()
    print(grbl_out)


com = 'grbl-1.1h/ttyGRBL'

# Open grbl serial port
s = serial.Serial(com, 115200)

# Open g-code file
f = open('sample.gcode', 'r')

s.write("\r\n\r\n".encode())  # Wake up grbl
time.sleep(2)  # Wait for grbl to initialize
s.flushInput()  # Flush startup text in serial input

for x in range(3):  # Allows 3 commands to be sent before exiting
    send_gcode(input("> "))

print("Exiting...")
send_gcode("$")

# grbl_out = send_gcode("$")
# print(grbl_out)
# grbl_out = send_gcode("G0 X0 Y0")
# print(grbl_out)
# grbl_out = send_gcode("G0 X10 Y10")
# print(grbl_out)

# # Wait here until grbl is finished to close serial port and file.
# input("  Press <Enter> to exit and disable grbl. ")

# Close file and serial port
f.close()
s.close()
