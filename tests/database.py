#!/usr/bin/env python
import json
import os


def get_args():
    import argparse

    desc = "Setup database for rotaprint"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-d', '--dev',
                        help='Enable dev mode (DANGEROUS)', action='store_true')

    args = parser.parse_args()
    return args


args = get_args()
db_path = 'monitor.json'

if args.dev:
    if os.path.isfile(db_path):
        os.remove(db_path)

if os.path.isfile(db_path):
    print
    print(f'WARNING: Existing database found at {db_path}!')
    print('Previous application did not shut down correctly!')
    print('Would you like to start now? (If another instance is running, quit that one first!)')

    response = ''
    while response not in ['y', 'n']:
        response = input('(y/n): ').lower().strip()

        if response == 'y':
            break
        elif response == 'n':
            print('Exiting...')
            quit()

        print('Please enter \'y\' or \'n\'.')

    os.remove(db_path)


defaults = {'current_status': 'IDLE',
            'pos_x': '0',
            'pos_y': '0',
            'pos_z': '0',
            'feed_x': '0',
            'feed_y': '0',
            'feed_z': '0'}

with open(db_path, 'w+') as outfile:
    json.dump(defaults, outfile)
