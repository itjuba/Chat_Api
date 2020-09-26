from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer,AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from asgiref.sync import sync_to_async
from accounts.models import User
from chat.models import Message


class ChatConsumer(AsyncWebsocketConsumer):


    @database_sync_to_async
    def crt(self, username):
        user = User.objects.get_or_create(username=username)
        return user


    async def init_chat(self, data):
        print('init ')
        print(data)
        username = self.user.username
        user = await self.crt(username)
        content = {
            'command': 'init_chat'
        }
        if not user:
            content['error'] = 'Unable to get or create User with username: ' + username
            await self.send(text_data=json.dumps(content))
        content['success'] = 'Chatting in with success with username: ' + username
        await self.send(text_data=json.dumps(content))

    @database_sync_to_async
    def get_m(self):
        result = []
        messages = Message.last_50_messages()
        for m in messages:
            result.append({
            'id': str(m.id),
            'author': m.author.username,
            'content': m.content,
            'created_at': str(m.created_at)
            }
        )
        return result
    async def fetch_messages(self, data):
        print('fetched !')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'messages': await self.get_m()
            }
        )
        print('done')

    @database_sync_to_async
    def message_to_json(self, message):
        print('message')
        return {
            'id': str(message.id),
            'author': message.author.username,
            'content': message.content,
            'created_at': str(message.created_at)
        }

    @database_sync_to_async
    def get_new_message(self,author,text):
        author_user, created =  User.objects.get_or_create(username=author)
        message = Message.objects.create(author=author_user, content=text)
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message)
        }
        return content

    async def new_message(self, data):
        print('new message')
        author = data['from']
        text = data['text']
        self.send_chat_message(await self.get_new_message(author,text))

    commands = {
        'init_chat': init_chat,
        'fetch_messages': fetch_messages,
        'new_message': new_message
    }

    async def connect(self):
        self.room_name = 'room'
        self.room_group_name = 'chat_%s' % self.room_name
        self.user = self.scope["user"]

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def com(self,text_data_json):
       await self.commands[text_data_json['command']](self, text_data_json)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        message = text_data_json['command']
        print(message)
        await self.com(text_data_json)
        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'fetch_messages',
                    'message': message
                },
            )

    @database_sync_to_async
    def send_chat_message(self, message):
            print('send')
            print(message)
            self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['messages']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'command': 'messages',
            # 'username':'username',
            'messages': message,

        }))

