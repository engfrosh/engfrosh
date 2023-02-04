import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer


class ScavConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.has_perm("common_models.manage_scav"):
            self.close()
        async_to_sync(self.channel_layer.group_add)(
            'scav',
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'scav',
            self.channel_name
        )

    def receive(self, text_data):
        pass

    def send_notification(self, event):
        self.send(text_data=json.dumps({
            'photo': event['photo'],
            'id': event['id'],
            'team': event['team']
        }))

    def notify_trigger(photo: str, team: str, id: int) -> None:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('scav', {'type': 'send_notification',
                                                            'photo': photo, 'id': id, 'team': team})
