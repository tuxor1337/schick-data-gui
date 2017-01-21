
import string, math

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
