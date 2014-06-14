import datetime
import time
import requests

from graphitepager.base_log import BaseLog
from graphitepager.config import parse_config
from graphitepager.description import get_descriptions
from graphitepager.graphite_data_record import GraphiteDataRecord
from graphitepager.graphite_target import get_records
from graphitepager.level import Level
from graphitepager.notifiers.notifier_proxy import create_notifier_proxy
from graphitepager.utils import parse_args
from graphitepager.utils import setup_custom_logger


class Worker(BaseLog):

    def __init__(self, config, logger):
        super(Worker, self).__init__(logger=logger)
        self._config = config
        self._graphite_url = config.get('GRAPHITE_URL')
        self._notifier_proxy = create_notifier_proxy(config, logger)

    def loop(self):
        alerts = self._config.alerts()
        while True:
            start_time = time.time()
            seen_alert_targets = set()
            for alert in alerts:
                self._log_debug('Processing {0}'.format(alert.get('real_name')))
                target = alert.get('target')
                try:
                    records = get_records(
                        self._graphite_url,
                        requests.get,
                        GraphiteDataRecord,
                        target,
                        from_=alert.get('from'),
                    )
                except requests.exceptions.RequestException, e:
                    print e
                    self.missing_target(alert)
                    continue

                if not records and not alert.get('ignore_no_data'):
                    self.missing_target(alert)
                    continue

                self.resolve_missing_target(alert)
                self.update_records(alert, records, seen_alert_targets)
                for record in records:
                    seen_alert_targets.add((alert.get('name'), record.target))
            self.sleep(start_time)

    def missing_target(self, alert):
        if self._config.get('IGNORE_NO_DATA'):
            return

        if alert.get('ignore_no_data'):
            return

        notification = 'Could not get target: {}'.format(alert.get('target'))
        self._log_info('[{0}] {1} - {2}'.format(
            Level.CRITICAL,
            alert.get('name'),
            notification
        ))
        self._notifier_proxy.notify(
            alert,
            alert.get('target'),
            Level.CRITICAL,
            notification,
            notification
        )

    def resolve_missing_target(self, alert):
        notification = 'Resolving missing target alert: {}'.format(alert.get('target'))
        self._log_info('[{0}] {1} - {2}'.format(
            Level.NOMINAL,
            alert.get('name'),
            notification
        ))
        self._notifier_proxy.notify(
            alert,
            alert.get('target'),
            Level.NOMINAL,
            notification,
            notification
        )

    def update_records(self, alert, records, seen_alert_targets):
        for record in records:
            alert_key = (alert.get('name'), record.target)
            if alert_key not in seen_alert_targets:
                self._log_debug('Checking record {0}'.format(alert_key))
                self.update_notifiers(alert, record)
                continue
            self._log_debug('Seen {0}'.format(alert_key))

    def update_notifiers(self, alert, record):
        alert_level, value = alert.check_record(record)

        alert_key = '{0} {1}'.format(alert.get('name'), record.target)
        if alert_level != Level.NOMINAL:
            notification = '[{0}] {1} - {2} passes threshold value {3} for {4}'
            self._log_info(notification.format(
                alert_level,
                alert_key,
                value,
                alert.value_for_level(alert_level),
                record.target
            ))

        description, html_description = get_descriptions(
            self._graphite_url,
            alert,
            record,
            alert_level,
            value
        )

        self._notifier_proxy.notify(
            alert,
            alert_key,
            alert_level,
            description,
            html_description
        )

    def sleep(self, start_time):
        time_per_run = int(self._config.get('TIME_PER_RUN', 60))
        time_diff = time.time() - start_time
        sleep_for = time_per_run - time_diff
        if sleep_for > 0:
            sleep_for = time_per_run - time_diff
            self._log_debug('Sleeping for {0} seconds at {1}'.format(
                sleep_for,
                datetime.datetime.utcnow()
            ))
            time.sleep(time_per_run - time_diff)


def run(config):
    logger = setup_custom_logger('graphitepager')
    logger.info('Creating worker')
    worker = Worker(config, logger)
    logger.info('Starting loop')
    worker.loop()


def verify(config):
    config.alerts()
    print 'Valid configuration, good job!'
    return True


def main():
    args = parse_args()
    config = parse_config(args.config)
    if args.command == 'verify':
        return verify(config)

    return run(config)


if __name__ == '__main__':
    main()
