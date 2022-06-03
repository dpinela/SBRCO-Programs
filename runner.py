# Runs the UI, calls client.py

import tkinter as tk
import charm_select
from icons import StatusIcon
import client
import threading
import time
from os import stat, getenv


def check_charms():
    if time.time() - stat(getenv("tmp") + "/" + "charms.txt").st_mtime > 3:
        hide_charms()
    else:
        update_charms()


class main(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.c = charm_select.CharmWindow(self, width=600, height=450)
        self.c.grid(row=0, column=0)
        self.f = tk.Frame(self)
        self.f.grid(row=0, column=1, sticky="nw")
        self.ring_id = self.c.create_oval(-2, -2, -1, -1, outline="#ff0000", width=3)
        #self.R_ico = StatusIcon(self.f)
        #self.R_ico.switch("failed")
        #self.R_ico.grid(row=0, column=0, sticky="nw")
        #self.Ready = tk.StringVar()
        #self.Ready.set(" R? ")
        #tk.Button(self.f, textvariable=self.Ready, command=self.toggleR).grid(row=0, column=1, sticky="w")
        tk.Label(self.f, text="IP:").grid(row=2, column=0, sticky="w")
        self.ip = tk.Entry(self.f)
        self.ip.grid(row=2, column=1, sticky="we")
        tk.Label(self.f, text="Port:").grid(row=3, column=0, sticky="w")
        self.port = tk.Entry(self.f)
        self.port.grid(row=3, column=1, sticky="we")
        tk.Label(self.f, text="Room:").grid(row=4, column=0, sticky="w")
        self.room = tk.Entry(self.f)
        self.room.grid(row=4, column=1, sticky="we")
        tk.Label(self.f, text="PW:").grid(row=5, column=0, sticky="w")
        self.pw = tk.Entry(self.f)
        self.pw.grid(row=5, column=1, sticky="we")
        tk.Label(self.f, text="Player:").grid(row=6, column=0, sticky="w")
        self.player_index = tk.Entry(self.f)
        self.player_index.grid(row=6, column=1, sticky="we")
        self.srv_conn_B = tk.Button(self.f, text="Connect", command=self.confirm_mainsrv_conn)
        self.srv_conn_B.grid(row=7, column=0, sticky="we")
        self.ls_connect_ico = StatusIcon(self.f)
        self.ls_connect_ico.switch("loading")
        self.ls_connect_ico.grid(row=0, column=0, sticky="nw")
        self.ls_connect_tvar = tk.StringVar()
        self.ls_connect_tvar.set("Connecting to LiveSplit Server...")
        tk.Label(self.f, textvariable=self.ls_connect_tvar).grid(row=0, column=1, sticky="w")
        self.srv_connect_ico = StatusIcon(self.f)
        self.srv_connect_ico.switch("loading")
        self.srv_connect_ico.grid(row=1, column=0, sticky="nw")
        self.srv_connect_tvar = tk.StringVar()
        self.srv_connect_tvar.set("Connecting to Main Server...")
        tk.Label(self.f, textvariable=self.srv_connect_tvar).grid(row=1, column=1, sticky="w")
        self.livesplit_vars = [None, None, None]  # [player_index, split_index, ls_sock, charmsEquipped]
        self.server_vars = [None, None, None, b'',0]  # [player_index, split_index, srv_sock, b64]
        self.kill_main = [False]
        self.kill_ls = [False]
        gui_thread = threading.Thread(target=self.update_gui)
        livesplit_thread = threading.Thread(target=client.livesplit_setup,
                                            args=(self.livesplit_vars, self.kill_ls))
        self.threads = [None, livesplit_thread, gui_thread]
        gui_thread.start()
        livesplit_thread.start()

    def confirm_mainsrv_conn(self):
        """don't block GUI on clicking button, because we are waiting for the previous thread to die"""
        threading.Thread(target=self._confirm_mainsrv_conn).start()

    def _confirm_mainsrv_conn(self):
        ip, port = self.ip.get(), self.port.get()
        player_id = self.player_index.get()
        try:
            player_id = int(player_id)
            assert 0 <= player_id <= 3
        except (ValueError, AssertionError):
            print("player ID must be a number from 0-3")
            return
        old_t = self.threads[0]
        if old_t:
            self.kill_main[0] = True
            old_t.join()
            self.kill_main[0] = False
        t = self.start_mainsrv_conn(player_id, ip, port)
        self.threads[0] = t

    def start_mainsrv_conn(self, player_id, ip, port):
        main_thread = threading.Thread(target=client.main_setup, args=(self.server_vars,
                                                                       player_id,
                                                                       ip, port,
                                                                       self.kill_main))
        main_thread.start()
        return main_thread

    def update_gui(self):
        while True:
            if isinstance(self.livesplit_vars[1], int):
                self.place_ring(self.livesplit_vars[1])
            if self.server_vars[2]:
                self.srv_connect_ico.switch("finished")
            else:
                self.srv_connect_ico.switch("loading")
            self.ls_connect_ico.switch("finished")
            self.server_vars[1] = self.livesplit_vars[1]
            if self.server_vars[3]:
                self.gen_b64(self.server_vars[3])
            time.sleep(0.2)

    def place_ring(self, index):
        if index == -1:
            x1 = y1 = -2
            x2 = y2 = -1
        else:
            x1 = (index % 8) * 75 + 2
            y1 = index // 8 * 94 + 2
            x2 = x1 + 74
            y2 = y1 + 74
        self.c.coords(self.ring_id, x1, y1, x2, y2)

    def toggleR(self):
        if self.Ready.get() == " R? ":
            self.Ready.set(" R! ")
            self.R_ico.switch("finished")
            #client.send_ready()
        else:
            self.Ready.set(" R? ")
            self.R_ico.switch("failed")
            #client.send_not_ready()

    def gen_b64(self, b64):
        self.c.charmlist = charm_select.get_charmlist_from_b64(b64.decode())
        for i, charm in enumerate(self.c.charmlist):
                self.c.insert_charm(charm, i)
        #print("\nCharms:", self.c.charmlist)
        #print("Charmlist in base64:", charm_select.get_charm_order_b64(self.c.charmlist), end="\n\n\n")

    def connect_ls(self):
        client.main_livesplit()

    def connect_main(self):
        client.main_setup()



if __name__ == "__main__":
    runner = main()
    runner.grid()
    runner.mainloop()
    runner.kill_ls[0] = True
    runner.kill_main[0] = True
