import hipchat
import os

from graphitepager.level import Level
from graphitepager.notifiers.base import BaseNotifier


class HipChatNotifier(BaseNotifier):

    def __init__(self, storage):
        super(HipChatNotifier, self).__init__(storage)
        self._rooms = set()

        env_vars = ['HIPCHAT_KEY', 'HIPCHAT_ROOM']
        self.enabled = all(x in os.environ for x in env_vars)
        if self.enabled:
            self._client = hipchat.HipChat(os.getenv('HIPCHAT_KEY'))
            self.add_room(os.getenv('HIPCHAT_ROOM'))

    def _notify(self,
                alert,
                level,
                description,
                html_description,
                nominal=None):
        colors = {
            Level.NOMINAL: 'green',
            Level.WARNING: 'yellow',
            Level.CRITICAL: 'red',
        }
        color = colors.get(level, 'red')

        description = str(html_description)
        self._notify_room_with_args(
            'Graphite-Pager',
            description,
            message_format='html',
            color=color,
        )

    def _notify_room_with_args(self, *args, **kwargs):
        for room in self._rooms:
            self._client.message_room(room, *args, **kwargs)

    def add_room(self, room):
        self._rooms.add(room)
