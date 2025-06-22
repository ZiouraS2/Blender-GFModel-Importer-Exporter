import os
import sys
import struct
from . import helperfunctions


class Vector4(object):         
  
    def __init__(self,file):
        self.file = file
        self.X = 0
        self.Y = 0
        self.Z = 0
        self.W = 0
		
        self.X = struct.unpack('f',file.read(4))
        self.Y = struct.unpack('f',file.read(4))
        self.Z = struct.unpack('f',file.read(4))
        self.W = struct.unpack('f',file.read(4))
    def writeVec4(self,f):
        f.write(struct.pack('f',self.X[0]))
        f.write(struct.pack('f',self.Y[0]))
        f.write(struct.pack('f',self.Z[0]))
        f.write(struct.pack('f',self.W[0]))