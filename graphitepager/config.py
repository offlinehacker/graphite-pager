import os
import yaml

from alerts import Alert


def contents_of_file(filename):
    open_file = open(filename)
    contents = open_file.read()
    open_file.close()
    return contents


def get_config(path):
    return Config(path)


class Config(object):

    def __init__(self, path):
        alert_yml = contents_of_file(path)
        self._data = yaml.load(alert_yml)

    def data(self, key):
        return self._data.get(key)

    def get(self, key, default=None):
        return os.environ.get(key, self._data.get(key.lower(), default))

    def has(self, key):
        value = None
        _key = key.lower()
        if _key in self._data:
            value = self._data[_key]
        elif key in os.environ:
            value = os.environ.get(key, None)

        return value is not None and value != ''

    def alerts(self):
        alerts = []
        doc_url = self._data.get('docs_url')
        for alert_string in self._data.get('alerts'):
            alerts.append(Alert(alert_string, doc_url))
        return alerts

    def has_keys(self, keys):
        for key in keys:
            if self.has(key) is False:
                return False
        return True
