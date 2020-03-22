#!/usr/bin/env python


def get_args():
    import argparse

    desc = "Print on cylindrical components!"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('gcode', type=str, help='Input GCODE file')
    parser.add_argument('length', type=float,
                        help='Length of part to print on')
    parser.add_argument('radius', type=float,
                        help='Radius of part to print on')

    args = parser.parse_args()

    return args


def load_gcode(path):
    gcode = list()
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


args = get_args()  # Get input arguments

# Load selected gcode file into list
gcode = load_gcode(args.gcode)
# Convert commands where printing to G1 to indicate printing
gcode = g0_g1_conversion(gcode)


# Write to output file for testing purposes
with open("output.gcode", "w+") as f:
    for command in gcode:
        f.write("%s\n" % command)
