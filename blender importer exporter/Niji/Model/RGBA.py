import os
import sys
import struct
from . import helperfunctions
from . import GFSection
from . import GFHashName


class RGBA(object):         

    def readRGBA(self,file):
        self.a = int.from_bytes(file.read(1),"little")
        self.b = int.from_bytes(file.read(1),"little")
        self.g = int.from_bytes(file.read(1),"little")
        self.r = int.from_bytes(file.read(1),"little")
    def writeRGBA(self,f):
        f.write(self.a.to_bytes(1, 'little'))
        f.write(self.b.to_bytes(1, 'little'))
        f.write(self.g.to_bytes(1, 'little'))
        f.write(self.r.to_bytes(1, 'little'))
    def __init__(self,file):
            self.r = 0
            self.g = 0	
            self.b = 0
            self.a = 0
            self.readRGBA(file)
    def __init2__(self,r,g,b,a):
            self.r = r
            self.g = g	
            self.b = b
            self.a = a      