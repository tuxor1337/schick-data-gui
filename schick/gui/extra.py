
from schick.gui.util import FilteredListbox

from tkinter import *
from tkinter import ttk

class SchickXTEventsContent(ttk.Frame):
    def __init__(self, master, schick_reader):
        ttk.Frame.__init__(self, master)

        self.schick_reader = schick_reader
        self.init_tevents()

        self.lbox = FilteredListbox(self, listvariable=self.tevents, height=30)

        self.lbox.grid(column=0, row=0, sticky=(N,E,S,W))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.lbox.bind("<<ListboxSelect>>", self.select_cb)

    def init_tevents(self):
        self.tevents = []
        self.schick_reader.get_tevent(0)
        for idx, te in enumerate(self.schick_reader.tevents_tab):
            r = self.schick_reader.get_route(te["route_id"])
            if idx == 58:
                from_town = self.schick_reader.get_town(4) + "/" + self.schick_reader.get_town(5)
                to_town =  self.schick_reader.get_town(7) + "/" + self.schick_reader.get_town(8)
            else:
                from_town = self.schick_reader.get_town(r["from"])
                to_town = self.schick_reader.get_town(r["to"])
            self.tevents.append("id: %d, place: %d%% (%d:%s-%s)" % (
                te["tevent_id"],
                100*te["place"]/r["length"] if r["length"] > 0 else 100,
                te["route_id"], from_town, to_town,
            ))

    def select_cb(self, *args):
        pass

class SchickXRoutesContent(ttk.Frame):
    def __init__(self, master, schick_reader):
        ttk.Frame.__init__(self, master)

        self.schick_reader = schick_reader
        self.init_routes()

        self.lbox = FilteredListbox(self, listvariable=self.routes, height=30)

        self.lbox.grid(column=0, row=0, sticky=(N,E,S,W))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.lbox.bind("<<ListboxSelect>>", self.select_cb)

    def init_routes(self):
        self.routes = []
        self.schick_reader.get_route(0)
        for idx, r in enumerate(self.schick_reader.routes_tab):
            if idx == 58:
                from_town = self.schick_reader.get_town(4) + "/" + self.schick_reader.get_town(5)
                to_town =  self.schick_reader.get_town(7) + "/" + self.schick_reader.get_town(8)
            else:
                from_town = self.schick_reader.get_town(r["from"])
                to_town = self.schick_reader.get_town(r["to"])
            self.routes.append("#%02d: %s-%s" % (idx, from_town, to_town))

    def select_cb(self, *args):
        pass

class SchickXContent(ttk.Frame):
    def __init__(self, master, schick_reader):
        ttk.Frame.__init__(self, master)

        self.schick_reader = schick_reader
        self.index = ["Routes", "Travel events"]

        self.contents = {
            "Routes": SchickXRoutesContent(self, self.schick_reader),
            "Travel events": SchickXTEventsContent(self, self.schick_reader)
        }

        self.v_name = StringVar()
        self.content = None

        lbl = ttk.Label(self, textvariable=self.v_name, font="bold")

        lbl.grid(column=0, row=0, padx=10, pady=5, sticky=(N,W))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.v_name.set('')

    def show(self, idx):
        c_type = self.index[idx]
        self.v_name.set(c_type)
        if self.content is not None:
            self.content.grid_forget()
        self.content = self.contents[c_type]
        self.content.grid(column=0, row=1, padx=10, pady=5, sticky=(N,E,S,W))

    def color_cb(self, idx):
        pass

