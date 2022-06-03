# Class Called by Restreamer.py, handles all of the UI

import tkinter as tk
import charm_select
import threading
import os
import time
from random import choice

width = 1800
height = 1012

w_offset = 38
h_offset = 36
h_offset *= 2

w_side = (width - 22 * w_offset * 2) // 2
h_side = (height - 13 * h_offset) // 2

class widget(tk.Tk):
    def __init__(self, charmlist=None, state=None, charmEquippedList = None, *args, **kw):
        tk.Tk.__init__(self, *args, **kw)
        self.title("Restream")
        self.c = tk.Canvas(self, width=width, height=height, bg="#006600")
        self.c.grid(row=0, column=0)
        self.charms_fnames = os.listdir("Resources/UI/charms")
        self.rings_fnames = os.listdir("Resources/UI/rings")
        self.border_fnames = os.listdir("Resources/UI/borders")
        self.images = {}
        self.rings = {}
        self.borders = {}
        self.lock = threading.Lock()

        for charm_fname in self.charms_fnames:
            cimg = tk.PhotoImage(file="Resources/UI/charms/" + charm_fname)
            cimg = cimg.subsample(2)
            self.images[charm_fname.split(".")[0]] = cimg

        for ui_overlay in self.rings_fnames:
            rimg = tk.PhotoImage(file="Resources/UI/rings/" + ui_overlay)
            rimg = rimg.subsample(2)
            self.rings[ui_overlay.split(".")[0]] = rimg

        for video_overlay in self.border_fnames:
            bimg = tk.PhotoImage(file="Resources/UI/borders/" + video_overlay)
            self.borders[video_overlay.split(".")[0]] = bimg

        #background = tk.PhotoImage(file="bg_sketch.png")
        #background = tk.PhotoImage(file="bg_draft01.png")
        #background = tk.PhotoImage(file="bg_draft02.png")
        self.background = tk.PhotoImage(file="Resources/UI/bg_black.png")
        self.timer = tk.PhotoImage(file="Resources/UI/timer.png")

        self.c.create_image(2, 2, image=self.background, anchor="nw")  # canvas will cut off 2 pixels from the top left for unknown reasons

        self.border_tk_ids = {}
        for k, v in self.borders.items():
            self.border_tk_ids[k] = self.c.create_image(-width, -height, image=v, anchor="nw")

        self.c.create_image(2, 2, image=self.timer, anchor="nw")

        self.finish_tex  = tk.PhotoImage(file="Resources/UI/glows/finish_tex.png")
        self.finish_tex1 = tk.PhotoImage(file="Resources/UI/glows/finish_tex4.png")
        self.finish_tex2 = tk.PhotoImage(file="Resources/UI/glows/finish_tex5.png")
        self.finish_tex3 = tk.PhotoImage(file="Resources/UI/glows/finish_tex6.png")

        ## logic
        self.charmlist = charmlist or [*self.images]
        self.charm_tk_ids = {}

        for i, charm_name in enumerate(self.charmlist):
            tk_id = self.c.create_image(-74, -74, image=self.images[charm_name], anchor="nw")
            self.charm_tk_ids[charm_name] = tk_id

        self.state = {"r": -1, "c": -1, "g": -1, "p": -1}
        self.server_state = state or {0: 0, 1: 0, 2: 0, 3: 0}
        self.player_dict = {0:"r", 1:"c", 2:"g", 3:"p"}
        self.tk_ring_ids = {}
        self.finished_ids = []

        # create all rings as canvas items already, but put them offscreen to hide them
        # this way, we won't need to keep track of newly created ones and keep destroying/creating new ones
        for ring, photoimage in self.rings.items():
            tk_id = self.c.create_image(-148, -148, image=photoimage, anchor="nw")
            self.tk_ring_ids[photoimage] = tk_id

        gui_thread = threading.Thread(target=self.gui_thread)
        gui_thread.start()


        # Charms Equipped UI
        if (charmEquippedList is None): charmEquippedList = [0,0,0,0]
        self.charmsEquippedIndices = charmEquippedList
        self.tempList = self.charmsEquippedIndices.copy()
        self.charms_equipped = [0 for i in range(4)]
        self.tk_imgID = [[]] * 4
        self.imagesEquippedCharms = [self.images[imgString].subsample(2) for imgString in sorted(self.images,key = lambda k: charm_select.vanilla_charm_order.index(k))]
        self.updateCharms()
        changeCharmsThread = threading.Thread(target = self.changeCharms).start()

    def changeCharms(self):
        # Update Equipped Charms every 2 seconds. tempList is the last State of equipped Charms
        while(True):
            for i in range(4):
                if (self.tempList[i] != self.charmsEquippedIndices[i]):
                    self.equippedCharm_to_img(i)
                    self.generateEquippedCharms(i)
                    self.tempList[i] = self.charmsEquippedIndices[i]
            time.sleep(2)

    def updateCharms(self):
        for i in range (4):
            self.equippedCharm_to_img(i)
            self.generateEquippedCharms(i)

    def equippedCharm_to_img(self,player):
        charms_equipped_temp = []
        for j,char in enumerate(f"{self.charmsEquippedIndices[player]:040b}"):
            if char == "1":
                charms_equipped_temp.append(self.imagesEquippedCharms[j])
        self.charms_equipped[player] = charms_equipped_temp

    def generateEquippedCharms(self,player):
        self.removeCharms(player)
        tmpList = []
        for j,equippedCharmImg in enumerate(self.charms_equipped[player]):
            # Layout for corners:
            # if player == 0:
            #     tmpList.append(self.c.create_image(width - 50 - 30*j,0, image = equippedCharmImg, anchor = "nw"))
            # if player == 1:
            #     tmpList.append(self.c.create_image(width - 50 - 30*j,height-50, image = equippedCharmImg, anchor = "nw"))
            # if player == 2:
            #     tmpList.append(self.c.create_image(30*j,height - 50, image = equippedCharmImg, anchor = "nw"))
            # if player == 3:
            #     tmpList.append(self.c.create_image(30*j,0, image = equippedCharmImg, anchor = "nw"))
            if player == 0:
                tmpList.append(self.c.create_image(width/2 + 145,110 + 30*j, image = equippedCharmImg, anchor = "nw"))
            if player == 1:
                tmpList.append(self.c.create_image(width/2 + 145,height-155 - 30*j, image = equippedCharmImg, anchor = "nw"))
            if player == 2:
                tmpList.append(self.c.create_image(width/2 - 182,height-155 - 30*j, image = equippedCharmImg, anchor = "nw"))
            if player == 3:
                tmpList.append(self.c.create_image(width/2 - 182,110 + 30*j, image = equippedCharmImg, anchor = "nw"))
        self.tk_imgID[player] = tmpList

    def removeCharms(self,player):
        for i in self.tk_imgID[player]:
            self.c.delete(i)
        self.update()

    # methods for charmList

    def update_charmlist(self, charmlist):
        self.charmlist = charmlist

    def populate_charms(self):
        for i, charm_name in enumerate(self.charmlist):
            self.c.coords(self.charm_tk_ids[charm_name],
                          self.charm_positions[i][0] * (w_offset) + w_side,
                          self.charm_positions[i][1] * (h_offset) + h_side)

    def bind_control(self, con):
        self.con = con

    def gui_thread(self):
        old_state = self.server_state.copy()
        while True:
            try:
                self.winfo_exists()
            except (tk._tkinter.TclError, RuntimeError):
                print("widget application destroyed, terminating gui thread...")
                break
            for i in range(4):
                if old_state[i] != self.server_state[i]:
                    print("player", i, "changed split to", self.server_state[i])
                    if old_state[i] < self.server_state[i]:
                        threading.Thread(target = lambda : self.advancePlayer(i)).start()
                        old_state[i] += 1
                    else:
                        threading.Thread(target = lambda : self.rewindPlayer(i)).start()
                        old_state[i] -= 1
            time.sleep(0.1)
            # self.c.update()

    def advancePlayer(self, player):

        # print(player,self.con,self.con.get(player),self.con.get)
        time.sleep(self.con.get(player))
        self.lock.acquire()
        self.advance(self.player_dict[player])
        self.lock.release()
        self.update()

    def rewindPlayer(self, player):
        time.sleep(self.con.get(player))
        self.lock.acquire()
        self.go_back(self.player_dict[player])
        self.lock.release()
        
    advance_positions = [-1, 5, 20, 35, 39]

    charm_positions = ((21, 0), (21, 1.03), (21, 2.06), (21, 3.09),
                       (20, 4.09), (22, 4.09),
                       (19, 5.06), (21, 5.06), (23, 5.06),
                       (0, 6), (2, 6), (4, 6), (6, 6), (8, 6), (10, 6),
                       (12, 6), (14, 6), (16, 6), (18, 6), (20, 6), (22, 6),
                       (24, 6), (26, 6), (28, 6), (30, 6), (32, 6), (34, 6),
                       (36, 6), (38, 6), (40, 6), (42, 6),
                       (19, 6.94), (21, 6.94), (23, 6.94),
                       (20, 7.91), (22,  7.91),
                       (21, 8.91), (21, 9.94), (21, 10.97), (21, 12)
                       )

    def hide(self, color_ring: str):
        """hide the Canvas-item that holds the given PhotoImage instance by moving it offscreen"""
        photoimage = self.rings[color_ring]
        self.c.coords(self.tk_ring_ids[photoimage], (-148, -148))

    def move_canvas_item(self, color_ring: str, pos: tuple):
        photoimage = self.rings[color_ring]
        tk_id = self.tk_ring_ids[photoimage]
        self.c.coords(tk_id, pos)

    def calc_coords(self, index: int):
    ##    g = [(5,5), (148+5+7,148+5+15), ((148+7)*3+5,5),(148+5+7,3*(148+15)+5)]
    ##    shuffle(g)
    ##    return g[0]
        if index > 39:
            return (-148, -148)
        return (self.charm_positions[index][0] * (w_offset) + w_side,
                self.charm_positions[index][1] * (h_offset) + h_side)

    def advance(self, color: str):
        current_pos = self.state[color]
        if current_pos > 39:
            return
        if current_pos + 1:  # remove old color from spot, only if not at 0 (because then there's nothing to remove)
            current_colors = "".join([k for k, v in self.state.items() if v == current_pos])  # colors in same spot as color to advance
            self.hide(current_colors)  # remove current rings from spot
            current_colors = current_colors.replace(color, "")
            if current_colors:  # move the corresponding new color ring (without the old color) into place
                self.move_canvas_item(current_colors, self.calc_coords(current_pos))
            else:  # check if this was the last one
                if current_pos == min(self.state.values()):
                    pos = self.calc_coords(current_pos)
                    choose = choice([self.finish_tex, self.finish_tex1, self.finish_tex2, self.finish_tex3])
                    tk_id = self.c.create_image(pos[0]-28, pos[1]-28, image=choose, anchor="nw")
                    self.finished_ids.append(tk_id)

        if current_pos in self.advance_positions:
            v = self.advance_positions.index(current_pos) + 1
            a = 0
            b = 1
            if v >= 4:  # skip 4
                a = 1
            if v == 4:
                b = 2
            if v != 1: # it's not the first one so we remove the previous one
                previous = self.border_tk_ids[f"v{color}{v + a - b}"]
                self.c.coords(previous, -width, -height)
            self.c.coords(self.border_tk_ids[f"v{color}{v + a}"], 2, 2)

        # move color into new position
        new_pos = self.state[color] = current_pos + 1
        new_colors = "".join([k for k, v in self.state.items() if v == self.state[color]])
        if new_colors.replace(color, ""):
            self.hide(new_colors.replace(color, ""))
        self.move_canvas_item(new_colors, self.calc_coords(new_pos))


    def go_back(self, color: str):
        current_pos = self.state[color]
        if current_pos < 0:
            return
        if current_pos - 40:  # remove old color from spot, only if not at 41 (because then there's nothing to remove)
            current_colors = "".join([k for k, v in self.state.items() if v == current_pos])  # colors in same spot as color to retreat
            self.hide(current_colors)  # remove current rings from spot
            current_colors = current_colors.replace(color, "")
            if current_colors:  # move the corresponding new color ring (without the old color) into place
                self.move_canvas_item(current_colors, self.calc_coords(current_pos))

        # move color into new position
        new_pos = self.state[color] = current_pos - 1
        new_colors = "".join([k for k, v in self.state.items() if v == self.state[color]])
        if new_colors.replace(color, ""):
            self.hide(new_colors.replace(color, ""))
        else:
            # check if this is now the last one
            if new_pos == min(self.state.values()) and new_pos + 1:  # previous field has a completed texture, remove it
                    tk_id = self.finished_ids.pop(new_pos)
                    self.c.delete(tk_id)
        if new_pos + 1:  # move new colors into place if the new field is a valid spot (i.e. > -1)
            self.move_canvas_item(new_colors, self.calc_coords(new_pos))

        if new_pos in self.advance_positions:
            v = self.advance_positions.index(new_pos) + 1
            a = 0
            b = 1
            if v >= 4:  # skip 4
                a = 1
            if v == 4:
                b = 2
            if v != 1: # it's not the first one, so we add a new one
                self.c.coords(self.border_tk_ids[f"v{color}{v + a - b}"], 2, 2)
            previous = self.border_tk_ids[f"v{color}{v + a}"]
            self.c.coords(previous, -width, -height)




"""stream 700 x 394, 7x7 pixel away from border"""

#timer_ex = tk.PhotoImage(file="timer_example2.png")
#c.create_image(2, 2, image=timer_ex, anchor="nw")

#finish_texture = tk.PhotoImage(file="C:\\Users\\peri\\AppData\\LocalLow\\Team Cherry"
#                               "\\Hollow Knight\\Livesplit\\Icon_HK_Dreamgate.png")

class control(tk.Toplevel):
    def __init__(self, main_widget, *args, **kw):
        tk.Toplevel.__init__(self, *args, **kw)
        self.title("restream control")
        # Description
        tk.Label(self, text = "Rewind").grid(row = 0, column = 0)
        tk.Label(self, text = "Advance").grid(row = 0, column = 1)
        tk.Label(self, text = "     Delay").grid(row = 0, column = 2)
        tk.Label(self, text = "Connect").grid(row = 0, column = 4)

        # Rewind Players
        tk.Button(self, text="player1 <", command=lambda: main_widget.go_back("r")).grid(row=1, column=0)
        tk.Button(self, text="player2 <", command=lambda: main_widget.go_back("c")).grid(row=2, column=0)
        tk.Button(self, text="player3 <", command=lambda: main_widget.go_back("g")).grid(row=3, column=0)
        tk.Button(self, text="player4 <", command=lambda: main_widget.go_back("p")).grid(row=4, column=0)

        # Advance Players
        tk.Button(self, text="> player1", command=lambda: main_widget.advance("r")).grid(row=1, column=1)
        tk.Button(self, text="> player2", command=lambda: main_widget.advance("c")).grid(row=2, column=1)
        tk.Button(self, text="> player3", command=lambda: main_widget.advance("g")).grid(row=3, column=1)
        tk.Button(self, text="> player4", command=lambda: main_widget.advance("p")).grid(row=4, column=1)

        # Add Delay
        self.scaleA = tk.Scale(self, from_= 0, to=10, length = 50)
        self.scaleA.grid(row=1, column = 2)
        self.scaleB = tk.Scale(self, from_= 0, to=10, length = 50)
        self.scaleB.grid(row=2, column = 2)
        self.scaleC = tk.Scale(self, from_= 0, to=10, length = 50)
        self.scaleC.grid(row=3, column = 2)
        self.scaleD = tk.Scale(self, from_= 0, to=10, length = 50)
        self.scaleD.grid(row=4, column = 2)

        # Connect to Room
        tk.Label(self, text="IP:").grid(row=1, column=3, sticky="w")
        self.ip = tk.Entry(self)
        self.ip.grid(row=1, column=4)
        tk.Label(self, text="Port:").grid(row=2, column=3, sticky="w")
        self.port = tk.Entry(self)
        self.port.grid(row=2, column=4)
        tk.Label(self, text="Room:").grid(row=3, column=3, sticky="w")
        self.room = tk.Entry(self)
        self.room.grid(row=3, column=4)
        tk.Label(self, text="PW:").grid(row=4, column=3, sticky="w")
        self.pw = tk.Entry(self)
        self.pw.grid(row=4, column=4)


    def get(self,player) -> int:
        dic = {k:v.get() for k,v in zip(range(4),(self.scaleA, self.scaleB, self.scaleC, self.scaleD))}
        return dic[player]


class Chooser(tk.Toplevel):
    def __init__(self, main_widget, send_charmdata=lambda *arg: None, printout=False, *args, **kw):
        tk.Toplevel.__init__(self, *args, **kw)
        self.title("SBRCO Chooser")
        charm_select.main(self, send_charmdata=lambda *arg: send_charmdata(*arg, main_widget), printout=printout).grid()


def populate_charms(w: widget, charmb64: str):
    w.update_charmlist(charm_select.get_charmlist_from_b64(charmb64))
    w.populate_charms()


if __name__ == "__main__":
    master = widget()
    #raise SystemExit
    cho = Chooser(master, send_charmdata=lambda b64, mw: populate_charms(mw, b64))

    # def go():
    #     while min(master.state.values()) < 40:
    #         time.sleep(choice([0.1,0.2,0.3,0.5,0.8,1,1.2,1.3,1.4,1.5]))
    #         master.advance(choice("rcgp"))
    #         master.update()
    #     print("finished")
    # tk.Button(con, text="advance", command=go).grid(row=5, column=0, columnspan=2)

    master.mainloop()
