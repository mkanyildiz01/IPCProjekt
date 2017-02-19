import socket
from enum import Enum


def rec_fields(clientsocket):
    data = clientsocket.recv(1024).decode()
    if not data:
        print("Connection closed")
        return True
    if len(data) == 50:
        print(data[0:10])
        print(data[10:20])
        print(data[20:30])
        print(data[30:40])
        print(data[40:50])
    elif len(data) == 18:
        print(data[0:6])
        print(data[6:12])
        print(data[12:18])
    elif len(data) == 98:
        print(data[0:14])
        print(data[14:28])
        print(data[28:42])
        print(data[42:56])
        print(data[56:70])
        print(data[70:84])
        print(data[84:98])
    else:
        # Lose / Win
        print(data)
        return True
    return False

class CommandType(Enum):
    UP = "up"
    RIGHT = "right"
    DOWN = "down"
    LEFT = "left"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
    try:
        # Verbindung herstellen (Gegenpart: accept() )
        clientsocket.connect(('localhost', 5050))
        msg = input("Name?")
        # Nachricht schicken
        clientsocket.send(msg.encode())
        # Antwort empfangen
        data = clientsocket.recv(1024).decode()
        if not data or not data=="OK":
            # Schließen, falls Verbindung geschlossen wurde
            clientsocket.close()
        else:
            while True:
                if rec_fields(clientsocket):
                    break
                while True:
                    msg = input("UP/RIGHT/DOWN/LEFT?")
                    # Nachricht schicken
                    if msg.lower() == "up":
                        clientsocket.send(CommandType.UP.value.encode())
                        break
                    elif msg.lower() == "down":
                        clientsocket.send(CommandType.DOWN.value.encode())
                        break
                    elif msg.lower() == "left":
                        clientsocket.send(CommandType.LEFT.value.encode())
                        break
                    elif msg.lower() == "right":
                        clientsocket.send(CommandType.RIGHT.value.encode())
                        break
    except socket.error as serr:
        print("Socket error: " + serr.strerror)