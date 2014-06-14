import json
import redis

from graphitepager.base_log import BaseLog


class RedisStorage(BaseLog):

    def __init__(self, config, logger=None):
        super(RedisStorage, self).__init__(logger=logger)
        self._config = config
        self._client = None
        self._redis_url = None
        self._redis = None

    def client(self):
        if self._client is None:
            redis_url = self.get_redis_url(self._config)
            self._client = self.get_redis().from_url(redis_url)
        return self._client

    def get_redis(self):
        if self._redis is None:
            self._redis = redis
        return self._redis

    def get_redis_url(self, config):
        if self._redis_url is None:
            default_redis_url = config.get('REDIS_URL', 'redis://localhost:6379/0')
            self._redis_url = config.get('REDISTOGO_URL', default_redis_url)
        return self._redis_url

    def get_incident_key_for_alert_key(self, alert):
        key = self._redis_key_from_alert_key(alert)
        resp = self.client().get(key)
        if resp is not None:
            return json.loads(resp)['incident']

    def set_incident_key_for_alert_key(self, alert, ik):
        data = {'incident': ik}
        key = self._redis_key_from_alert_key(alert)
        self.client().set(key, json.dumps(data))
        self.client().expire(key, 3600)

    def remove_incident_for_alert_key(self, alert):
        key = self._redis_key_from_alert_key(alert)
        self.client().delete(key)

    def set_lock_for_domain_and_key(self, domain, key):
        key = 'LOCK-{0}-{1}'.format(domain, key)
        self.client().set(key, True)
        self.client().expire(key, 300)

    def remove_lock_for_domain_and_key(self, domain, key):
        key = 'LOCK-{0}-{1}'.format(domain, key)
        self.client().delete(key)

    def is_locked_for_domain_and_key(self, domain, key):
        key = 'LOCK-{0}-{1}'.format(domain, key)
        value = self.client().get(key)
        if value is None:
            return False
        return True

    def _redis_key_from_alert_key(self, alert_key):
        return '{0}-incident-key'.format(alert_key)
