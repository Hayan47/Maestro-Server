from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Robot
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
from django.core.exceptions import ObjectDoesNotExist

user_connections = {}
robot_connections = {}
pairings = {}

class ControlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.parse_connection_params()
        print(f"Connection Type: {self.connection_type}")
        await self.add_to_connections()
        await self.attempt_pairing()


    async def parse_connection_params(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        
        self.token = query_params.get('token', [None])[0]
        self.connection_type = query_params.get('connection_type', ['unknown'])[0]

        if self.connection_type == "user":
            self.id = self.get_user_id(self.token)
        else:
            self.id = self.scope.get('robot_id')
        self.client_ip = self.scope['client'][0]
        self.user = self.scope['user']
        self.robot_authenticated = self.scope.get('robot', False)


    
    async def handle_robot_connection(self):
        self.robot = await self.get_robot()
        if self.robot:
            await self.accept()
            print(f"Robot {self.robot.name} connected from {self.client_ip}")
        else:
            await self.close()


    async def handle_user_connection(self):
        if self.token:
            self.user = await self.get_user_from_token(self.token)
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.robot = await self.get_user_robot(self.user)
        if self.robot:
            await self.accept()
            print(f"User {self.user.username} connected from {self.client_ip}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.remove_from_connections()
        await self.remove_from_pairing()
        print(f"Disconnected: {self.connection_type} {self.id}")
    
    async def receive(self, text_data):
        print(pairings)
        print(text_data)
        data = json.loads(text_data)
        if self.connection_type == 'user':
            await self.handle_user_message(data)
        elif self.connection_type == 'robot':
            await self.handle_robot_message(data)

    async def handle_user_message(self, data):
        robot_id = pairings.get(self.id)
        if robot_id:
            robot_consumer = robot_connections.get(robot_id)
            if robot_consumer:
                await robot_consumer.send(text_data=json.dumps({
                    'type': 'command',
                    'command': data.get('command')
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Robot is not connected'
                }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'No robot paired'
            }))

    async def handle_robot_message(self, data):
        user_id = next((user_id for user_id, robot_id in pairings.items() if robot_id == self.id), None)
        if user_id:
            user_consumer = user_connections.get(user_id)
            if user_consumer:
                await user_consumer.send(text_data=json.dumps({
                    'type': 'status',
                    'status': data.get('status')
                }))

    async def add_to_connections(self):
        if self.connection_type == 'user' and self.user.is_authenticated:
            user_connections[self.id] = self
            await self.accept()
        elif self.connection_type == 'robot' and self.scope.get('is_robot', False):
            robot_connections[self.id] = self
            await self.accept()
        else:
            print("Not Authenticated")
            # await self.send({
            #     "type": "websocket.close",
            #     "code": 403,  # Custom code for authentication failure
            #     "reason": "Authentication required"
            # })
            await self.close()

    async def remove_from_connections(self):
        if self.connection_type == 'user':
            user_connections.pop(self.id, None)
        else:
            robot_connections.pop(self.id, None)

    async def attempt_pairing(self):
        if self.connection_type == 'user':
            robot_id = await self.get_robot_id_for_user(self.id)
            if robot_id in robot_connections:
                pairings[self.id] = robot_id
                await self.send(text_data=json.dumps({
                    'type': 'pairing',
                    'status': 'paired',
                    'robot_id': robot_id
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'pairing',
                    'status': 'waiting',
                    'message': 'Waiting for robot to connect'
                }))
        else:  # robot
            user_id = await self.get_user_id_for_robot(self.id)
            print(f"user_id: {user_id}")
            print(f"user_connections: {user_connections}")
            print(type(user_id))
            print(user_id in user_connections)
            user_id = int(user_id)
            if user_id in user_connections:
                pairings[user_id] = self.id
                await user_connections[user_id].send(text_data=json.dumps({
                    'type': 'pairing',
                    'status': 'paired',
                    'robot_id': self.id
                }))

    async def remove_from_pairing(self):
        if self.connection_type == 'user':
            pairings.pop(self.id, None)
        else:
            user_id = next((user_id for user_id, robot_id in pairings.items() if robot_id == self.id), None)
            if user_id:
                pairings.pop(user_id, None)
                if user_id in user_connections:
                    await user_connections[user_id].send(text_data=json.dumps({
                        'type': 'pairing',
                        'status': 'disconnected',
                        'message': 'Robot disconnected'
                    }))


    @database_sync_to_async   
    def get_robot(self):
        try:
            robot =  Robot.objects.get(self.id)
            return robot
        except Robot.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_robot(self, user):
        try:
            robot =  Robot.objects.get(user=user)
            return robot
        except Robot.DoesNotExist:
            return None

    @database_sync_to_async  
    def get_robot_id_for_user(self, user_id):
        try:
            robot = Robot.objects.get(user_id=user_id)
            return str(robot.id)  
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def get_user_id_for_robot(self, robot_id):
        try:
            robot = Robot.objects.get(id=robot_id)
            return str(robot.user_id)  
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            print("KMKLMLKMKLMLKMLK")
            print(user_id)
            user = User.objects.get(id=user_id)
            return user
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None


    def get_user_id(self, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            print(type(user_id))
            return user_id
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None