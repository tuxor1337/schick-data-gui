
# This file is part of schick-data-gui
# Copyright (C) 2018  Thomas Vogt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from schick.gui.dat_extra import *

from tkinter import *
from tkinter import ttk

meta_files = ["MONSTER.TAB", "MFIGS.TAB", "WFIGS.TAB", "ANIS.TAB"]
ani_files = ["MONSTER", "MFIGS", "WFIGS", "ANIS"]
fight_files = ["FIGHT.LST", "SCENARIO.LST", "MONSTER.DAT", "ANI.DAT", "WEAPANI.DAT", "FIGHTTXT.LTX"]
tx_files = ["ITEMNAME", "MONNAMES"]
nvf_files = [
    "KARTE.DAT", "COMPASS", "TEMPICON", "SPLASHES.DAT", "PLAYM_UK", "PLAYM_US",
    "ZUSTA_UK", "ZUSTA_US", "BUCH.DAT", "KCBACK.DAT", "KCLBACK.DAT",
    "KDBACK.DAT", "KDLBACK.DAT", "KLBACK.DAT", "KLLBACK.DAT", "KSBACK.DAT",
    "KSLBACK.DAT", "POPUP.DAT", "BICONS", "ICONS", "FONT6", "FONT8"
] + ani_files
map_files = [
    "THORWAL.DAT", "SERSKE.DAT", "BREIDA.DAT", "PEILINEN.DAT", "ROVAMUND.DAT",
    "NORDVEST.DAT", "KRAVIK.DAT", "SKELELLE.DAT", "MERSKE.DAT", "EFFERDUN.DAT",
    "TJOILA.DAT", "RUKIAN.DAT", "ANGBODIRTAL.DAT", "AUPLOG.DAT", "VILNHEIM.DAT",
    "BODON.DAT", "OBERORKEN.DAT", "PHEXCAER.DAT", "GROENVEL.DAT",
    "FELSTEYN.DAT", "EINSIEDL.DAT", "ORKANGER.DAT", "CLANEGH.DAT", "LISKOR.DAT",
    "THOSS.DAT", "TJANSET.DAT", "ALA.DAT", "ORVIL.DAT", "OVERTHORN.DAT",
    "ROVIK.DAT", "HJALSING.DAT", "GUDDASUN.DAT", "KORD.DAT", "TREBAN.DAT",
    "ARYN.DAT", "RUNINSHA.DAT", "OTTARJE.DAT", "SKJAL.DAT", "PREM.DAT",
    "DASPOTA.DAT", "RYBON.DAT", "LJASDAHL.DAT", "VARNHEIM.DAT", "VAERMHAG.DAT",
    "TYLDON.DAT", "VIDSAND.DAT", "BRENDHIL.DAT", "MANRIN.DAT", "FTJOILA.DAT",
    "FANGBODI.DAT", "HJALLAND.DAT", "RUNIN.DAT",
    "SHIP.DNG", "F046.DNG", "F051.DNG", "F061.DNG", "F076.DNG", "F094.DNG",
    "F100.DNG", "F108.DNG", "F126.DNG", "F129.DNG", "F131.DNG", "OBER.DNG",
    "PREM.DNG", "THORWAL.DNG", "FINAL.DNG"
]

class SchickDatContent(ttk.Frame):
    def __init__(self, master, schick_reader):
        ttk.Frame.__init__(self, master)

        self.schick_reader = schick_reader
        self.index = self.schick_reader.archive_files

        self.v_name = StringVar()
        self.page_str = StringVar(value="1/1")
        self.content = None

        lbl = ttk.Label(self, textvariable=self.v_name, font="bold")
        page_lbl = ttk.Label(self, textvariable=self.page_str)
        self.b_prev = Button(self, text="<<")
        self.b_next = Button(self, text=">>")

        lbl.grid(column=0, row=0, padx=10, pady=5, sticky=(N,W))
        page_lbl.grid(column=1, row=0, padx=10, pady=5, sticky=(N,W))
        self.b_prev.grid(column=2, row=0, padx=2, sticky=(N,W))
        self.b_next.grid(column=3, row=0, padx=2, sticky=(N,W))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.v_name.set('')

        self.page = 0
        self.max_pages = 1
        self.b_prev.config(state=DISABLED)
        self.b_next.config(state=DISABLED)
        self.b_prev.config(command=lambda: self.button_cb(False))
        self.b_next.config(command=lambda: self.button_cb())

    def show(self, idx, page=None):
        if page is None:
            self.fid = idx
            self.page = 0

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
            self.content = SchickDatNVFContent(self, self.schick_reader, fname, self.page)
        elif fname in map_files:
            self.content = SchickDatMapContent(self, self.schick_reader, fname, self.page)
        elif fname == "ITEMS.DAT":
            self.content = SchickDatItemsContent(self, self.schick_reader)
        else:
            self.content = SchickDatHexContent(self, self.schick_reader, fname)
        self.max_pages = self.content.max_pages
        self.content.grid(column=0, row=1, columnspan=4, padx=10, pady=5, sticky=(N,E,S,W))

        self.b_prev.config(state=DISABLED)
        self.b_next.config(state=DISABLED)
        if self.page < self.max_pages - 1:
            self.b_next.config(state=ACTIVE)
        if self.page > 0:
            self.b_prev.config(state=ACTIVE)
        self.page_str.set("%d/%d" % (self.page+1, self.max_pages))

    def button_cb(self, next=True):
        if next:
            self.page += 1
        else:
            self.page -= 1
        self.show(self.fid, self.page)

    def color_cb(self, idx):
        name = self.index[idx]
        if name[-2:] == "TX" or name in tx_files:
            return "#000000", '#ffff77'
        elif name in nvf_files or name[-3:] == "NVF":
            return "#ffffff", '#339933'
        elif name in fight_files:
            return "#ffffff", '#333333'
        elif name in meta_files:
            return "#000000", '#aaeeaa'
        elif name in map_files:
            return "#000000", '#ffaaee'
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

