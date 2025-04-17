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
		
        X = struct.unpack('f',file.read(4))
        Y = struct.unpack('f',file.read(4))
        Z = struct.unpack('f',file.read(4))
        W = struct.unpack('f',file.read(4))
