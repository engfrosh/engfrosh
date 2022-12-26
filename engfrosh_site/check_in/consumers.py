import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer


class CheckInConsumer(WebsocketConsumer):

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'default',
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'default',
            self.channel_name
        )

    def receive(self, text_data):
        pass

    def send_notification(self, event):
        self.send(text_data=json.dumps({
            'location': event['location'],
            'size': event['size'],
            'team': event['team']
        }))

    def notify_trigger(location: str, size: str, team: str) -> None:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('default', {'type': 'send_notification',
                                                            'location': location, 'size': size, 'team': team})
