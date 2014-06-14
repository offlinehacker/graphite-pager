from graphitepager.redis_storage import RedisStorage

from graphitepager.notifiers.hipchat_notifier import HipChatNotifier
from graphitepager.notifiers.pagerduty_notifier import PagerdutyNotifier


class NotifierProxy(object):

    def __init__(self):
        self._notifiers = []

    def add_notifier(self, notifier):
        self._notifiers.append(notifier)

    def notify(self, *args, **kwargs):
        for notifier in self._notifiers:
            notifier.notify(*args, **kwargs)


def create_notifier_proxy(config, logger=None):
    STORAGE = RedisStorage(config, logger)

    klasses = [
        HipChatNotifier,
        PagerdutyNotifier,
    ]

    notifier_proxy = NotifierProxy()
    for klass in klasses:
        notifier = klass(STORAGE, config, logger)
        if notifier.enabled:
            logger.info('Enabling {0}'.format(notifier._domain))
            notifier_proxy.add_notifier(notifier)

    return notifier_proxy
