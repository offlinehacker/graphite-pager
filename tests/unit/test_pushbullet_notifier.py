from unittest import TestCase

from mock import MagicMock
from pushbullet import PushBullet


from graphitepager.notifiers.pushbullet_notifier import PushBulletNotifier
from graphitepager.redis_storage import RedisStorage
from graphitepager.alerts import Alert
from graphitepager.config import Config
from graphitepager.level import Level


class TestPushBulletNotifier(TestCase):

    def setUp(self):
        self.alert_key = 'ALERT KEY'
        self.description = MagicMock()
        self.description.__str__.return_value = 'ALERT DESCRIPTION'
        self.description.graphite_url = 'GRAPGITE URL'
        self.html_description = 'HTML ALERT DESCRIPTION'
        self.mock_redis_storage = MagicMock(RedisStorage)
        self.mock_pushbullet_client = MagicMock(PushBullet)
        self.mock_pushbullet_client.devices = [
            MagicMock(device_iden="device1"),
            MagicMock(device_iden="device2")
        ]
        self.mock_pushbullet_client.contacts = [
            MagicMock(email="contact1"),
            MagicMock(email="contact2")
        ]
        self.mock_alert = MagicMock(Alert)
        self.mock_alert.get.return_value = "name"

    def default_notifier(self):
        def mock_get(key, default=None):
            if key == 'PUSHBULLET_KEY':
                return 'PUSHBULLET_KEY'
            return default

        mock_config = MagicMock(Config)
        mock_config.get = mock_get
        self.pbn = PushBulletNotifier(
            self.mock_redis_storage, mock_config,
            client=self.mock_pushbullet_client
        )

    def devices_notifier(self):
        def mock_get(key, default=None):
            if key == 'PUSHBULLET_KEY':
                return 'PUSHBULLET_KEY'
            if key == 'PUSHBULLET_DEVICES':
                return 'device3, device1'
            return default

        mock_config = MagicMock(Config)
        mock_config.get = mock_get
        self.pbn = PushBulletNotifier(
            self.mock_redis_storage, mock_config,
            client=self.mock_pushbullet_client
        )

    def contacts_notifier(self):
        def mock_get(key, default=None):
            if key == 'PUSHBULLET_KEY':
                return 'PUSHBULLET_KEY'
            if key == 'PUSHBULLET_CONTACTS':
                return 'contact3, contact1'
            return default

        mock_config = MagicMock(Config)
        mock_config.get = mock_get
        self.pbn = PushBulletNotifier(
            self.mock_redis_storage, mock_config,
            client=self.mock_pushbullet_client
        )

    def test_should_not_notify_pb_if_warning_and_already_notified(self):
        self.default_notifier()

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = True

        self.pbn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description,
            self.html_description)

        self.assertEqual(self.mock_pushbullet_client.mock_calls, [])

    def test_should_notify_pb_resolved_if_nominal_and_had_notified(self):
        self.default_notifier()

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = True

        self.pbn.notify(
            self.mock_alert,
            self.alert_key,
            Level.NOMINAL,
            self.description,
            self.html_description)

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            assert_called_once_with('PushBullet', self.alert_key)
        self.mock_pushbullet_client.push_link.assert_called_once_with(
            "[%s]: %s" % (Level.NOMINAL, "name"),
            self.description.graphite_url,
            body=str(self.description)
        )
        self.mock_redis_storage.remove_lock_for_domain_and_key.\
            assert_called_once_with('PushBullet', self.alert_key)

    def test_should_notify_pb_of_warning_if_had_not_notified_before(self):
        self.default_notifier()

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.pbn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description,
            self.html_description)

        self.mock_pushbullet_client.push_link.assert_called_once_with(
            "[%s]: %s" % (Level.WARNING, "name"),
            self.description.graphite_url,
            body=str(self.description)
        )

        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('PushBullet', self.alert_key)

    def test_should_notify_pbn_of_critical_if_had_not_notified_before(self):
        self.default_notifier()

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.pbn.notify(
            self.mock_alert,
            self.alert_key,
            Level.CRITICAL,
            self.description,
            self.html_description)

        self.mock_pushbullet_client.push_link.assert_called_once_with(
            "[%s]: %s" % (Level.CRITICAL, "name"),
            self.description.graphite_url,
            body=str(self.description)
        )

        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('PushBullet', self.alert_key)

    def test_should_notify_pb_of_no_data_if_had_not_notified_before(self):
        self.default_notifier()

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.pbn.notify(
            self.mock_alert,
            self.alert_key,
            Level.NO_DATA,
            self.description,
            self.html_description)

        self.mock_pushbullet_client.push_link.assert_called_once_with(
            "[%s]: %s" % (Level.NO_DATA, "name"),
            self.description.graphite_url,
            body=str(self.description)
        )

        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('PushBullet', self.alert_key)

    def test_should_notify_devices(self):
        self.devices_notifier()

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.pbn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description,
            self.html_description)

        devices = self.mock_pushbullet_client.devices
        devices[0].push_link.assert_called_once_with(
            "[%s]: %s" % (Level.WARNING, "name"),
            self.description.graphite_url,
            body=str(self.description)
        )

        self.assertEqual(devices[1].mock_calls, [])

        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('PushBullet', self.alert_key)

    def test_should_notify_contacts(self):
        self.contacts_notifier()

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.pbn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description,
            self.html_description)

        contacts = self.mock_pushbullet_client.contacts
        contacts[0].push_link.assert_called_once_with(
            "[%s]: %s" % (Level.WARNING, "name"),
            self.description.graphite_url,
            body=str(self.description)
        )

        self.assertEqual(contacts[1].mock_calls, [])

        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('PushBullet', self.alert_key)
