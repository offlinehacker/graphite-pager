from level import Level


class PagerdutyNotifier(object):

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage

    def notify(self, alert, alert_key, level, description, html_description):
        service_key = None
        if alert.get('pagerduty_key', None) is not None:
            service_key = self._client.service_key
            self._client.service_key = alert.get('pagerduty_key', None)

        incident_key = self._storage.get_incident_key_for_alert_key(alert_key)
        if level != Level.NOMINAL:
            description = str(description)
            incident_key = self._client.trigger(
                incident_key=incident_key,
                description=description
            )
            self._storage.set_incident_key_for_alert_key(
                alert_key,
                incident_key
            )
        elif incident_key is not None:
            self._client.resolve(incident_key=incident_key)
            self._storage.remove_incident_for_alert_key(alert_key)

        if service_key:
            self._client.service_key = service_key
