
from schick.util import hexdump
       
from tkinter import *
from tkinter import ttk

class SchickmExeContent(ttk.Frame):
    def __init__(self, master, schick_reader):
        ttk.Frame.__init__(self, master)
        
        self.schick_reader = schick_reader
        self.index = self.schick_reader.vars
        
        self.v_name = StringVar()
        self.v_type = StringVar()
        
        lbl = ttk.Label(self, textvariable=self.v_name, font="bold")
        lbl2 = ttk.Label(self, textvariable=self.v_type)
        self.v_comment = Text(self, height=5, width=100)
        self.v_hex = Text(self, height=20, width=63, padx=10, pady=10)
        
        lbl.grid(column=0, row=0, padx=10, pady=5, sticky=(N,W))   
        lbl2.grid(column=0, row=1, padx=10, pady=5, sticky=(N,W))
        self.v_comment.grid(column=0, row=2, padx=10, pady=5, sticky=(N,W))
        self.v_hex.grid(column=0, row=3, padx=10, pady=5, sticky=(N,S))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        self.v_name.set('')
        self.v_type.set('')
        
    def show(self, idx):
        self.v_name.set(self.index[idx])
        self.v_type.set(self.schick_reader.get_var_type(idx))
        self.v_comment.delete("1.0", END)
        self.v_comment.insert(END, self.schick_reader.get_var_comment(idx))
        self.v_hex.delete("1.0", END)
        self.v_hex.insert(END, hexdump(self.schick_reader.get_var_bytes(idx)))
        
    def color_cb(self, idx):
        mark = self.schick_reader.get_var_mark(idx)
        name = self.schick_reader.get_var_name(idx)
        if mark == "?":
            return "#000000", '#ffcccc'
        elif mark == "/":
            return "#000000", '#ffeecc'
        elif name.find("DATSEG") >= 0:
            return "#ffffff", '#339933'
        else:
            return None
