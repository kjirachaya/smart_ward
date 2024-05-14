import socketio
# from utils import config
from config import Config
import json
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Chat, ChatMessage
from .serializers import MessageSerializer
from asgiref.sync import sync_to_async

# mgr = socketio.AsyncRedisManager(Config.REDIS_URL)
mgr = socketio.AsyncRedisManager("redis://127.0.0.1:6379")
sio = socketio.AsyncServer(
    async_mode="asgi", client_manager=mgr, cors_allowed_origins="*"
)


# # establishes a connection with the client
# @sio.on("connect")
# async def connect(sid, env, auth):
#     if auth:
#         chat_id = auth["chat_id"]
#         print("SocketIO connect")
#         sio.enter_room(sid, chat_id)
#         await sio.emit("connect", f"Connected as {sid}")
#     else:
#         raise ConnectionRefusedError("No auth")

# establishes a connection with the client
@sio.on("connect")
async def connect(sid, env):
    # chat_id = "96a3825a-3c6c-4a6b-9136-6b3336c463aa"
    print("SocketIO connect")
    await sio.enter_room(sid, "ward")
    await sio.enter_room(sid, "form31")
    await sio.enter_room(sid, "form70")
    await sio.enter_room(sid, "bed")
    await sio.emit("connect", f"Connected as {sid}")

# communication with orm
def store_and_return_message(data):
    data = json.loads(data)
    sender_id = data["sender_id"]
    chat_id = data["chat_id"]
    text = data["text"]
    sender = get_object_or_404(User, pk=sender_id)
    chat = get_object_or_404(Chat, short_id=chat_id)

    instance = ChatMessage.objects.create(sender=sender, chat=chat, text=text)
    instance.save()
    message = MessageSerializer(instance).data
    message["chat"] = chat_id
    message["sender"] = str(message["sender"])
    return message

@sio.on("message_ward")
async def print_message_ward(sid, data):
    print("Socket ID", sid)
    await sio.emit("update_ward", "update", room="ward")

@sio.on("message_form31")
async def print_message_form31(sid, data):
    print("Socket ID", sid)
    await sio.emit("update_form31", "update", room="form31")

@sio.on("message_form70")
async def print_message_form70(sid, data):
    print("Socket ID", sid)
    await sio.emit("update_form70", "update", room="form70")

# listening to a 'message' event from the client
@sio.on("message")
async def print_message(sid, data):
    print("Socket ID", sid)
    message = await sync_to_async(store_and_return_message, thread_sensitive=True)(
        data
    )  # communicating with orm
    print(message['chat'])
    await sio.emit("new_message", message, room=message["chat"])

@sio.on("disconnect")
async def disconnect(sid):
    print("SocketIO disconnect")
