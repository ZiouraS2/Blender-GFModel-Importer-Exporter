import os
import sys
import struct
from . import helperfunctions


class GFLUT(object):         

    def readGFLUT(self,file,lutslength):
        self.hashid = file.read(4)
        helperfunctions.skippadding1(12,file)
        for x in range(lutslength >> 2):
            self.picacommands.append(file.read(4))
    def __init__(self,file,lutslength):
        self.hashid = 0
        self.picacommands = []
        self.lutslength = lutslength
        self.readGFLUT(file,lutslength)
    def writelut(self, f):
        f.write(self.hashid)
        helperfunctions.skippadding1(12,f)
        for x in range(self.lutslength >> 2):
            f.write(self.picacommands[x])