
import string, math, struct, re
import numpy as np
from schick.pp20 import PP20File

def process_nvf(handle, length):
    nvf_type, count = struct.unpack("<BH", handle.read(3))
    n = 3
    compressed_sizes = []
    dims = []
    if nvf_type in [0x00]:
        dims = [struct.unpack("<HH", handle.read(4))]*count
        compressed_sizes = [dims[0][0]*dims[0][1]]*count
        n += 4
    elif nvf_type in [0x02, 0x04]:
        dims = [struct.unpack("<HH", handle.read(4))]*count
        compressed_sizes = [struct.unpack("<L", handle.read(4))[0] for n in range(count)]
        n += 4 + count*4
    elif nvf_type in [0x01]:
        dims = [struct.unpack("<HH", handle.read(4)) for n in range(count)]
        compressed_sizes = [w*h for w,h in dims]
        n += 4*count
    else:
        for n in range(count):
            w, h, s = struct.unpack("<HHL", handle.read(8))
            dims.append((w,h))
            compressed_sizes.append(s)
            n += 8
    imgs = []
    for s, cs in zip(dims, compressed_sizes):
        data = handle.read(cs)
        if nvf_type in [0x04, 0x05]:
            data = decomp_rle(data)
        elif nvf_type in [0x02, 0x03]:
            data = decomp_pp20(data)
        n += cs
        imgs.append({
            "width": s[0],
            "height": s[1],
            "raw": data
        })
    pal_bytes = b''
    if length-4 > n:
        pal_count = struct.unpack("<H", handle.read(2))[0]
        if pal_count*3 <= length - n:
            pal_bytes = handle.read(pal_count*3)
    return imgs, pal_bytes

def decomp_rle(bytes):
    src = [int(b) for b in bytes]
    dst = []
    while len(src) > 0:
        tmp = src.pop(0)
        if tmp == 0x7f:
            cnt = src.pop(0)
            dst += [src.pop(0)]*cnt
        else:
            dst.append(tmp);
    return dst

def decomp_pp20(src):
	f = PP20File(src)
	return f.decrunch()

def img_to_rgb(img):
    img["rgb"] = np.zeros((len(img["raw"]), 3), dtype=np.uint8)
    for i, b in enumerate(img["raw"]):
        if img["palette"] is None:
            img["rgb"][i,:] = np.array([b,b,b], dtype=np.uint8)
        else:
            img["rgb"][i,:] = np.array(img["palette"][b], dtype=np.uint8)
    img["rgb"] = img["rgb"].reshape((img["height"], img["width"], 3))

def parse_pal(bytes):
    palette = []
    for i in range(0, len(bytes), 3):
        palette.append([b*4 for b in bytes[i:i+3]])
    return palette

varsize_tab = {
    'char': 1,
    'short': 2,
    'long': 4,
    'RealPt': 4
}

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

def hexdump(bytes):
    if len(bytes) == 0:
        return "0000: "
    result = ""
    counter = 0
    counter_len = max(4, math.ceil(math.log(len(bytes))/math.log(16)))
    for i in range(0,len(bytes),16):
        buf = bytes[i:i+16]
        buf2 = [('%02x' % i) for i in buf]
        cnt_str = ("%%0%dx" % counter_len) % (counter * 16)
        result += '{0}: {1:<39}  {2}\n'.format(cnt_str,
            ' '.join([''.join(buf2[i:i + 2]) for i in range(0, len(buf2), 2)]),
            ''.join([chr(c) if c in string.printable[:-5].encode("ascii") else '.' for c in buf]))
        counter += 1
    return result
