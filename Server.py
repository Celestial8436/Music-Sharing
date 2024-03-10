import socket
from threading import Thread
import time
import os
import random
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

IP_ADDRESS = '127.0.0.1'
PORT = 8050
SERVER = None
BUFFER_SIZE = 4096
clients = {}

is_dir_exists = os.path.isdir('shared_files')
print(is_dir_exists)
if (not is_dir_exists):
    os.makedirs('shared_files')


def acceptConnections():
    global SERVER
    global clients

    while True:
        client, addr = SERVER.accept()
        client_name = client.recv(4096).decode().lower()
        clients[client_name] = {
            "client": client,
            "address": addr,
            "connected_with": "",
            "file_name": "",
            "file_size": 4096
        }

        print(f"Connection established with {client_name} : {addr}")

        thread = Thread(target=handleClient, args=(client, client_name,))
        thread.start()


def handleClient(client, client_name):
    global clients

    while True:
        try:
            data = client.recv(BUFFER_SIZE)
            if not data:
                break

            message_type = data[:1].decode()
            message_data = data[1:].decode()

            if message_type == 'c':

                available_clients = [c for c in clients if c !=
                                     client_name and not c['connected_with']]
                if available_clients:

                    target_client = random.choice(available_clients)
                    clients[client_name]['connected_with'] = target_client
                    clients[target_client]['connected_with'] = client_name

                    file_name = f"{client_name}_{target_client}.txt"
                    clients[client_name]['file_name'] = file_name
                    clients[target_client]['file_name'] = file_name

                    if os.path.isfile(file_name):
                        file_size = os.path.getsize(file_name)
                    else:
                        file_size = 0

                    clients[client_name]['client'].send(
                        f't{file_name}#{file_size}'.encode())
                    clients[target_client]['client'].send(
                        f't{file_name}#{file_size}'.encode())

            elif message_type == 't':
                target_client = clients[client_name]['connected_with']
                with open(clients[client_name]['file_name'], 'rb') as f:
                    while True:
                        data = f.read(BUFFER_SIZE)
                        if not data:
                            break
                        clients[target_client]['client'].sendall(data)

            elif message_type == 'd':
                target_client = clients[client_name]['connected_with']
                clients[client_name]['connected_with'] = ""
                clients[target_client]['connected_with'] = ""

        except Exception as e:
            print(f"Error handling client {client_name}: {e}")
            break

    del clients[client_name]
    client.close()

def setup():
    print("\n\t\t\t\t\t\tIP MESSENGER\n")

    global PORT
    global IP_ADDRESS
    global SERVER

    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.bind((IP_ADDRESS, PORT))

    SERVER.listen(100)

    print("\t\t\t\tSERVER IS WAITING FOR INCOMMING CONNECTIONS...")
    print("\n")

    acceptConnections()


def ftp():
    global IP_ADDRESS

    authorizer = DummyAuthorizer()
    authorizer.add_user("lftpd", "lftpd", ".", perm="elradfmw")

    handler = FTPHandler

setup_thread = Thread(target=setup)
setup_thread.start()


ftp_thread = Thread(target=ftp)
ftp_thread.start()
