import tkinter as tk
from math import sin, cos, e, pi
import time
import threading


class StatusIcon(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.c = tk.Canvas(self, width=50, height=40)
        self.c.grid(row=0, column=0)
        self.i = 0
        self.check_tk = -1
        self.cross_tk = -1
        self.dots = []
        self.load_offset = 0
        self.init_finished()
        self.init_failed()
        self.init_loading()
        self.switch("failed")

    def init_finished(self):
        self.checkmark = tk.PhotoImage(file="Resources/UI/checkmark.png")
        self.checkmark = self.checkmark.subsample(2)
        self.check_tk = self.c.create_image(2,2, image=self.checkmark, anchor="nw")

    def init_failed(self):
        self.cross = tk.PhotoImage(file="Resources/UI/cross.png")
        self.cross = self.cross.subsample(2)
        self.cross_tk = self.c.create_image(7,2, image=self.cross, anchor="nw")

    def init_loading(self):
        ido1 = self.c.create_oval(0,0,5,5,fill="#000000", width=0)
        ido2 = self.c.create_oval(0,0,5,5,fill="#4f4f4f", width=0)
        ido3 = self.c.create_oval(0,0,5,5,fill="#7a7a7a", width=0)
        ido4 = self.c.create_oval(0,0,5,5,fill="#a0a0a0", width=0)
        ido5 = self.c.create_oval(0,0,5,5,fill="#b4b4b4", width=0)
        self.dots = [ido1, ido2, ido3, ido4, ido5]
        self.thread1 = threading.Thread(target=self._move_loading)
        self.thread1.start()

    def _move_loading(self):
        i = self.i
        c = self.c
        d1, d2, d3, d4, d5 = self.dots
        while True:
            offset = self.load_offset
            x1 = cos(i/360*2*pi)*14 + 21 + offset
            y1 = sin(i/360*2*pi)*14 + 16 + offset
            x2 = cos((i-1*55)/360*2*pi)*14 + 21 + offset
            y2 = sin((i-1*55)/360*2*pi)*14 + 16 + offset
            x3 = cos((i-2*55)/360*2*pi)*14 + 21 + offset
            y3 = sin((i-2*55)/360*2*pi)*14 + 16 + offset
            x4 = cos((i-3*55)/360*2*pi)*14 + 21 + offset
            y4 = sin((i-3*55)/360*2*pi)*14 + 16 + offset
            x5 = cos((i-4*55)/360*2*pi)*14 + 21 + offset
            y5 = sin((i-4*55)/360*2*pi)*14 + 16 + offset
            c.coords(d1, x1, y1, x1+12, y1+12)
            c.coords(d2, x2, y2, x2+11, y2+11)
            c.coords(d3, x3, y3, x3+10, y3+10)
            c.coords(d4, x4, y4, x4+9, y4+9)
            c.coords(d5, x5, y5, x5+8, y5+8)
            c.update()
            i += 1
            i %= 360
            time.sleep(0.005)

    def switch(self, mode):
        if mode == "loading":
            self.load_offset = 0
            self.c.coords(self.check_tk, -80, -80)
            self.c.coords(self.cross_tk, -80, -80)
        if mode == "finished":
            self.load_offset = -80
            self.c.coords(self.check_tk, 2, 2)
            self.c.coords(self.cross_tk, -80, -80)
        if mode == "failed":
            self.load_offset = -80
            self.c.coords(self.check_tk, -80, -80)
            self.c.coords(self.cross_tk, 2, 2)


if __name__ == "__main__":
    def switch_random():
        import random
        while True:
            new_mode = random.choice(["loading", "finished", "failed"])
            print(new_mode)
            f.switch(new_mode)
            time.sleep(random.randint(1, 3))
    m = tk.Tk()
    f=StatusIcon(m)
    f.pack()
    sw_thread = threading.Thread(target=switch_random)
    sw_thread.start()
    m.mainloop()


