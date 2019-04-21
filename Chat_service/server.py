import socket
import threading
import json


class ChatServer:
    server_socket = None
    # Define socket host and port
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 8000
    # List of connected clients
    clients_list = list()
    # Dictionary of rooms with client list
    rooms = ["#geral"]

    # List of Commands
    commands = ("#Commands available:\r\n"
                     + "(Join <room>): /join:<room>\r\n"
                     + "(Create a room): /create:<room>\r\n"
                     + "(Exit the room): /exit\r\n"
                     + "(Kick client): /kick:<client>\r\n"
                     + "(Ban client): /ban:<client>\r\n"
                     + "(Disban client): /disban:<client>\r\n"
                     + "(Clear Chat): /clear\r\n"
                     + "(Show me this): /help")

    def __init__(self):
        # Create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.SERVER_HOST, self.SERVER_PORT))
        self.server_socket.listen(1)
        print("Listening on port %s ..." % self.SERVER_PORT)
        self.receive_messages_in_a_new_thread()

    # Recebe Mensagens do servidor
    def receive_messages_in_a_new_thread(self):
        while True:
            # Wait for client connections
            client_connection, (ip, port) = self.server_socket.accept()

            # Save data from the connected client
            client = {"Conn": client_connection, "Ip": ip, "Port": port, "Name": None,
                      "Room": None, "Mod": [], "Bans": []}

            print("Connected to ", ip, ":", str(port))

            # Create thread
            thread = threading.Thread(target=self.client_handle, args=(client,))
            thread.start()
        # Close socket
        self.server_socket.close()


    def client_handle(self, client):
        name = None
        client_connection = client["Conn"]
        while client["Name"] is None:
            name = client_connection.recv(1024).decode()
            name_exists = False
            for clients in self.clients_list:
                if clients["Name"] == name:
                    server_message = "NameExist:This name is taken"
                    name_exists = True
                    client_connection.sendall(server_message.encode())
                    break
            if not name_exists:
                client["Name"] = name.lower()
                client["Room"] = self.rooms[0]
                self.clients_list.append(client)
        message_join = "Server:" + client["Name"] + " has joined " + client["Room"]
        msg_welcome = "Welcome to the chat server " + name + "\nYou dont know the comands? just write /help"
        self.server_messages(client_connection, msg_welcome)
        self.broadcast(client, message_join)
        self.receive_messages(client)

    def receive_messages(self, client):
        client_connection = client["Conn"]
        while True:
            client_connection.send(json.dumps(self.rooms).encode())
            client_msg = client_connection.recv(1024)
            if not client_msg:
                break
            message = client_msg.decode('utf-8')

            if message == "/disconnect":
                break
            elif "/help" in message:
                self.list_commands(client_connection)
            elif "/create" in message:
                room = message.split(':')[2].lower()
                self.create_room(client, room)
                print(self.rooms)
            elif "/join" in message:
                room = message.split(':')[2].lower()
                self.join_room(client, room)
            elif "/kick" in message:
                client_kick = message.split(':')[2].lower()
                self.kick_client(client, client_kick)
            elif "/ban" in message:
                client_ban = message.split(':')[2].lower()
                self.ban_client(client, client_ban)
                print(self.clients_list)
            elif "/disban" in message:
                client_disban = message.split(':')[2].lower()
                self.remove_ban(client, client_disban)
                print(self.clients_list)
            elif "/exit" in message:
                self.exit_room(client)
            elif "/clear" in message:
                msg = "Clear"
                self.server_messages(client_connection, msg)
            else:
                self.broadcast(client, message)
        print('Client disconnected...')
        client_connection.close()

    # Send messages to clients in the same room
    def broadcast(self, client, message):
        room = client["Room"]
        client_connection = client["Conn"]
        conn = None
        for clients in self.clients_list:
            conn = clients["Conn"]
            if room.lower() == clients["Room"].lower() and client_connection is not clients["Conn"]:
                conn.sendall(message.encode())

    def broadcast_all(self, room, message):
        conn = None
        for clients in self.clients_list:
            conn = clients["Conn"]
            if room.lower() == clients["Room"].lower():
                conn.sendall(message.encode())

    def server_messages(self, client_connection, message):
        client_connection.sendall(message.encode())

    def list_commands(self, client_connection):
        client_connection.sendall(self.commands.encode())

    def create_room(self, client, new_room):

        room_exists = False
        new_room = "#" + new_room
        for room in self.rooms:
            if new_room.lower() == room.lower():
                room_exists = True
                message = "Error:Room with this name already exists"
                self.server_messages(client["Conn"], message)

        if not room_exists:
            self.rooms.append(new_room)
            client["Mod"].append(new_room)
            message = "Server:Room " + new_room + " was created"
            self.server_messages(client["Conn"], message)

    def join_room(self, client, room):
        if room not in self.rooms:
            message = "Error:Room does not exist"
            self.server_messages(client["Conn"], message)
        elif room in client["Bans"]:
            message = "Error:You are banned from the room " + room
            self.server_messages(client["Conn"], message)
        else:
            client["Room"] = room
            message_client = "Server:You has joined the room " + room
            message = "Server:" + client["Name"] + ' has joined the room ' + room
            self.server_messages(client["Conn"], message_client)
            self.broadcast(client, message)

    def kick_client(self, client, client_kick):
        client_exist = True
        client_dic = None
        for dic in self.clients_list:
            if client_kick == dic["Name"]:
                client_dic = dic
                client_exist = True
                break
            else:
                client_exist = False
        if not client_exist:
            message = "Error:Client with the name '" + client_kick + "'" + " does not exist"
            self.server_messages(client["Conn"], message)
            return

        if client["Room"] not in client["Mod"]:
            message = "Error:You do not have permissions in this room"
            self.server_messages(client["Conn"], message)
            return

        elif client_dic["Room"] != client["Room"]:
            message = "Error:Client with the name '" + client_kick + "'" + " is not in the room"
            self.server_messages(client["Conn"], message)
            return
        room = client["Room"]
        message = "Server:" + client_kick + " was kicked of the room"
        message_client_kick = "Kick:You was kicked out of the room"
        self.server_messages(client_dic["Conn"], message_client_kick)
        self.join_room(client_dic, self.rooms[0])
        self.broadcast_all(room, message)

    def ban_client(self, client, client_ban):
        # Verificar se client_ban existe
        client_exist = True
        room = client["Room"]
        client_dic = dict()
        for dic in self.clients_list:
            if client_ban == dic["Name"]:
                client_dic = dic
                client_exist = True
                break
            else:
                client_exist = False

        if not client_exist:
            message = "Error:Client with the name '" + client_ban + "'" + " does not exist"
            self.server_messages(client["Conn"], message)
            return
        # Verificar se cliente tem Mod
        if client["Room"] not in client["Mod"]:
            message = "Error:You do not have permissions in this room"
            self.server_messages(client["Conn"], message)
            return
        # Verifica se o client_ban esta banido
        elif room in client_dic["Bans"]:
            message = "Error:Client with the name '" + client_ban + "'" + " is banned"
            self.server_messages(client["Conn"], message)
            return
        # Verificar se client_ban esta na sala, ban o cliente e envia para sala1
        elif room == client_dic["Room"]:
            client_dic["Bans"].append(room)
            message_client_ban = "Ban:You was banned of the room " + room
            message = "Server:" + client_ban + " was banned of the room" + room
            self.server_messages(client_dic["Conn"], message_client_ban)
            self.join_room(client_dic, self.rooms[0])
            self.broadcast_all(room, message)

            return
        # Adiciona o cliente a lista de bans da sala
        else:
            client_dic["Bans"].append(room)
            message_client_ban = "Ban:You was banned of the room " + room
            message = "Server:" + client_ban + " was banned of the room"
            self.server_messages(client_dic["Conn"], message_client_ban)
            self.broadcast_all(room, message)
            return

    def remove_ban(self, client, client_disban):
        client_exist = True
        room = client["Room"]
        client_dic = dict()
        # Verificar se o utilizador a banir existe
        for dic in self.clients_list:
            if client_disban == dic["Name"]:
                client_dic = dic
                client_exist = True
                break
            else:
                client_exist = False
        if not client_exist:
            message = "Error:Client with the name '" + client_disban + "'" + " does not exist"
            self.server_messages(client["Conn"], message)
            return
        # Verificar se o utilizador tem mod da  sala
        if client["Room"] not in client["Mod"]:
            message = "Error:You do not have permissions in this room"
            self.server_messages(client["Conn"], message)
            return
        # verficar se o cliente esta na sala de bans
        elif room not in client_dic["Bans"]:
            message = "Server:Client with the name '" + client_disban + "'" + " is not banned"
            self.server_messages(client["Conn"], message)
            return
        else:
            client_dic["Bans"].remove(room)
            message_disban = "Server:You was disban of the room " + room
            message = "Server:" + client_disban + " was disban of the room"
            self.server_messages(client_dic["Conn"], message_disban)
            self.broadcast_all(room, message)

    def exit_room(self, client):
        message = "leftRoom:You left the room " + client["Room"]
        self.server_messages(client["Conn"], message)
        self.join_room(client, self.rooms[0])



if __name__ == "__main__":
    ChatServer()
