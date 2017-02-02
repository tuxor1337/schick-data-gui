
import numpy as np

import struct

base_tile = np.ones((7,7))

dng_tile_colors = {
     0: 19,
     1: 11,
     2: 11,
     3:  3,
     4:  6,
     5:  2,
     6:  9,
     7:  1,
     8: 17,
     9: 11,
}

tile_colors = {
     0: 19,
     1: 12, # temple
     2: 11, # HOUSE1
     3: 11, # HOUSE2
     4: 11, # HOUSE3
     5: 11, # HOUSE4
     6:  3, # water
     7: 18, # grass
     8:  1, # direction sign
     9:  6, # tavern/inn
    10: 15, # shop
    11:  9,
    12:  5,
    13: 10,
}

loc_descr = {
    0: ( 0, "0"),
    1: ( 0, "1"),
    2: ( 1, "temple"),
    3: ( 9, "tavern"),
    4: (12, "healer"),
    5: (10, "shop"),
    7: ( 9, "inn"),
    8: (11, "smith"),
    9: ( 0, "market"),
   10: ( 0, "landmark"),
   11: ( 0, "harbor"),
   12: ( 8, "direction sign"),
   13: ( 0, "informant"),
   14: ( 0, "dungeon"),
   15: ( 0, "15"),
   16: ( 0, "16"),
   17: ( 0, "misc"),
   18: ( 0, "18"),
}

border_index = [0, 15, 31, 63, 95, 127, 159, 175, 191, 207, 223, 239]

def get_tile_color(x, y, loc_bytes, town):
    xy = (x << 8) + y
    for i in range(0, len(loc_bytes), 6):
        d, t = struct.unpack("<HB", loc_bytes[i:i+3])
        if d == xy:
            if town == "THORWAL":
                if x == 4 and y == 13:
                    return 13
                elif x == 5 and y == 2:
                    return 8
                elif (x == 5 and y == 1) or (x ==  5 and y ==  4) \
                        or (x ==  3 and y ==  6) or (x == 13 and y ==  8) \
                        or (x == 20 and y == 11) or (x ==  5 and y ==  5) \
                        or (x ==  3 and y == 10):
                    return 9
            elif town == "PREM":
                if x == 28 and y == 9:
                    return 9
            elif town == "GUDDASUN":
                if x == 1 and y == 14:
                    return 8
            if t <= 8:
                return loc_descr[t][0]
    return 0

def automap_tile(x, y):
    return (slice(1+8*y,1+8*y+7),slice(1+8*x,1+8*x+7))

def get_border_index(val):
    i = 0
    while border_index[i] < val: i += 1
    if i > 0: i -= 1
    return i

def draw_entrance(dir):
    tile = base_tile.copy().reshape(-1)
    if dir == 0:
        c, dst = 1, 0*7 + 2
    elif dir == 1:
        c, dst = 7, 2*7 + 6
    elif dir == 2:
        c, dst = 1, 6*7 + 2
    elif dir == 3:
        c, dst = 7, 2*7 + 0
    tile[dst] = tile[dst+c] = tile[dst+2*c] = 0
    return tile.reshape((7,7))

def draw_automap(map_bytes, loc_bytes, fname):
    dng_flag = fname[-3:] == "DNG"
    w = 16 if len(map_bytes) == 16*16 else 32
    h = 16
    arr = np.zeros((h*8+1,w*8+1), order='C', dtype=np.uint8)
    for i,b in enumerate(map_bytes):
        x, y = i%w, i//w
        tile = base_tile
        if dng_flag:
            type = b >> 4
            color = dng_tile_colors[type] if type <= 9 else 1
        else:
            type = get_tile_color(x, y, loc_bytes, fname[:-4])
            if type == 0:
                type = get_border_index(b)
            color = tile_colors[type] if type <= 13 else 0
            if type not in [0,6,7,8]:
                tile = draw_entrance(b & 3)
        arr[automap_tile(x, y)] = color * tile
    img = {
        "width": w*8+1,
        "height": h*8+1,
        "scaling": 1.5,
        "raw": arr.tobytes()
    }
    return img

def parse_locations_tab(loc_bytes, town_tx):
    loctab = []
    for i in range(0, len(loc_bytes), 6):
        d, t, l, tx = struct.unpack("<HBBH", loc_bytes[i:i+6])
        if t in [11,12]: # direction sign or harbor
            tx = (tx >> 8, tx & 0xf)
        else:
            tx = town_tx[tx]
        loctab.append([(0, d >> 8, d & 0xff), loc_descr[t][1], l, tx])
    return loctab

def parse_dng_coords(coords):
    pos = coords % 4096
    return (coords // 4096, pos >> 8, pos & 0xff)

def parse_locations_ddt(ddt_bytes):
    low, high = struct.unpack("<HH", ddt_bytes[:4])
    dng_fights = ddt_bytes[4:][:low]
    dng_doors = ddt_bytes[4:][low:high]
    dng_stairs = ddt_bytes[4:][high:][:0x7d0]
    loctab = []

    for i in range(0, len(dng_fights), 14):
        # pos, fight_id, u1,u2,u3,u4, ap
        fig = struct.unpack("<7H", dng_fights[i:i+14])
        coords = parse_dng_coords(fig[0])
        loctab.append([coords, "fight", fig[1],
            "AP: {}".format(fig[6])
        ])

    for i in range(0, len(dng_doors), 5):
        # pos, KK, SCHLOESSER, FORAMEN
        door = struct.unpack("<HBBB", dng_doors[i:i+5])
        coords = parse_dng_coords(door[0])
        loctab.append([coords, "door", 0,
            "KK: {}, TA: {}, SP: {}".format(*door[1:])
        ])

    lvl_change = { 0x40: "-2", 0x00: "-1", 0x80: "+1", 0xc0: "+2" }
    for i in range(0, len(dng_stairs), 4):
        # pos, target_x, target_y
        staircase = struct.unpack("<HBB", dng_stairs[i:i+4])
        coords = parse_dng_coords(staircase[0])
        loctab.append([coords, "staircase", 0,
            "({},{}), dir: {}, lvl:{})".format(
                staircase[1]&0xf, staircase[2]&0xf, staircase[2]>>4,
                lvl_change[staircase[1]&0xf0]
            )
        ])

    return loctab

