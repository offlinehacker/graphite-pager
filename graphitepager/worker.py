import datetime
import time

import redis
import requests
import requests.exceptions

from graphitepager.config import get_config
from graphitepager.description import get_descriptions
from graphitepager.graphite_data_record import GraphiteDataRecord
from graphitepager.graphite_target import get_records
from graphitepager.level import Level
from graphitepager.redis_storage import RedisStorage
from graphitepager.utils import parse_args

from notifiers.notifier_proxy import NotifierProxy
from notifiers.hipchat_notifier import HipChatNotifier
from notifiers.pagerduty_notifier import PagerdutyNotifier
from notifiers.pushbullet_notifier import PushBulletNotifier


def update_notifiers(notifier_proxy, alert, record, graphite_url):
    alert_key = '{} {}'.format(alert.get('name'), record.target)

    alert_level, value = alert.check_record(record)

    description, html_description = get_descriptions(
        graphite_url,
        alert,
        record,
        alert_level,
        value
    )
    if alert_level != Level.NOMINAL:
        print description

    notifier_proxy.notify(
        alert,
        alert_key,
        alert_level,
        description,
        html_description
    )


def create_notifier_proxy(config):
    redis_url = config.get('REDISTOGO_URL', config.get('REDIS_URL', None))
    STORAGE = RedisStorage(redis, redis_url)

    klasses = [
        HipChatNotifier,
        PagerdutyNotifier,
        PushBulletNotifier
    ]

    notifier_proxy = NotifierProxy()
    for klass in klasses:
        notifier = klass(STORAGE, config)
        if notifier.enabled:
            print 'Enabling {0}'.format(notifier._domain)
            notifier_proxy.add_notifier(notifier)

    return notifier_proxy


def verify(args):
    config = get_config(args.config)
    config.alerts()
    print 'Valid configuration, good job!'
    return


def run(args):
    config = get_config(args.config)
    alerts = config.alerts()
    notifier_proxy = create_notifier_proxy(config)
    graphite_url = config.get('GRAPHITE_URL')
    while True:
        start_time = time.time()
        seen_alert_targets = set()
        for alert in alerts:
            target = alert.get('target')
            try:
                records = get_records(
                    graphite_url,
                    requests.get,
                    GraphiteDataRecord,
                    target,
                    from_=alert.get('from'),
                )
            except requests.exceptions.RequestException:
                notification = 'Could not get target: {}'.format(target)
                print notification
                notifier_proxy.notify(
                    alert,
                    target,
                    Level.CRITICAL,
                    notification,
                    notification
                )
                records = []

            for record in records:
                name = alert.get('name')
                target = record.target
                if (name, target) not in seen_alert_targets:
                    print 'Checking', (name, target)
                    update_notifiers(
                        notifier_proxy,
                        alert,
                        record,
                        graphite_url
                    )
                    seen_alert_targets.add((name, target))
                else:
                    print 'Seen', (name, target)
        time_diff = time.time() - start_time
        sleep_for = 60 - time_diff
        if sleep_for > 0:
            sleep_for = 60 - time_diff
            print 'Sleeping for {0} seconds at {1}'.format(
                sleep_for,
                datetime.datetime.utcnow()
            )
            time.sleep(60 - time_diff)


def main():
    args = parse_args()
    if args.command == 'verify':
        return verify(args)
    return run(args)


if __name__ == '__main__':
    main()
