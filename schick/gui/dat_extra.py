
from schick.util import hexdump, img_to_rgb
from schick.gui.util import FilteredListbox, img_to_tk

from tkinter import *
from tkinter import ttk
import tkinter as tk

class SchickDatTlkContent(ttk.Frame):
    def __init__(self, master, schick_reader, fname):
        ttk.Frame.__init__(self, master)

        self.max_pages = 1
        self.schick_reader = schick_reader

        self.random, self.informers, self.states, self.texts = schick_reader.read_archive_tlk_file(fname)
        informer_index = []
        for i in self.informers:
            informer_index.append(
            "'{:s}' (state_offset: {:d}, txt_offset: {:d}, head_id: 0x{:04x})".format(
                i['title'], i['state_offset'], i['txt_offset'], i['head_id']
            ))
        self.state_descr = []
        self.informer_name = StringVar(value="")
        self.state_selected = StringVar()
        self.text = StringVar(value="")
        self.opts = [StringVar(value=""), StringVar(value=""), StringVar(value="")]

        l = ttk.Label(self, textvariable=self.informer_name, width=20)
        self.in_head = ttk.Label(self, anchor=CENTER)
        self.lbox = Listbox(self, listvariable=StringVar(value=informer_index), height=8)
        self.state_select = FilteredListbox(self, listvariable=self.state_descr, height=10)
        t = ttk.Label(self, textvariable=self.text)
        self.buttons = [Button(self, textvariable=s, anchor=W, justify=LEFT) for s in self.opts]

        l.grid(column=0, row=0, sticky=(W,), padx=10)
        self.in_head.grid(column=0, row=1, sticky=(N,E,S,W))
        self.lbox.grid(column=1, row=0, rowspan=2, columnspan=1, pady=5, sticky=(N,S,W,E))
        self.state_select.grid(column=0, row=2, columnspan=2, pady=5, sticky=(N,E,S,W))
        t.grid(column=0, row=3, columnspan=2, pady=5, sticky=(N,W,E))
        for i,b in enumerate(self.buttons):
            b.grid(column=0, row=4+i, columnspan=2, sticky=(N,W,E))

        self.grid_columnconfigure(1, weight=1)

        self.lbox.bind("<<ListboxSelect>>", self.select_in_cb)
        self.state_select.bind("<<ListboxSelect>>", self.select_state_cb)
        for i, b in enumerate(self.buttons):
            b.config(command=lambda no=i: self.button_cb(no))

        self.lbox.selection_set(0)
        self.select_in_cb()

    def load_in_head(self, no):
        img = self.schick_reader.get_in_head(no)
        img["scaling"] = 3.0
        img_to_tk(img)
        self.img_tk = img["tk"]
        self.in_head.config(image=self.img_tk)

    def load_in_states(self, idx):
        off = self.informers[idx]['state_offset']
        next = len(self.states)
        if len(self.informers) > idx+1:
            next = self.informers[idx+1]['state_offset']
        cnt = next - off
        result = []
        self.state_descr = []
        for i in range(cnt):
            s = self.states[off + i]
            choice = "[{:03d}{}] GOTO: ({:03d}) || ({:03d}) || ({:03d})".format(
                    i, "*" if (s['txt_id'] & 0x8000) else " ",
                    -1 if s['ans1'] == 255 else s['ans1'], s['ans2'], s['ans3']
            )
            self.state_descr.append(choice)
        self.state_select.set_listvariable(self.state_descr)

    def load_in_state(self, idx):
        state = self.state = self.states[self.informer['state_offset'] + idx]
        output = ""
        if state['txt_id'] == -1:
            output += "<no text, auto-option>"
        else:
            txt_id = state['txt_id'] & 0x7fff
            txt_id *= 4 if self.random else 1
            for r in range(4 if self.random else 1):
                txt = self.texts[self.informer['txt_offset'] + txt_id + r]
                if txt == "": continue
                if self.random: output += "T:"
                output += txt
                if self.random: output += "\n"
        self.text.set(output.strip())
        for n, opt in enumerate(state['opt']):
            if state['ans'][n] == 0:
                self.opts[n].set("")
                self.buttons[n].config(state=DISABLED)
                continue
            output = ""
            for r in range(4 if self.random else 1):
                output += "{:d}: ".format(n)
                txt_id = self.informer['txt_offset'] + opt + r
                if state['ans'][n] == 255:
                    output += "<end of dialog>"
                elif opt == 0:
                    output += "<no text, auto-option>"
                else:
                    output += self.texts[txt_id]
                output += "\n"
            self.opts[n].set(output.strip())
            if state['ans'][n] != 255:
                self.buttons[n].config(state=NORMAL)
            else:
                self.buttons[n].config(state=DISABLED)

    def button_cb(self, no):
        self.state_select._select(self.state["ans"][no])

    def select_in_cb(self, *args):
        idxs = self.lbox.curselection()
        if len(idxs)==1:
            idx = int(idxs[0])
            i = self.informers[idx]
            self.informer = i
            self.informer_name.set(i['title'])
            self.load_in_head(i['head_id'])
            self.load_in_states(idx)
            self.state_selected.set(self.state_descr[0])
            self.select_state_cb()

    def select_state_cb(self, *args):
        idx = self.state_select.curselection()
        if idx is not None:
            self.load_in_state(idx)

class SchickDatMapContent(ttk.Frame):
    def __init__(self, master, schick_reader, fname, page=0):
        ttk.Frame.__init__(self, master)

        self.page = page
        self.schick_reader = schick_reader

        self.canvas = Canvas(self, height=8*16*1.5)
        self.lbox = FilteredListbox(self, listvariable=[], height=15)

        self.canvas.grid(row=0, column=0, pady=5, sticky=(N,E,S,W))
        self.lbox.grid(row=1, column=0, sticky=(N,E,S,W))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self.on_resize)
        self.lbox.bind("<<ListboxSelect>>", self.select_loc_cb)

        self.images, self.loctab = self.schick_reader.read_archive_map_file(fname)
        for img in self.images: img["bak"] = img["rgb"].copy()
        self.max_pages = len(self.images)
        self.filter_loctab(self.page)
        self.show_image(self.page)

    def select_loc_cb(self, *args):
        idx = self.lbox.curselection()
        if idx is not None:
            self.mark_tile(self.loctab_filtered[idx][0][1:])

    def mark_tile(self, coords):
        img = self.images[self.page]
        y,x = coords
        x *= 8; y *= 8
        img["rgb"][:] = img["bak"]
        color = [255,255,255]
        img["rgb"][x:x+9,y:y+2] = color
        img["rgb"][x:x+9,y+7:y+9] = color
        img["rgb"][x:x+2,y:y+9] = color
        img["rgb"][x+7:x+9,y:y+9] = color
        self.show_image(self.page)

    def on_resize(self, event):
        self.canvas.delete("all")
        self.show_image(self.page)
        
    def filter_loctab(self, lvl):
        listvar = []
        self.loctab_filtered = []
        for l in self.loctab:
            if lvl == l[0][0]:
                listvar.append(
                    "({:02d},{:02d}): {} (#{}, {})".format(*l[0][1:], *l[1:])
                )
                self.loctab_filtered.append(l)
        self.lbox.set_listvariable(listvar)

    def show_image(self, page):
        img = self.images[page]
        img_to_tk(img)
        posx = (self.canvas.winfo_width()-img["tk"].width())//2
        self.canvas.create_image((posx,0), anchor=NW, image=img["tk"])

class SchickDatNVFContent(ttk.Frame):
    def __init__(self, master, schick_reader, fname, page=0):
        ttk.Frame.__init__(self, master)

        self.schick_reader = schick_reader

        self.canvas = Canvas(self)
        s = Scrollbar(self)
        self.canvas.config(yscrollcommand=s.set)
        s.config(command=self.canvas.yview)

        s.grid(row=0, column=1, sticky=(N,S))
        self.canvas.grid(row=0, column=0, sticky=(N,E,S,W))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self.on_resize)

        self.images, self.max_pages = self.schick_reader.read_archive_nvf_file(fname, page)
        self.show_images()

    def on_resize(self, event):
        self.canvas.delete("all")
        self.show_images()

    def show_images(self):
        posx, posy = 0, 0
        lastheight = 0
        max_x = self.canvas.winfo_width()-5
        for img in self.images:
            img_to_tk(img, self.canvas.winfo_width()-5)
            if posx + img["tk"].width() > max_x:
                posx = 0
                posy += lastheight + 5
                lastheight = 0
            self.canvas.create_image((posx, posy), anchor=NW, image=img["tk"])
            lastheight = max(lastheight, img["tk"].height())
            posx += img["tk"].width() + 5
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))

class SchickDatTxContent(ttk.Frame):
    def __init__(self, master, schick_reader, fname):
        ttk.Frame.__init__(self, master)

        self.max_pages = 1
        self.tx_index = schick_reader.read_archive_tx_file(fname)

        self.by_index = StringVar()
        self.by_hex = StringVar()

        l1 = ttk.Label(self, text="#")
        e1 = Entry(self, textvariable=self.by_index, width=3)
        l2 = ttk.Label(self, text="get_tx(0x...)")
        e2 = Entry(self, textvariable=self.by_hex, width=4)
        self.text = Text(self, height=10, padx=10, pady=10)
        self.lbox = FilteredListbox(self, listvariable=self.tx_index, height=30)

        l1.grid(column=0, row=0, sticky=(W,))
        e1.grid(column=1, row=0, padx=(0,10), sticky=(W,))
        l2.grid(column=2, row=0, sticky=(W,))
        e2.grid(column=3, row=0, sticky=(W,))
        self.lbox.grid(column=0, row=1, columnspan=5, sticky=(N,E,S,W))
        self.text.grid(column=0, row=2, columnspan=5, padx=10, pady=5, sticky=(W,E))
        self.grid_columnconfigure(4, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.by_hex.trace("w", self.by_hex_cb)
        self.by_index.trace("w", self.by_index_cb)

        self.lbox.bind("<<ListboxSelect>>", self.select_cb)
        self.select_cb()

    def by_hex_cb(self, *args):
        try:
            idx = int(self.by_hex.get(), 16)//4
            self.lbox._select(idx)
        except ValueError:
            pass

    def by_index_cb(self, *args):
        try:
            idx = int(self.by_index.get())
            self.lbox._select(idx)
        except ValueError:
            pass

    def select_cb(self, *args):
        idx = self.lbox.curselection()
        if idx is not None:
            self.text.delete("1.0", END)
            self.text.insert(END, self.tx_index[idx])

class SchickDatHexContent(ttk.Frame):
    def __init__(self, master, schick_reader, fname):
        self.max_pages = 1
        ttk.Frame.__init__(self, master)
        text = Text(self, height=20, width=65, padx=10, pady=10)
        text.grid(column=0, row=0, padx=10, pady=5, sticky=(N,S))
        text.delete("1.0", END)
        text.insert(END, hexdump(schick_reader.read_archive_file(fname)))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

