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
            gcode.append(line.strip)
    return gcode


def g0_g1_conversion(gcode):
    for command in gcode:
        if command.startswith("G1 F"):
            print(command)


args = get_args()

gcode = load_gcode(args.gcode)

print(args)
print(args.gcode)
print(args.length)
