
import re, struct
import numpy as np

varsize_tab = {
    'char': 1,
    'short': 2,
    'long': 4,
    'RealPt': 4
}

text_ltx_towns = 235
ds_offset = 0x173c0

informer_keys = ["state_offset", "txt_offset", "title", "head_id"]
state_keys = ["txt_id", "opt1", "opt2", "opt3", "ans1", "ans2", "ans3"]
route_keys = ["from", "to", "length", "speed_mod", "encounters", "u1", "u2", "fights", "u3"]
tevent_keys = ["route_id", "place", "tevent_id"]

random_tlk_files = ["SCHMIED.TLK", "GHANDEL.TLK", "KHANDEL.TLK", "WHANDEL.TLK", "HERBERG.TLK"]

def sizeof(varstr):
    varstr = re.sub(r'(un)?signed\s+', "", varstr)
    arrsize = 1
    if varstr[-1] == "]":
        pos = varstr.find("[")
        arrsize = int(varstr[pos+1:-1])
        varstr = varstr[:pos]
    if varstr[-1] == ")":
        pos = varstr.find("(")
        varsize = int(varstr[pos+1:-1])
    else:
        varsize = varsize_tab[varstr]
    return varsize*arrsize

class SchickReader(object):
    def __init__(self, schickm_exe, schick_dat, symbols_h):
        self.schickm_exe = schickm_exe
        self.schick_dat = schick_dat
        self.symbols_h = symbols_h
        
        self.text_ltx_index = None
        self.tevents_tab = None
        self.routes_tab = None
        
        self.init_vars()
        
        self.archive_files = self.get_var_bytes(self.get_var_by_name("SCHICK_DAT_FNAMES")).split(b"\0")
        self.archive_files = [s.strip().decode() for s in self.archive_files[1:-1]]
        
    def init_vars(self):
        self.vars = []
        self.vars_info = []
        self.v_offset = 0
        for line in self.symbols_h:
            data = self.parse_symbols_h_line(line)
            if data is None:
                continue
            self.vars.append("%s (0x%04x)" % (data["name"], data["offset"]))
            self.vars_info.append(data)
            
    def parse_symbols_h_line(self, line):
        if line[:2] not in ["//", "#d"] or line.find("SYMBOLS_H") >= 0:
            return None
        var = {
            "mark": "?",
            "name": "",
            "offset": self.v_offset,
            "type": "",
            "comment": ""
        }
        if line[:4] == "// ?":
            gapsize = int(line[4:])
            self.v_offset += gapsize
            var["name"] = "%d unknown bytes" % gapsize
        else:
            var["mark"] = line[0]
            line = re.sub(r'^(#|//)define ', "", line)
            pos = line.find("(")
            var["name"] = line[:pos].strip()
            var["offset"] = int(line[pos+3:pos+7], 16)
            l_type, _, l_comment = line[pos+14:-3].strip().partition(";")
            var["type"] = l_type.strip()
            var["comment"] = l_comment.strip()
            
            if var["offset"] != self.v_offset:  
                print("0x{:04x} != 0x{:04x}".format(var["offset"], self.v_offset))
                
            self.v_offset += sizeof(var["type"])
        return var
        
    def get_var_by_offset(self, offset):
        for idx, v in enumerate(self.vars_info):
            if v["offset"] == offset:
                return idx
        return None
        
    def get_var_by_name(self, name):
        for idx, v in enumerate(self.vars_info):
            if v["name"] == name:
                return idx
        return None
            
    def get_var_mark(self, idx):
        return self.vars_info[idx]["mark"]
            
    def get_var_name(self, idx):
        return self.vars_info[idx]["name"]
        
    def get_var_type(self, idx):
        return self.vars_info[idx]["type"]
        
    def get_var_comment(self, idx):
        return self.vars_info[idx]["comment"]
        
    def get_var_bytes(self, idx):
        offset = self.vars_info[idx]["offset"]
        if idx == len(self.vars)-1:
            length = sizeof(self.vars_info[idx]["type"])
        else:
            length = self.vars_info[idx+1]["offset"] - offset
        self.schickm_exe.seek(ds_offset + offset)
        return self.schickm_exe.read(length)
        
    def get_ttx(self, no):
        if self.text_ltx_index is None:
            self.text_ltx_index = self.read_archive_tx_file("TEXT.LTX")
        return self.text_ltx_index[no]
        
    def get_town(self, no):
        return self.get_ttx(text_ltx_towns + no)
        
    def load_tevents(self):
        if self.tevents_tab is not None:
            return
        data = self.get_var_bytes(self.get_var_by_name("TEVENTS_TAB"))
        self.tevents_tab = []
        for i in range(155):
            self.tevents_tab.append(dict(
                zip(tevent_keys, struct.unpack("<3B", data[3*i:3*(i+1)]))
            ))
            self.tevents_tab[-1]["route_id"] -= 1
        
    def load_routes(self):
        if self.routes_tab is not None:
            return
        data = self.get_var_bytes(self.get_var_by_name("ROUTES_TAB"))
        self.routes_tab = []
        for i in range(59):
            self.routes_tab.append(dict(
                zip(route_keys, struct.unpack("<9B", data[9*i:9*(i+1)]))
            ))
        
    def get_route(self, no):
        self.load_routes()
        return self.routes_tab[no]
        
    def get_tevent(self, no):
        self.load_tevents()
        return self.tevents_tab[no]
        
    def get_in_head(self, no):
        return self.read_archive_nvf_file("IN_HEADS.NVF", no)[0]
        
    def load_archive_file(self, fname):
        fileindex = self.archive_files.index(fname)
        self.schick_dat.seek(4*fileindex)
        start, end = struct.unpack("<LL", self.schick_dat.read(8))
        self.schick_dat.seek(start)
        return self.schick_dat, end - start
        
    def read_archive_file(self, fname):
        f_handle, f_len = self.load_archive_file(fname)
        return f_handle.read(f_len)
        
    def read_archive_tx_file(self, fname):
        tx_index = self.read_archive_file(fname).decode("cp850").split("\0")
        return [s.replace("\r","\n").strip() for s in tx_index]
        
    def parse_pal(self, bytes, offset=0):
        palette = [[0,0,0]]*offset
        for i in range(0, len(bytes), 3):
            palette.append([b*4 for b in bytes[i:i+3]])
        return palette
        
    def img_to_rgb(self, img):
        img["rgb"] = np.zeros((len(img["raw"]), 3), dtype=np.uint8)
        for i, b in enumerate(img["raw"]):
            if img["palette"] is None:
                img["rgb"][i,:] = 4*np.array([b,b,b], dtype=np.uint8)
            else:
                img["rgb"][i,:] = np.array(img["palette"][b], dtype=np.uint8)
        img["rgb"] = img["rgb"].reshape((img["height"], img["width"], 3))
        
    def read_archive_nvf_file(self, fname, no=None):
        bytes = self.read_archive_file(fname)
        images = []
        if fname in ["KARTE.DAT", "SKULL.NVF"]:
            pal_offset = 320*200 + 2
            pal_len = len(bytes) - pal_offset
            img = {
                "width": 320,
                "height": 200,
                "scaling": 0,
                "raw": bytes[0:320*200],
                "palette": self.parse_pal(bytes[pal_offset:pal_offset+pal_len])
            }
            self.img_to_rgb(img)
            images.append(img)
        elif fname == "IN_HEADS.NVF":
            pal_bytes = self.get_var_bytes(self.get_var_by_offset(0xb2b1))
            pal_parsed = self.parse_pal(pal_bytes, 32)
            for i, offset in enumerate(range(0, len(bytes), 1024)):
                if no == None or no == i:
                    img = {
                        "width": 32,
                        "height": 32,
                        "scaling": 1.5,
                        "raw": bytes[offset:offset+32*32],
                        "palette": pal_parsed
                    }
                    self.img_to_rgb(img)
                    images.append(img)
        elif fname[:4] == "FONT":
            palette = [[0x21, 0x61, 0x25], [255,255,255]]
            for offset in range(0, len(bytes), 8):
                raw = "".join("{:08b}".format(b) for b in bytes[offset:offset+8])
                raw = [ord(b) - ord('0') for b in raw]
                img = {
                    "width": 8,
                    "height": 8,
                    "scaling": 3,
                    "raw": raw,
                    "palette": palette
                }
                self.img_to_rgb(img)
                images.append(img)
        return images
        
    def read_archive_tlk_file(self, fname):
        tlk_handle, tlk_len = self.load_archive_file(fname)
        tlk_random = False
        if fname in random_tlk_files:
            tlk_random = True
        
        header_bytes = tlk_handle.read(6)
        off, partners = struct.unpack("<LH", header_bytes)
        
        informer_bytes = tlk_handle.read(partners*38)
        informer_tab = []
        for i in range(partners):
            struct_bytes = informer_bytes[i*38:(i+1)*38]
            informer = dict(
                zip(informer_keys, struct.unpack("<LH30sH", struct_bytes))
            )
            informer['title'] = informer['title'].strip(b"\0").decode("cp850")
            informer['state_offset'] = informer['state_offset']//8
            informer_tab.append(informer)
        
        state_bytes = tlk_handle.read(off - partners*38)
        state_tab = []
        for i in range(len(state_bytes)//8):
            struct_bytes = state_bytes[i*8:(i+1)*8]
            state = zip(state_keys, struct.unpack("<h6B", struct_bytes))
            state = dict(state)
            if tlk_random:
                state['opt1'] *= 4
                state['opt2'] *= 4
                state['opt3'] *= 4
            state_tab.append(state)
        
        text_tab = tlk_handle.read(64000).split(b"\0")
        for i, t in enumerate(text_tab):
            text_tab[i] = t.decode("cp850").replace("\r","\n").strip()
        return tlk_random, informer_tab, state_tab, text_tab
        
