
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

from schick.gui.util import FilteredListbox
from schick.gui.exe import SchickmExeContent
from schick.gui.dat import SchickDatContent
from schick.gui.extra import SchickXContent

from tkinter import *
from tkinter import ttk

class SchickGUI(ttk.Frame):
    def __init__(self, master, schick_reader):
        ttk.Frame.__init__(self, master, padding=(5, 5, 12, 12))

        self.contents = {
            "SCHICKM.EXE": SchickmExeContent(self, schick_reader),
            "SCHICK.DAT": SchickDatContent(self, schick_reader),
            "Extras": SchickXContent(self, schick_reader)
        }
        self.content_types = ["SCHICK.DAT", "SCHICKM.EXE", "Extras"]

        self.content = None
        self.lbox = FilteredListbox(self, color_cb=self.lbox_color_cb, height=30, width=30)

        self.content_type = StringVar()
        o_menu = OptionMenu(self, self.content_type, *self.content_types)

        o_menu.grid(column=0, row=0, sticky=(W,E))
        self.lbox.grid(column=0, row=1, sticky=(N,E,S,W))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.lbox.bind('<<ListboxSelect>>', self.lbox_select_cb)
        self.content_type.trace("w", self.type_change_cb)

        self.content_type.set(self.content_types[0])
        self.lbox_select_cb()

    def type_change_cb(self, *args):
        c_type = self.content_type.get()
        if self.content is not None:
            self.content.grid_forget()
        self.content = self.contents[c_type]
        self.content.grid(column=1, row=0, rowspan=2, sticky=(N,E,S,W))
        self.lbox.set_listvariable(self.content.index)
        self.lbox_select_cb()

    def lbox_select_cb(self, *args):
        idx = self.lbox.curselection()
        if idx is not None:
            self.content.show(idx)

    def lbox_color_cb(self, idx):
        return self.content.color_cb(idx)

