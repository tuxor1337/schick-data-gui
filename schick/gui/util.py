
from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk

import math
        
def img_to_tk(img, max_width=0):
    img_pil = Image.fromarray(img["rgb"])
    if img["scaling"] == 0 and max_width != 0:
        out_w = max(img["width"], max_width)
        out_h = max(img["height"], math.floor(img["height"]*max_width/img["width"]))
    else:
        out_w = math.floor(img["width"]*img["scaling"])
        out_h = math.floor(img["height"]*img["scaling"])
    img["tk"] = ImageTk.PhotoImage(img_pil.resize((out_w, out_h)))

class FilteredListbox(ttk.Frame):
    def __init__(self, master, color_cb=lambda idx: None, listvariable=[], **kwargs):
        ttk.Frame.__init__(self, master)
        
        self.color_cb = color_cb
        self.data_raw = listvariable
        self.data_filtered = []
        self.data_lbox = StringVar(value=listvariable)
        self.filter = StringVar()
        
        self.lbox = Listbox(self, listvariable=self.data_lbox, **kwargs)
        e = Entry(self, textvariable=self.filter)
        s = Scrollbar(self)
        self.lbox.config(yscrollcommand=s.set)
        s.config(command=self.lbox.yview)
        
        self.lbox.grid(column=0, row=0, sticky=(N,E,S,W))
        s.grid(column=1, row=0, sticky=(N,S,W))
        e.grid(column=0, row=1, columnspan=2, sticky=(W,E))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.lbox.bind('<<ListboxSelect>>', self.select_cb)
        self.filter.trace("w", self.filter_cb)
        
        self.filter_cb()
        self.lbox.selection_set(0)
        
    def color_lbox(self):
        for i, idx in enumerate(self.data_filtered):
            colors = self.color_cb(idx)
            if colors is not None:
                fg, bg = colors
            elif i%2 == 0:
                fg, bg = "#000000", '#f0f0f0'
            else:
                fg, bg = "#000000", '#ffffff'
            self.lbox.itemconfigure(i, foreground=fg, background=bg)
        
    def filter_cb(self, *args):
        filter_str = self.filter.get()
        try:
            prog = re.compile(filter_str)
            self.data_filtered = []
            result = []
            for idx, s in enumerate(self.data_raw):
                if re.search(filter_str, s, flags=re.I) is not None: 
                    self.data_filtered.append(idx)
                    result.append(s)
            self.data_lbox.set(result)
        except re.error:
            pass
        self.color_lbox()
        
    def curselection(self):
        idxs = self.lbox.curselection()
        if len(idxs)==1:
            return self.data_filtered[int(idxs[0])]
        else:
            return None
            
    def set_listvariable(self, data):
        self.data_raw = data
        self.data_lbox.set(data)
        self.filter.set("")
        self.lbox.selection_clear(0, last=len(self.data_filtered)-1)
        self.lbox.selection_set(0)
            
    def _select(self, idx):
        self.lbox.selection_clear(0, last=len(self.data_filtered)-1)
        try:
            i = self.data_filtered.index(idx)
            self.lbox.selection_set(i)
            self.lbox.see(i)
        except ValueError:
            pass
        self.event_generate('<<ListboxSelect>>')
        
    def select_cb(self, *args):
        self.event_generate('<<ListboxSelect>>')
        
