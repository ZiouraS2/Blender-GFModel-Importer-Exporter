import os
import sys
import struct
from . import helperfunctions


class Vector2(object):         
  
    def __init__(self,file):
        self.X = 0
        self.Y = 0
		
        self.X = struct.unpack('f',file.read(4))[0]
        self.Y = struct.unpack('f',file.read(4))[0]