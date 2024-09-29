import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from channels.exceptions import StopConsumer


class CheckInConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.has_perm("common_models.check_in"):
            self.close()
        async_to_sync(self.channel_layer.group_add)(
            'checkin',
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'checkin',
            self.channel_name
        )
        raise StopConsumer()

    def receive(self, text_data):
        pass

    def send_notification(self, event):
        self.send(text_data=json.dumps({
            'location': event['location'],
            'size': event['size'],
            'team': event['team'],
            'name': event['name'],
            'ssize': event['ssize'],
        }))

    def notify_trigger(location: str, size: str, ssize: str, team: str, name: str) -> None:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('checkin', {'type': 'send_notification',
                                                            'location': location, 'size': size,
                                                            'team': team, 'name': name, 'ssize': ssize})
