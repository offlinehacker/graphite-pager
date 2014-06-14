import argparse
import logging


def parse_args():
    parser = argparse.ArgumentParser(description='Run Graphite Pager')
    parser.add_argument(
        'command',
        choices=['run', 'verify'],
        default='run',
        help='What action to take'
    )
    parser.add_argument(
        '--config',
        metavar='config',
        type=str,
        default='alerts.yml',
        help='path to the config file'
    )

    args = parser.parse_args()
    return args


def setup_custom_logger(name):
    logging.basicConfig()
    logger = logging.getLogger(name)
    logger.propagate = False
    if logger.handlers:
        logger.handlers = []

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-7s %(message)s'
        )

        handler = logging.StreamHandler()
        if formatter is not False:
            handler.setFormatter(formatter)

        logger.addHandler(handler)

    if False:
        logger.setLevel(logging.DEBUG)
        if hasattr(logging, 'captureWarnings'):
            logging.captureWarnings(True)
    else:
        logger.setLevel(logging.INFO)
        if hasattr(logging, 'captureWarnings'):
            logging.captureWarnings(False)

    log_level = logging.getLevelName(logger.level)
    logger.debug('Logger level is {0}'.format(log_level))
    return logger
