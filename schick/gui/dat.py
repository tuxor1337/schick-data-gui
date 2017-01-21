
from schick.gui.dat_extra import *

from tkinter import *
from tkinter import ttk

nvf_files = [
    "KARTE.DAT", "GENTIT.DAT", "DSALOGO.DAT", "HEADS.DAT", "COMPASS",
    "TEMPICON", "ATTIC", "SPLASHES.DAT", "PLAYM_UK", "PLAYM_US", "ZUSTA_UK",
    "ZUSTA_US", "BUCH.DAT", "KCBACK.DAT", "KCLBACK.DAT", "KDBACK.DAT",
    "KDLBACK.DAT", "KLBACK.DAT", "KLLBACK.DAT", "KSBACK.DAT", "KSLBACK.DAT",
    "POPUP.DAT", "BICONS", "ICONS", "FONT6", "FONT8"
]

ani_files = ["MONSTER", "MONSTER.TAB", "MFIGS", "MFIGS.TAB", "WFIGS", "WFIGS.TAB", "ANIS", "ANIS.TAB"]
fight_files = ["FIGHT.LST", "SCENARIO.LST", "MONSTER.DAT", "ANI.DAT", "WEAPANI.DAT", "FIGHTTXT.LTX"]
tx_files = ["ITEMNAME", "MONNAMES"]

class SchickDatContent(ttk.Frame):
    def __init__(self, master, schick_reader):
        ttk.Frame.__init__(self, master)

        self.schick_reader = schick_reader
        self.index = self.schick_reader.archive_files

        self.v_name = StringVar()
        self.content = None

        lbl = ttk.Label(self, textvariable=self.v_name, font="bold")

        lbl.grid(column=0, row=0, padx=10, pady=5, sticky=(N,W))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.v_name.set('')

    def show(self, idx):
        fname = self.index[idx]
        self.v_name.set(fname)
        if self.content is not None:
            self.content.grid_forget()
            self.content.destroy()
        if fname in tx_files or fname[-2:] == "TX":
            self.content = SchickDatTxContent(self, self.schick_reader, fname)
        elif fname[-3:] == "TLK":
            self.content = SchickDatTlkContent(self, self.schick_reader, fname)
        elif fname in nvf_files or fname[-3:] == "NVF":
            self.content = SchickDatNVFContent(self, self.schick_reader, fname)
        else:
            self.content = SchickDatHexContent(self, self.schick_reader, fname)
        self.content.grid(column=0, row=1, padx=10, pady=5, sticky=(N,E,S,W))

    def color_cb(self, idx):
        name = self.index[idx]
        if name[-2:] == "TX" or name in tx_files:
            return "#000000", '#ffff77'
        elif name in nvf_files or name[-3:] == "NVF":
            return "#ffffff", '#339933'
        elif name in fight_files:
            return "#ffffff", '#333333'
        elif name in ani_files:
            return "#000000", '#aaeeaa'
        elif name.find("ROUT") >= 0:
            return "#000000", '#ff5555'
        elif name[-3:] == "NPC":
            return "#000000", '#ffaaaa'
        elif name[-3:] == "XMI":
            return "#000000", '#aaaaff'
        elif name[-3:] == "VOC":
            return "#000000", '#7777ff'
        elif name[-2:] == "AD":
            return "#000000", '#ddddff'
        elif name[-3:] == "TLK":
            return "#000000", '#ffcc88'
        else:
            return None

