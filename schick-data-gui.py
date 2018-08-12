#!/usr/bin/python3
#
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

from schick.reader import SchickReader
from schick.gui.base import SchickGUI

from tkinter import *
from tkinter import ttk

import os

curr_path = os.path.dirname(os.path.realpath(__file__))

def destroy_cb():
    root.destroy()
    schickm_exe.close()
    schick_dat.close()
    symbols_h.close()

def window_setup():
    root.wm_title("Schick data GUI")
    w, h = 960, 600
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.protocol("WM_DELETE_WINDOW", destroy_cb)

root = Tk()

window_setup()

symbols_h = open(os.path.join(curr_path, "symbols.h"), "r")
schickm_exe = open(os.path.join(curr_path, "SCHICKM.EXE"), "rb")
schick_dat = open(os.path.join(curr_path, "SCHICK.DAT"), "rb")
schick_reader = SchickReader(schickm_exe, schick_dat, symbols_h)
SchickGUI(root, schick_reader).grid(column=0, row=0, sticky=(N,E,S,W))

root.mainloop()

