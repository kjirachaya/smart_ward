# consumers.py
import json
from channels.generic.websocket import WebsocketConsumer

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        # Called when a WebSocket connection is closed.
        pass

    def receive(self, text_data):
        # This is called when the consumer receives a message from the WebSocket
        message = json.loads(text_data)
        if message.get('type') == 'telemetry_created':
            self.send(text_data=json.dumps({'type': 'refresh_page'}))
