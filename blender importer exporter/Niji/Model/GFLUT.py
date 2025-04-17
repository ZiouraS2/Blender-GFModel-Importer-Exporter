import os
import sys
import struct
from . import helperfunctions


class GFLUT(object):         

    def readGFBone(self,file,lutslength):
        self.hashid = file.read(4)
        helperfunctions.skippadding1(12,file)
        for x in range(lutslength >> 2):
            self.picacommands.append(file.read(4))
    def __init__(self,file,lutslength):
        self.hashid = 0
        self.picacommands = []
        self.readGFBone(file,lutslength)