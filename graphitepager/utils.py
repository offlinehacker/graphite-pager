import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Run Graphite Pager')
    parser.add_argument(
        'command',
        choices=['run', 'verify'],
        default='run',
        help='What action to take',
        nargs='?'
    )
    parser.add_argument(
        '-c',
        '--config',
        dest='config',
        default='alerts.yml',
        help='path to the config file'
    )

    args = parser.parse_args()
    return args
