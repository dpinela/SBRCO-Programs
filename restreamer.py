"""logic for connecting to the server as restreamer
and for managing information to send to the players"""
import base64
import socket
import threading
import select
import time
import list_permutations
import widget
import charm_select
import Restreamer.keys

restream_key = Restreamer.keys.restream_key
b64String = None

def connect_server(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        return sock
    except ConnectionResetError:
        print("Connection to Main Server reset while trying to connect")
        return
    except ConnectionRefusedError:
        print("Connection to Main Server refused while trying to connect")
        return
    except ConnectionAbortedError:
        print("Connection to Main Server aborted while trying to connect")
        return
    except TimeoutError:
        print("Main Server Connection timed out, maybe wrong ip or port?")
        return
    except socket.gaierror:
        print("Main Server address couldn't be resolved")
        return

def send_i_am_awake(main_socket):
    global state
    print('test')
    try:
        #print("sending to main server socket, selecting response:", end=" ")
        main_socket.send(restream_key.encode())
        response = select.select([main_socket], [], [], 5)
        #print(response)
        if not response[0]:
            return False
        data = main_socket.recv(1024)
        print(data)
    except ConnectionResetError:
        print("Connection to Main Server reset while trying to send/receive data")
        return
    except ConnectionAbortedError:
        print("Connection to Main Server aborted while trying to send/receive data")
        return
    except TimeoutError:
        print("Main Server Connection timed out, maybe wrong ip or port?")
        return
    except socket.gaierror:
        print("Main Server address couldn't be resolved")
        return

    progress = int.from_bytes(data[:3], "big")
    player_progress = [mask(progress, i,6) - 1 for i in range(4)]
    for i, player_split in enumerate(player_progress):
        state[i] = player_split
    charmsEquip = int.from_bytes(data[3:], "big")
    playerCharmsEquip = [mask(charmsEquip, i,40) for i in range(4)]
    for i in range (4):
        charmEquippedState[i] = playerCharmsEquip[3-i]
    return True

def mask(value: int, position: int, offset):
    return (value >> position * offset & (2**offset - 1))

def send_charms(socket, charms: int):
    socket.send(charms.to_bytes(20, "big"))

def generate_charm_list(charms: list):
    return list_permutations.index(charms)

def recv_charmdata_from_selector(charmdata: str, master: widget.widget):
    global b64String, charmlist
    b64String = charmdata
    print(b64String)
    charmlist.extend(charm_select.get_charmlist_from_b64(charmdata))
    widget.populate_charms(master, charmdata)

def send_b64_to_Server(main_socket):
    main_socket.send(restream_key.encode() + base64.b64decode(b64String))

def connect_to_server(ip, port):
    global b64String, kill_thread
    while True:
        if kill_thread[0]:
            print("main server thread received kill signal while connecting, terminating...")
            return
        main_socket = connect_server(ip, port)
        while main_socket:
            if kill_thread[0]:
                print("main server thread received kill signal while connected, terminating...")
                return
            send_success = send_i_am_awake(main_socket)
            if send_success is None:
                break
            if b64String != None:
                try:
                    send_b64_to_Server(main_socket)
                except:
                    print("Couldn't send to server")
                    continue
                b64String = None
            time.sleep(2)
        time.sleep(2)

def dispatch_server_start_thread():
    global con
    ip = con.ip.get() or "localhost"
    port = (int(con.port.get()) if con.port.get() else 9099)
    threading.Thread(target=_dispatch_server_start, args=(ip, port)).start()

def _dispatch_server_start(ip, port):
    global kill_thread, active_thread
    if active_thread[0]:
        kill_thread[0] = True
        active_thread[0].join()
        kill_thread[0] = False
    server_thread = threading.Thread(target=connect_to_server, args=(ip, port))
    server_thread.start()
    active_thread[0] = server_thread

if __name__ == "__main__":
    charmlist = []
    state = {0: -1, 1: -1, 2: -1, 3: -1}
    charmEquippedState = [0,0,0,0]
    active_thread = [None]
    kill_thread = [False]
    master = widget.widget(charmlist=charmlist, state=state, charmEquippedList = charmEquippedState)
    con = widget.control(master)
    master.bind_control(con)
    widget.tk.Button(con, text="Connect", command=dispatch_server_start_thread).grid(row=5, column=0)
    charm_select_window = widget.Chooser(master, send_charmdata=recv_charmdata_from_selector)
    master.mainloop()
    kill_thread[0] = True
