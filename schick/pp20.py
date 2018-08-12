
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

import struct

def _val(p):
    return p[0] << 16 | p[1] << 8 | p[2]

class PP20File(object):
    def __init__(self, src):
        head = src[:4]
        head_l = struct.unpack("<L", head)[0]
        if head == b'PP20' or head_l in [len(src), len(src) - 8]:
            self.dest_len = _val(src[-4:])
        else:
            raise Exception("PP20: Not a proper PP20 file!")

        self.dest = [0]*self.dest_len
        self.data = src[8:-4]
        self.offset_lens = src[4:8]
        self.skip_bits = src[-1]

    def decrunch(self):
        self.p_in = len(self.data)
        self.p_out = len(self.dest)
        self.written = 0
        self.bit_buffer_size = 0
        self.bit_buffer = 0

        self.read_bits(self.skip_bits)
        while self.written < self.dest_len:
            "1bit==0: literal, then match. 1bit==1: just match"
            if self.read_bits(1) == 0:
                todo = 1
                while True:
                    x = self.read_bits(2)
                    todo += x
                    if x != 3: break
                while todo > 0:
                    todo -= 1
                    x = self.read_bits(8)
                    self.byte_out(x)
                if self.written == self.dest_len:
                    break

            "match: read 2 bits for initial offset bitlength / match length"
            x = self.read_bits(2)
            offbits = self.offset_lens[x]
            todo = x+2
            if x == 3:
                if self.read_bits(1) == 0:
                    offbits = 7
                offset = self.read_bits(offbits)
                while True:
                    x = self.read_bits(3)
                    todo += x
                    if x != 7: break
            else:
                offset = self.read_bits(offbits)

            if (self.p_out + offset) >= self.dest_len:
                raise Exception("PP20: Invalid offset!")
            while todo > 0:
                todo -= 1
                self.byte_out(self.dest[self.p_out + offset])
        return self.dest

    def read_bits(self, nbits):
        while self.bit_buffer_size < nbits:
            if self.p_in < 0: raise Exception("PP20: Unexpected EOF!")
            self.p_in -= 1
            self.bit_buffer |= self.data[self.p_in] << self.bit_buffer_size
            self.bit_buffer_size += 8
        result = 0
        self.bit_buffer_size -= nbits
        while nbits > 0:
            nbits -= 1
            result = (result << 1) | (self.bit_buffer & 1)
            self.bit_buffer >>= 1
        return result

    def byte_out(self, byte):
        if self.p_out <= 0: raise Exception("PP20: Buffer overrun!")
        self.p_out -= 1
        self.dest[self.p_out] = byte
        self.written += 1
