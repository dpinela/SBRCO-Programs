"""GUI to display and randomize charm orders, as well as create livesplit files.
uses SBRCO_logic_parser for charm logic within generate_charmlist"""

import tkinter as tk
from Resources.res import charms_splits, charms_autosplits
from Resources.res.charms import charms as vanilla_charm_order
from Resources.config.logic_config import config as logic_config
from generate_charmlist import create_logic, generate_charm_order, update_sender, update_params
from list_permutations import k_th_permutation, index as permutation_index
import threading
from os import getcwd, listdir
import base64
from time import sleep

num_charms = 55

def generate_charmlist_from_order(charm_order: list) -> list:
    charms = [vanilla_charm_order[charm_pos] for charm_pos in charm_order]
    return charms


def generate_charm_orderlist(charms: list) -> list:
    charm_order = [vanilla_charm_order.index(charm) for charm in charms]
    return charm_order


def get_charmlist_from_b64(b64string: str) -> list:
    charm_config = int.from_bytes(base64.b64decode(b64string.encode()), "big")
    charm_order = k_th_permutation(num_charms, charm_config)
    return generate_charmlist_from_order(charm_order)


def get_charm_order_b64(charmlist: list) -> str:
    charm_order = generate_charm_orderlist(charmlist)
    charmlist_id = permutation_index(charm_order)
    return base64.b64encode(charmlist_id.to_bytes(31, "big")).decode()


def generate_autosplits(charms: list, randowake: bool = False):
    with open("Resources/res/charms_splitfile.txt") as f:
        s = f.read()
    try:
        with open("config/layoutpath.txt") as f:
            layoutpath = f.read().strip()
    except IOError:
        layoutpath = ""
    if layoutpath and len(layoutpath.split("\\/")) == 1:
        layoutpath = getcwd() + "\\" + layoutpath
    lss = s.format(
        charmsplits="\n    ".join(
            charms_splits.charms_splits[charm] for charm in charms),
        autostart=("RandoWake" if randowake else ""),
        autosplits="\n      ".join(
            charms_autosplits.charms_splits[charm] for charm in charms),
        layoutpath=f"<LayoutPath>{layoutpath}</LayoutPath>" if layoutpath else "")
    return lss
    

class CharmWindow(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.bg_img = tk.PhotoImage(file="Resources/UI/bgfaint.png")
        self.create_image(2, 2, image=self.bg_img, anchor="nw")

        self.red = self.create_rectangle(-5, -5, -4, -4, fill="#ff0000", width=0)

        self.greens = []
        for i in range(num_charms):
            tk_id = self.create_rectangle(-5, -5, -4, -4, fill="#00ff00", width=0)
            self.greens.append(tk_id)
        self.current_greens = []

        self.drop_shadows = []
        for i in range(num_charms):
            tk_id = self.create_oval(-5, -5, -4, -4, fill="#2a3694", outline="#131b56", width=2)
            self.drop_shadows.append(tk_id)

        self.charm_tk_ids = {}
        for i, charm_name in enumerate(vanilla_charm_order):
            cimg = tk.PhotoImage(file="Resources/UI/charms/" + charm_name + ".png")
            cimg = cimg.subsample(2)
            tk_id = self.create_image(-148, -148, image=cimg, anchor="nw")
            self.charm_tk_ids[charm_name] = tk_id, cimg

        self.charmlist = []

    @staticmethod
    def get_charm_coords(index):
        return (index % 8) * 75 + 2, index // 8 * 94 + 2

    def insert_charm(self, charm_name, index):
        self.coords(self.charm_tk_ids[charm_name][0], *self.get_charm_coords(index))

    def remove_charm(self, charm_name):
        self.coords(self.charm_tk_ids[charm_name][0], -148, -148)

    def lift_charm(self, index):
        self.move(self.charm_tk_ids[self.charmlist[index]][0], 0, -10)
        self.move_shadow(index, *self.get_charm_coords(index))

    def drop_charm(self, index):
        self.move(self.charm_tk_ids[self.charmlist[index]][0], 0, 10)
        self.reset_shadow(index)

    def move_left(self, *, charm=None, index=None):
        if index is None:
            try:
                index = self.charmlist.index(charm)
            except ValueError:
                index = len(self.charmlist)
        if charm is None:
            charm = self.charmlist[index]
        self.insert_charm(charm, index - 1)
        return charm, index - 1

    def move_right(self, *, charm=None, index=None):
        if index is None:
            try:
                index = self.charmlist.index(charm)
            except ValueError:
                index = len(self.charmlist) - 1
        if charm is None:
            charm = self.charmlist[index]
        self.insert_charm(charm, index + 1)
        return charm, index + 1

    def highlight_charm_green(self, index):
        self.move_green(index, *self.get_charm_coords(index))

    def highlight_charm_red(self, index):
        self.settle_green(index)
        self.move_red(*self.get_charm_coords(index))

    def settle_green(self, index):
        self.coords(self.greens[index], -5, -5, -4, -4)

    def settle_red(self):
        self.coords(self.red, -5, -5, -4, -4)

    def move_red(self, x, y):
        self.coords(self.red, x, y, x + 74, y + 74)

    def move_green(self, index, x, y):
        self.coords(self.greens[index], x, y, x + 74, y + 74)

    def move_shadow(self, index, x, y):
        self.coords(self.drop_shadows[index], x, y, x + 74, y + 74)

    def reset_shadow(self, index):
        self.coords(self.drop_shadows[index], -5, -5, -4, -4)

    def reset_charms(self):
        """move all charms in the visible window back into the corner"""
        for charm in self.charmlist:
            self.remove_charm(charm)
            self.charmlist = []


class CharmWindowUpdater:
    """handles the (window) logic for updating CharmWindow on the fly as the charm order is being generated"""
    def __init__(self, charmwindow, logic_cfg=None):
        self.cw = charmwindow
        self.update_sender = update_sender(send=self.recv)
        self.last_charm_added = [True, None, None]  # to track if we added the charm on the previous attempt, as there is no indication if we didn't
        self.removed_charm_last = [False, None]
        self.inserted_charm_last = [False, None, None, None]

        if logic_cfg is None:
            logic_cfg = logic_config
        self.logic_config = logic_cfg

    fast_forward = False

    @classmethod
    def toggle_fast(cls):
        cls.fast_forward = not cls.fast_forward

    def recv(self, *args):
        # this function is more fragile than your heart, so don't change anything or the UI will break
        # also, imagine commenting your code or refactoring it into sub-methods
        """function that gets called whenever generate_charmlist.generate_charm_order
        sends an update to change the currently displayed charms in some way.

        args and actions: (this was an early draft for required actions for each possible *args value and may not reflect the final state)
        ====================
        insert: charm WHITE and move to pos                                     ("insert" . index charm)
                move all charms to the right of charm one right and drop /&end
        contains: mark charm GREEN                                              ("__contains__" . req_charm True)
        append: remove RED /&end                                                ("append" . charm None)
        pop:    LIFT charm                                                      ("pop" . charm)
        remove: idk I forgor                                                    ("remove" . charm None)
        attempt:move charm to pos and RED                                       (. "attempt add new charm" charm index)
        move overdue tuple: charm RED and move left                             (. "move charm forward overdue" charm tuple)
        move overdue TRUE:  charm GREEN and move left                           (. "move charm forward overdue" charm True)
        move overdue FALSE: charm RED, drop the one to the left                 (. "move charm forward overdue" charm False)
        move inbounds: charm GREEN and move left                                (. "move charm forward inbounds" charm index)
        /&end: clear GREENs
        """
        if args[0] == "generate":  # one of "add new charm" or "move overdue charm backwards"
            charm = args[2]
            if args[1] == "attempt add new charm":
                index = args[3]
                self.clean_up_after_inserts()
                if self.removed_charm_last[0]:
                    for left_i in range(self.cw.charmlist.index(self.inserted_charm_last[1]) + 1, len(self.cw.charmlist)):
                        self.cw.insert_charm(self.cw.charmlist[left_i], left_i)
                    self.inserted_charm_last = [False, None, None, None]
                    self.removed_charm_last = [False, None]
                if not self.last_charm_added[0]:  # remove failed previous attempt
                    self.cw.charmlist.remove(self.last_charm_added[1])
                    self.cw.remove_charm(self.last_charm_added[1])
                    self.cw.settle_red()
                for i in self.cw.current_greens:
                    self.cw.settle_green(i)
                self.cw.current_greens = []
                self.last_charm_added = [False, charm, index]
                self.cw.highlight_charm_red(index)
                self.cw.insert_charm(charm, index)
                self.cw.charmlist.append(charm)
            if args[1] == "move charm forward overdue":
                index = len(args[4])
                if isinstance(args[3], tuple):
                    self.cw.insert_charm(charm, index)
                    self.cw.highlight_charm_red(index)
                    self.cw.move_right(index=index)
                    self.cw.charmlist.remove(charm)
                    self.cw.charmlist.insert(index, charm)
                    self.cw.lift_charm(index + 1)
                if args[3] is False:
                    for right_i in range(index + 1, len(self.cw.charmlist)):
                        self.cw.drop_charm(right_i)
                        self.cw.move_left(index=right_i)
                    self.cw.remove_charm(charm)
                    self.cw.charmlist.remove(charm)
                    for i in self.cw.current_greens:
                        self.cw.settle_green(i)
                    self.cw.current_greens = []
                    self.last_charm_added[2] = index
                if args[3] is True:
                    self.cw.insert_charm(charm, index)
                    self.cw.highlight_charm_green(index)
                    self.cw.current_greens.append(index)
                    self.cw.settle_red()
                    self.cw.move_right(index=index)
                    self.cw.charmlist.remove(charm)
                    self.cw.charmlist.insert(index, charm)
                    self.cw.lift_charm(index + 1)
                    for left_i in range(index + 1, len(self.cw.charmlist)):
                        self.cw.drop_charm(left_i)
                    self.inserted_charm_last[3] = index
            if args[1] == "move charm forward inbounds":
                index = len(args[3])
                self.cw.insert_charm(charm, index)
                self.cw.highlight_charm_green(index)
                self.cw.current_greens.append(index)
                self.cw.settle_green(index + 1)
                self.cw.current_greens.remove(index + 1)
                self.cw.move_right(index=index)
                self.cw.charmlist.remove(charm)
                self.cw.charmlist.insert(index, charm)
                self.cw.lift_charm(index + 1)
                self.inserted_charm_last[2] = index
        if args[0] == "append":
            charm = args[2]
            for i in self.cw.current_greens:
                self.cw.settle_green(i)
            self.cw.current_greens = []
            self.cw.settle_red()
            self.last_charm_added[:2] = [True, charm]
        if args[0] == "insert":
            index, charm = args[2:4]
            self.inserted_charm_last[:2] = [True, charm]
            for i in self.cw.current_greens:
                self.cw.settle_green(i)
            self.cw.current_greens = []
            self.cw.settle_red()
            # print("self.inserted_charm_last:", self.inserted_charm_last)
            try:
                self.cw.charmlist.remove(charm)
            except ValueError:
                # this will come into play if we failed to find a valid position
                # for a dependency and just inserted the new charm behind it,
                # as it won't have been added in that case
                self.inserted_charm_last[2:] = [index, len(self.cw.charmlist)]
            self.cw.insert_charm(charm, index)
            self.cw.charmlist.insert(index, charm)
            self.last_charm_added = [True, charm, index]
        if args[0] == "__contains__" and args[3] is True:
            req_charm = args[2]
            index = self.cw.charmlist.index(req_charm)
            self.cw.highlight_charm_green(index)
            self.cw.current_greens.append(index)
        if args[0] == "remove":
            charm = args[2]
            self.removed_charm_last = [True, charm]
        if args[0] == "pop":
            pass
        self.cw.update()
        if not self.fast_forward:
            sleep(0.2)

    def clean_up_after_inserts(self):
        if self.inserted_charm_last[0] and not self.removed_charm_last[0]:
            # we previously moved a charm inbounds and now need to reset all left ones
            last_charm = self.inserted_charm_last[1]
            for left_i in range(self.inserted_charm_last[2], self.inserted_charm_last[3] + 1):
                self.cw.drop_charm(left_i)
                self.cw.insert_charm(self.cw.charmlist[left_i], left_i)
            self.inserted_charm_last = [False, None, None, None]


class CharmSelector(tk.Frame):
    """Frame around a CharmWindow-instance which adds buttons, entry widgets and management logic
    to fetch options from the main(tk.Tk)-instance and call generate_charm_order() with"""
    def __init__(self, *args, logic_cfg=None, printout=True, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.c = CharmWindow(self, width=600, height=650, bg="#ffffff")
        self.c.grid(row=2, column=0, columnspan=4)
        self.cwu = CharmWindowUpdater(self.c)
        self.genButton = tk.Button(self, text="generate Random Charm Order", command=self.start_thread_generate)
        self.genButton.grid(row=1, column=0, columnspan=4, sticky="wesn")
        self.seedORb64 = tk.IntVar()
        self.seedORb64.set(0)
        tk.Radiobutton(self, text="Seed:", variable=self.seedORb64, value=0).grid(row=0, column=0)
        self.charmseed = tk.Entry(self)
        self.charmseed.grid(row=0, column=1, sticky="wesn")
        tk.Radiobutton(self, text="base64 config:", variable=self.seedORb64, value=1).grid(row=0, column=2)
        self.b64config = tk.Entry(self)
        self.b64config.grid(row=0, column=3, sticky="wesn")
        self.grid_columnconfigure((1,3), weight=1)
        if logic_cfg is None:
            logic_cfg = logic_config
        self.logic_config = logic_cfg
        self.printout = printout

    def start_thread_generate(self):
        thread1 = threading.Thread(target=self.generate)
        thread1.start()

    def generate(self, logic=None, config=None):
        self.genButton["state"] = "disabled"
        if logic is None:
            with open("Resources/config/logic.txt") as f:
                logic = f.read()
        if config is None:
            config = self.logic_config
        if isinstance(config, logic_dict):
            config = config.eval_contents()
        logic = create_logic(logic, config)
        seed_or_b64 = self.seedORb64.get()
        b64config = self.b64config.get()
        if self.charmseed.get():
            seed = self.charmseed.get()
        else:
            seed = None
        print("="*20, "\n\nGenerating Charms from", end=" ")
        if not seed_or_b64:
            print("random seed" if seed is None else f"seed {seed}")
        else:
            print("base64-string", b64config)
        print()
        print("Logic Config:", config, end="\n\n\n")
        #print("Logic:", logic)
        self.c.reset_charms()
        if seed_or_b64 == 0:
            self.c.charmlist = generate_charm_order(logic, self.cwu.update_sender, seed=seed, print=(print if self.printout else (lambda *a, **kw: None)))
            self.cwu.clean_up_after_inserts()
            self.b64config.delete(0, "end")
            self.b64config.insert(0, get_charm_order_b64(self.c.charmlist))
            print("\nSuccessfully generated Charmlist!")
        else:
            self.c.charmlist = get_charmlist_from_b64(b64config)
            for i, charm in enumerate(self.c.charmlist):
                self.c.insert_charm(charm, i)
        self.genButton["state"] = "normal"
        print("\nCharms:", self.c.charmlist)
        # print("Charmlist in base10:", charmlist_id)
        print("Charmlist in base64:", get_charm_order_b64(self.c.charmlist), end="\n\n\n")


class logic_dict(dict):
    """dict where values are tk.BooleanVar() instances and need to be retrieved using .get(). looks them up on the go"""
    def __getitem__(self, key):
        return dict.__getitem__(self, key).get()

    def __repr__(self):
        return "{" + ", ".join([f"{repr(key)}: {repr(value.get())}" for key, value in self.items()]) + "}"

    def eval_contents(self):
        return {k: self[k] for k in self}


class main(tk.Frame):
    def __init__(self, *args, send_charmdata=lambda *arg: None, printout=True, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        # add tk widgets
        self.config_i = tk.IntVar()
        self.config_i.set(0)
        configframe = tk.Frame(self)
        configframe.grid(row=0, column=0, columnspan=3, sticky="we")
        self.logic_options = logic_dict()
        for i, (option, v) in enumerate(logic_config.items()):
            logic_val = tk.BooleanVar()
            logic_val.set(v)
            self.logic_options[option] = logic_val
            tk.Checkbutton(configframe, text=option, variable=logic_val).grid(row=i//7, column=i%7)
            configframe.grid_columnconfigure(i%7, weight=1)
        tk.Frame(self, height=188).grid(row=1, column=1)
        tk.Checkbutton(configframe, text="Fast", command=CharmWindowUpdater.toggle_fast).grid(row = (i + 1) // 7,
                                                                                              column = (i + 1) % 7)
        self.config1 = CharmSelector(self, logic_cfg=self.logic_options, printout=printout)
        self.config1.grid(row=1, rowspan=2, column=0, sticky="n")
        tk.Radiobutton(self, text="RCO 1", variable=self.config_i, value=0).grid(row=3, column=0)
        self.config2 = CharmSelector(self, logic_cfg=self.logic_options, printout=printout)
        self.config2.grid(row=2, column=1)
        tk.Radiobutton(self, text="RCO 2", variable=self.config_i, value=1).grid(row=3, column=1)
        self.config3 = CharmSelector(self, logic_cfg=self.logic_options, printout=printout)
        self.config3.grid(row=1, rowspan=2, column=2, sticky="n")
        tk.Radiobutton(self, text="RCO 3", variable=self.config_i, value=2).grid(row=3, column=2)
        if send_charmdata is None:
            send_charmdata=lambda *args: self.generate_lss()
        tk.Button(self, text="generate lss", command=lambda: send_charmdata(
            get_charm_order_b64((self.config1, self.config2, self.config3)[self.config_i.get()].c.charmlist)
            )).grid(row=4, column=0, columnspan=3, sticky="wesn")

        # add data
        self.charmlist = vanilla_charm_order.copy()

    def generate_lss(self):
        charm_order_b64 = get_charm_order_b64((self.config1, self.config2, self.config3)[self.config_i.get()].c.charmlist)
        self.get_charmlist(charm_order_b64)
        lss = generate_autosplits(self.charmlist, randowake=self.logic_options["randowake"])
        with open(f"sbrco.lss", "w") as f:
            f.write(lss)
        print("generated autosplits in ./sbrco.lss")

    def get_charmlist(self, config: str):
        """:param config: base64 string"""
        print("old charms:", self.charmlist)
        order = generate_charm_orderlist(self.charmlist)
        print("old order:", order)
        print("new config:", config)
        config_bytes = base64.b64decode(config.encode())
        print("config bytes:", config_bytes)
        config_int = int.from_bytes(config_bytes, "big")
        print("config int:", config_int)
        order = k_th_permutation(len(self.charmlist), config_int)
        print("new order:", order)
        self.charmlist = generate_charmlist_from_order(order)
        print("new charms:", self.charmlist)
        return self.charmlist


if  __name__ == "__main__":
    master = tk.Tk()
    window = main(master, send_charmdata=None)
    window.grid()
    master.mainloop()
