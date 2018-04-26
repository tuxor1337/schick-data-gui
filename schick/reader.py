
import re, struct

from schick.util import process_nvf, process_ani, sizeof, parse_pal, img_to_rgb
from schick.pp20 import PP20File
from schick.automap import draw_automap, parse_locations_tab, parse_locations_ddt

text_ltx_towns = 235
ds_offset = 0x173c0

items_dat_flags = ["armor", "weapon", "useable", "food", "stackable", "herb/potion", "undropable", "unknown"]

informer_keys = ["state_offset", "txt_offset", "title", "head_id"]
state_keys = ["txt_id", "opt1", "opt2", "opt3", "ans1", "ans2", "ans3"]
route_keys = ["from", "to", "length", "speed_mod", "encounters", "u1", "u2", "fights", "u3"]
tevent_keys = ["route_id", "place", "tevent_id"]

graphics_full_size = ["KARTE.DAT", "SKULL.NVF"]
graphics_full_size_pp20 = [
    "PLAYM_UK", "PLAYM_US", "ZUSTA_UK", "ZUSTA_US", "BUCH.DAT",
    "KCBACK.DAT", "KCLBACK.DAT", "KDBACK.DAT", "KDLBACK.DAT", "KLBACK.DAT",
    "KLLBACK.DAT", "KSBACK.DAT", "KSLBACK.DAT"
]
graphics_fixed_size = {
    "ICONS": (24, 24, 55), # 0x302 undetermined bytes left in this file!
    "BICONS": (24, 24, 9),
    "IN_HEADS.NVF": (32, 32, 71),
    "SPSTAR.NVF": (32, 32, 3),
    "POPUP.DAT": (8, 16, 13)
}
graphics_fonts = ["FONT6", "FONT8"]
graphics_nvf_ani = ["MONSTER", "MFIGS", "WFIGS","ANIS"]
graphics_nvf = ["COMPASS", "TEMPICON", "SPLASHES.DAT"] + graphics_nvf_ani

random_tlk_files = ["SCHMIED.TLK", "GHANDEL.TLK", "KHANDEL.TLK", "WHANDEL.TLK", "HERBERG.TLK"]

maps_large = ["THORWAL.DAT", "PREM.DAT", "PHEXCAER.DAT"]

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

        self.init_palettes()

    def init_vars(self):
        self.vars = []
        self.vars_info = []
        self.v_offset = 0x0094
        for line in self.symbols_h:
            data = self.parse_symbols_h_line(line)
            if data is None:
                continue
            self.vars.append("%s (0x%04x)" % (data["name"], data["offset"]))
            self.vars_info.append(data)

    def init_palettes(self):
        """
        It's still not clear which palettes to use for those graphics that
        don't come with their own palette. Here are the palettes that are
        stored in the data segment together with the palette offsets used
        in the game (comment at end of line).
        Some of the palettes, such as PALETTE_BUILDINGS (at offset 0x80) or
        PALETTE_FLOOR (at offset 0x00) are loaded at game time, so those
        variables are not helpful.
        """
        self.pal_fight1 = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_FIGHT1"))) # 0x00 (0x20)
        self.pal_statuspage = parse_pal(self.get_var_bytes(self.get_var_by_name("STATUSPAGE_PALETTE"))) # 0x00 (0x20)
        self.pal_general = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_GENERAL"))) # 0x20 (0x20)
        self.pal_unkn4 = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_UNKNOWN4"))) # 0x40 (0x20)
        self.pal_unkn1 = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_UNKNOWN1"))) # 0x60 (0x20)
        self.pal_fight2 = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_FIGHT2"))) # 0x80 (0x14)
        self.pal_unkn3 = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_UNKNOWN3"))) # 0xc8 (0x03)
        self.pal_unkn2 = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_UNKNOWN2"))) # 0xd8 (0x08)
        self.pal_special = parse_pal(self.get_var_bytes(self.get_var_by_name("PALETTE_SPECIAL"))) # 0xe0 (0x20)

        pal_dummy = [[0,0,0]]*0x100
        pal_dummy[0x00:0x20] = self.pal_statuspage
        pal_dummy[0x20:0x40] = self.pal_general
        pal_dummy[0x40:0x60] = self.pal_unkn4
        pal_dummy[0x60:0x80] = self.pal_unkn1
        pal_dummy[0x80:0xc0] = self.pal_general + self.pal_special
        pal_dummy[0xc8:0xcb] = self.pal_unkn3
        pal_dummy[0xd8:0xe0] = self.pal_unkn2
        pal_dummy[0xe0:] = self.pal_special
        self.pal_standard = pal_dummy.copy()
        pal_dummy[0x00:0x20] = self.pal_fight1
        pal_dummy[0x80:0x94] = self.pal_fight2
        self.pal_fight = pal_dummy.copy()

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
        return self.read_archive_nvf_file("IN_HEADS.NVF", no)[0][0]

    def load_archive_file(self, fname):
        fileindex = self.archive_files.index(fname)
        self.schick_dat.seek(4*fileindex)
        start, end = struct.unpack("<LL", self.schick_dat.read(8))
        self.schick_dat.seek(start)
        return self.schick_dat, end - start

    def read_archive_file(self, fname):
        f_handle, f_len = self.load_archive_file(fname)
        return f_handle.read(f_len)

    def read_archive_items_dat(self):
        bytes = self.read_archive_file("ITEMS.DAT")[:-12]
        names = self.read_archive_tx_file("ITEMNAME")[:-1]
        ggsts = self.read_archive_nvf_file("GGSTS.NVF")[0]
        descr = []
        for i in range(0, len(bytes), 12):
            raw = struct.unpack("<HBBBHBHBB", bytes[i:i+12])
            flags = []
            for i,s in enumerate(items_dat_flags):
                if (raw[1] >> i) & 1:
                    flags.append(s)
            t = raw[2]
            if "weapon" in flags:
                t = self.get_ttx(48+t)
            descr.append([
                ["pic", raw[0]],
                ["flags", "{} ({:08b})".format(", ".join(flags), raw[1])],
                ["type", t],
                ["extra", raw[3]],
                ["weight", raw[4]],
                ["shop_unkn", raw[5]],
                ["shop_price", raw[6]],
                ["shop_rarity", raw[7]],
                ["magical", raw[8]]
            ])
        return names, descr, ggsts

    def read_archive_map_file(self, fname):
        dng_flag = ("DNG" == fname[-3:])
        map_size = 0x100
        if fname in maps_large:
            map_size = 0x200
        bytes = self.read_archive_file(fname)
        levels = 1 if not dng_flag else len(bytes)//(map_size+0x40)
        images = []
        for l in range(levels):
            loc_bytes = b'' if dng_flag else bytes[map_size + 0x40:]
            map_bytes = bytes[l*(map_size+0x40):][:map_size]
            img = draw_automap(map_bytes, loc_bytes, fname)
            img['palette'] = self.pal_standard
            img['palette'][:0x14] = self.pal_fight2
            img_to_rgb(img)
            images.append(img)
        loctab = []
        if dng_flag:
            dng_ddt = self.read_archive_file(fname[:-4] + ".DDT")
            loctab = parse_locations_ddt(dng_ddt)
        else:
            town_ltx_base = self.archive_files.index("THORWAL.LTX")
            town_idx = self.archive_files.index(fname) - self.archive_files.index("THORWAL.DAT")
            town_ltx = self.archive_files[town_ltx_base + town_idx]
            town_tx = self.read_archive_tx_file(town_ltx)
            loctab = parse_locations_tab(loc_bytes, town_tx)
        return images, loctab

    def read_archive_tx_file(self, fname):
        tx_index = self.read_archive_file(fname).decode("cp850").split("\0")
        return [s.replace("\r","\n").strip() for s in tx_index]

    def read_archive_nvf_file(self, fname, no=None):
        images = []
        max_pages = 1
        if fname in graphics_full_size:
            bytes = self.read_archive_file(fname)
            pal_offset = 320*200 + 2
            pal_len = len(bytes) - pal_offset
            img = {
                "width": 320,
                "height": 200,
                "scaling": 0,
                "raw": bytes[0:320*200],
                "palette": parse_pal(bytes[pal_offset:pal_offset+pal_len])
            }
            img_to_rgb(img)
            images.append(img)
        elif fname in graphics_full_size_pp20:
            f = PP20File(self.read_archive_file(fname))
            bytes = f.decrunch()
            if len(bytes) > 64000:
                palette = 8*parse_pal(bytes[64002:])
                bytes = bytes[:64000]
            else:
                print("No palette! Trying standard palette...")
                palette = self.pal_standard
            img = {
                "width": 320,
                "height": 200,
                "scaling": 0,
                "raw": bytes,
                "palette": palette
            }
            img_to_rgb(img)
            images.append(img)
        elif fname in graphics_fixed_size.keys():
            if fname == "POPUP.DAT":
                f = PP20File(self.read_archive_file(fname))
                bytes = f.decrunch()
            else:
                bytes = self.read_archive_file(fname)
            width, height, count = graphics_fixed_size[fname]
            print("No palette! Trying standard palette...")
            for i, offset in enumerate(range(0, count*width*height, width*height)):
                if no is not None and i != no:
                    continue
                img = {
                    "width": width,
                    "height": height,
                    "scaling": 1.5,
                    "raw": bytes[offset:offset+width*height],
                    "palette": self.pal_standard
                }
                img_to_rgb(img)
                images.append(img)
        elif fname in graphics_fonts:
            bytes = self.read_archive_file(fname)
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
                img_to_rgb(img)
                images.append(img)
        elif fname[-3:] == "NVF" or fname in graphics_nvf:
            if fname in graphics_nvf_ani:
                if no is None or no < 0: no = 0
                bytes = self.read_archive_file("%s.TAB" % fname)
                max_pages = len(bytes) / 4 - 1
                no = min(no, max_pages-1)
                offset = struct.unpack("<L", bytes[no*4:(no+1)*4])[0]
                length = struct.unpack("<L", bytes[(no+1)*4:(no+2)*4])[0] - offset
                handle, _ = self.load_archive_file(fname)
                handle.seek(offset, 1)
                if fname == "ANIS":
                    nvf_imgs, pal_raw = process_ani(handle.read(length))
                else:
                    nvf_imgs, pal_raw = process_nvf(handle, length)
            else:
                nvf_imgs, pal_raw = process_nvf(*self.load_archive_file(fname))
            # ["TFLOOR1.NVF", "TFLOOR2.NVF", "FACE.NVF", "HYGGELIK.NVF"]
            palette = parse_pal(pal_raw)
            if fname in ["GUERTEL.NVF", "LTURM.NVF", "MARBLESL.NVF", "SHIPSL.NVF", "STONESL.NVF", "TDIVERSE.NVF"]:
                palette = [[0,0,0]]*0x80 + palette
            elif len(palette) == 0:
                print("No palette! Trying fight palette...")
                palette = self.pal_fight
                if fname == "OBJECTS.NVF":
                    palette = self.pal_standard[0xe0:] + self.pal_fight[0x20:]
            if len(palette) < 256:
                palette += [[0,0,0]]*(256-len(palette))
            for i in nvf_imgs:
                img = {
                    "width": i['width'],
                    "height": i['height'],
                    "scaling": 1.5,
                    "raw": i['raw'],
                    "palette": palette
                }
                img_to_rgb(img)
                images.append(img)
        return images, max_pages

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
            state = dict(zip(state_keys, struct.unpack("<h6B", struct_bytes)))
            if tlk_random:
                state['opt1'] *= 4
                state['opt2'] *= 4
                state['opt3'] *= 4
            state['opt'] = [state['opt1'], state['opt2'], state['opt3']]
            state['ans'] = [state['ans1'], state['ans2'], state['ans3']]
            state_tab.append(state)

        text_tab = tlk_handle.read(64000).split(b"\0")
        for i, t in enumerate(text_tab):
            text_tab[i] = t.decode("cp850").replace("\r","\n").strip()
        return tlk_random, informer_tab, state_tab, text_tab

