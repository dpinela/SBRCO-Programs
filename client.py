import socket
import select  # used for checking if socket has data pending
import time
import list_permutations
import base64
from charm_select import generate_autosplits, generate_charmlist_from_order
import tempfile
import Restreamer.keys

player_key = Restreamer.keys.player_key
player_wait_key = Restreamer.keys.player_wait_key
livesplit_varsClient = [None,None,None,b'']

def main_setup(srv_vars: list, player_index, ip="localhost", port=9090, killswitch=None):  # [player_index, split_index, srv_sock, b64]
    print("Running Main setup, trying to connect to server and await race information...")
    print("Welcome, Player", player_index)
    srv_vars[0] = player_index
    waiting_for_charms = True
    racing = False
    while True:
        srv_vars[2] = None
        ip = ip or "localhost"
        port = (int(port) if port else 9099)
        srv_sock = wait_main_connect(ip, port, killswitch)
        srv_vars[2] = srv_sock
        while waiting_for_charms:
            if killswitch and killswitch[0]:
                print("main server thread received kill signal while "
                      "waiting for charms, terminating...")
                srv_sock.close()
                return
            time.sleep(2)
            try:
                print("trying to tell server I'm waiting")
                dataFromSrv = send_to_srv(srv_sock, player_wait_key.encode())
                print("response:", dataFromSrv)
            except (ConnectionResetError, ConnectionAbortedError):
                print("Lost Connection to main server while waiting for charms, trying to reconnect...")
                break
            except Exception as e:
                print("failed to tell server I'm waiting or retrieve answer. server unavailable?", e)
                break
            if dataFromSrv is None:
                break
            elif dataFromSrv is False:
                print("no data on server")
                continue
##            try:
##                print("receiving data from server /init...")
##                dataFromSrv = srv_sock.recv(1024)
##                print("received data from server done:")
##            except (ConnectionResetError, ConnectionAbortedError):
##                print("Lost Connection to main server while waiting for charms, trying to reconnect...")
##                continue
##            if not dataFromSrv:
##                print("no data received")
##                continue
            print(dataFromSrv)
            srv_vars[3] = base64.b64encode(dataFromSrv)
            print("base64 serv:", srv_vars[3])
            charm_order = list_permutations.k_th_permutation(40, int.from_bytes(dataFromSrv, "big"))
            print("received charm order:", base64.b64encode(dataFromSrv))
            print("charm order:", charm_order)
            charms = generate_charmlist_from_order(charm_order)
            print("generating autosplits...")
            lss = generate_autosplits(charms)
            with open(f"sbrco.lss", "w") as f:
                f.write(lss)
            print(f"autosplits generated under: sbrco.lss")
            waiting_for_charms = False
            racing = True
        while racing:
            if killswitch and killswitch[0]:
                print("main server thread received kill signal while racing, terminating...")
                srv_sock.close()
                return
            time.sleep(1)
            try:
                PlayerData = convert_vars_to_bytes(srv_vars)
                print(player_key.encode() + livesplit_varsClient[3] + PlayerData)
                send_to_srv(srv_sock, player_key.encode() + livesplit_varsClient[3] + PlayerData)
            except:
                break
            if not select.select([srv_sock], [], [], 1)[0]:
                # while running, the client will mostly go into this and the select will time out, causing a 1s wait time + 1s default wait
                continue
            try:
                dataFromSrv = srv_sock.recv(1024)
            except ConnectionResetError:
                print("Lost Connection to main server while racing, trying to reconnect...")
                break
            if not dataFromSrv:
                continue
            # doesn't really need to receive any data atm??
            #racing = False
        if not waiting_for_charms and not racing:
            return
        print("Lost Connection to Main Server")

def wait_main_connect(ip, srv_port, killswitch=None):
    srv_sock = main_connect(ip, srv_port)
    while srv_sock is None:
        if killswitch and killswitch[0]:
            print("main server thread received kill signal while connecting, terminating...")
            return
        print("Couldn't establish connection to Main Server. Retrying...")
        srv_sock = main_connect(ip, srv_port)
        time.sleep(5)
    print("Connected to Main Server!")
    return srv_sock

def main_connect(ip, port):
    print("Trying to connect to Main Server...")
    try:
        srv_sock = socket.socket()
        srv_sock.connect((ip, port))
        return srv_sock
    except ConnectionRefusedError:
        print("Main Server refused Connection, maybe server application is not running?")
        return
    except TimeoutError:
        print("Main Server Connection timed out, maybe wrong ip or port?")
        return
    except socket.gaierror:
        print("Main Server address couldn't be resolved")
        return

def send_to_srv(srv_sock, command: bytes) -> bytes:
    try:
        srv_sock.send(command)
    except:
        print("Main Server seems to be unavailable.")
        return None
    socket_ready = select.select([srv_sock], [], [], 5)
    if socket_ready[0]:
        return srv_sock.recv(1000)
    return False

def convert_vars_to_bytes(srv_vars: list) -> bytes:
    player_index = srv_vars[0]
    split_index = srv_vars[1]
    if split_index is None:
        split_index = -1
    # ready = srv_vars[3]
    value = player_index + (split_index + 1 << 2)  # split index starts at -1 so for unsigned, add 1
    return value.to_bytes(1, "big")




def livesplit_setup(ls_vars: list, killswitch=None):  # [player_index, split_index, ls_sock, charmsEquipped]
    print("Running Livesplit setup, trying to connect to Livesplit server")

    # Read from Text File created by my own Modified Assembly-Csharp
    while(True):
        try:
            with open(tempfile.gettempdir() + "/charms.txt") as f:
                lines = f.readlines()
            counter = 0
            for i in range(len(lines[1])-1):
                counter += int(lines[1][i])
            charms_equipped_int = int(lines[0][:-1],2)
            print(charms_equipped_int.to_bytes(5,"big"))
            livesplit_varsClient[3] = charms_equipped_int.to_bytes(5,"big")
            ls_vars[1] = int(counter)
            time.sleep(1)
        except:
            print("Couldn't open file, make sure you started Hollow Knight first")
            time.sleep(1)

    # Alternatively, use Livesplit server and read the charm Index from livesplit:
    # while True:
        # if killswitch and killswitch[0]:
        #     print("livesplit thread received kill signal, terminating...")
        #     return
        # ls_vars[2] = None
        # ls_sock = wait_ls_connect(killswitch)
        # ls_vars[2] = ls_sock
        # split_index = get_split_index(ls_sock)
        # while split_index is not None and split_index is not False:
        #     if killswitch and killswitch[0]:
        #         print("livesplit thread received kill signal while playing, terminating...")
        #         ls_sock.close()
        #         return
        #     new_split_index = get_split_index(ls_sock)
        #     if new_split_index != split_index:
        #         print("split:", new_split_index)
        #         split_index = new_split_index
        #     ls_vars[1] = split_index
        #     time.sleep(1)
        # print("Lost Connection to Livesplit")

def wait_ls_connect(killswitch):
    ls_port = 16834
    ls_sock = ls_connect(ls_port)
    while ls_sock is None:
        if killswitch and killswitch[0]:
            print("livesplit thread received kill signal while connecting, terminating...")
            return
        print("Livesplit server not started? Trying to connect to Livesplit...")
        ls_sock = ls_connect(ls_port)
        time.sleep(5)
    print("Connected to Livesplit Server!")
    return ls_sock

def ls_connect(port):
    try:
        ls_sock = socket.socket()
        ls_sock.connect(('localhost', port))
        return ls_sock
    except ConnectionRefusedError:
        return

def send_to_ls(ls_socket, command: str) -> str:
    try:
        ls_socket.send(command.encode())
    except:
        print("Livesplit Server seems to be unavailable. "
              "Consider checking LiveSplit or closing the connection using CTRL+C")
        return None
    socket_ready = select.select([ls_socket], [], [], 1)
    if socket_ready[0]:
        try:
            return ls_socket.recv(1000).decode()
        except:
            return False
    print("Livesplit Server socket not ready")
    return False

def get_split_index(ls_socket):
    ls_data = send_to_ls(ls_socket, "getsplitindex\r\n")
    if ls_data is False:
        return ls_data
    elif ls_data is None:
        return None
    return int(ls_data)


if __name__ == "__main__":
    server_vars = [None, None, None, b'']
    livesplit_vars = [None, None, None]
    livesplit_setup(livesplit_vars)
    main_setup(server_vars, 0)
