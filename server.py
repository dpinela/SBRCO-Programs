# This is run on a public server which gets pinged by Restreamer.py and 

import socket
import threading
import select
import time
import Restreamer.keys

restream_key = Restreamer.keys.restream_key
player_wait_key = Restreamer.keys.player_wait_key
player_key = Restreamer.keys.player_key

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(("localhost", 9090))

serverSocket.listen()
playerCounter = []
custom_vars = {}
livesplitCounter = [-1, -1, -1, -1]
charmCounter = [b'\x00\x00\x00\x00\x00'] * 4

def connectServer():
    clientConnected, clientAddress = serverSocket.accept()
    playerCounter.append(clientConnected)
    k = f'thread{playerCounter}'
    custom_vars[k] = threading.Thread(target = connectServer)
    custom_vars[k].start()
    print(f"Accepted a connection request from {clientAddress[0]}:{clientAddress[1]}")
    listenToData(clientConnected)

def listenToData(clientConnected):
    no_response_i = 0
    while True:
        if not select.select([clientConnected], [], [], 10)[0]:
            #print("no data on select")
            continue  # todo: this will have a 10 second timeout before a client is connected, but after the socket is closed it will immediately go into an insta-infinite loop
        try:
            dataFromClient = clientConnected.recv(1024)
            print(dataFromClient)
        except ConnectionResetError:
            print(f"Connection lost ({clientConnected})\nresetting connection")
            clientConnected.close()
            return
        if not dataFromClient:
            if no_response_i > 100:
                print("didn't receive data from client after 100 attempts, closing connection...")
                clientConnected.close()
                #time.sleep(1)
                return
            #print("no data from client")
            no_response_i += 1
            continue
        # handle restreamer
        else:
            no_response_i = 0
        try:
            if (dataFromClient[:len(restream_key)].decode() == restream_key):
                print("Restreamer authenticated:", dataFromClient[:len(restream_key)].decode())
                additional_data = dataFromClient[len(restream_key):]
                if additional_data:
                    print("received additional data:", additional_data, "\nforwarding to connected clients...")
                    custom_vars["additional_restreamer_data"] = additional_data
                clientConnected.send(sum([(charm_index + 1) << 6 * i for i, charm_index in enumerate(livesplitCounter)]).to_bytes(3, "big")
                                     + b"".join(charmCounter))
                continue
            elif dataFromClient.decode() == player_wait_key:  # handle setup of player
                print("Player authenticated:", dataFromClient.decode(), "(waiting)")
                charm_list = custom_vars.get("additional_restreamer_data", None)
                if not charm_list:
                    continue
                try:
                    print("sending charmlist to player")
                    clientConnected.send(charm_list)
                except ConnectionResetError:
                    print("Player disconnected while waiting for charmlist, closing connection")
                    clientConnected.close()
                    return
                continue
        except UnicodeDecodeError:
            pass
        pw, charmEquipped,value = dataFromClient[:len(player_key)], dataFromClient[len(player_key):-1], dataFromClient[-1]
        # handle player
        try:
            if pw.decode() != player_key:
                print("invalid connection attempt, wrong passphrase:", pw, hex(value))
                continue
        except UnicodeDecodeError:
            print("connection attempt with wrong passphrase or bad format:", pw, hex(value))
            continue
        player_index, split_index = value & 0b11, (value >> 2) - 1
        print("Player authenticated:", pw.decode(), f"(player {player_index}, split {split_index})")
        charms = custom_vars.get("additional_restreamer_data", None)
        if charms:
            clientConnected.send(charms)
        livesplitCounter[player_index] = split_index
        charmCounter[player_index] = charmEquipped

thread1 = threading.Thread( target = connectServer)
thread1.start()
