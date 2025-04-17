import os
import sys
import struct
from . import helperfunctions


class Matrix4x4(object):         
  
    def __init__(self,file):
            self.file = file
            self.a11 = 0
            self.a12 = 0
            self.a13 = 0
            self.a14 = 0
		
            self.a21 = 0
            self.a22 = 0
            self.a23 = 0
            self.a24 = 0
		
            self.a31 = 0
            self.a32 = 0
            self.a33 = 0
            self.a34 = 0
		
            self.a41 = 0
            self.a42 = 0
            self.a43 = 0
            self.a44 = 0
	
		
            a11 = struct.unpack('f',file.read(4))
            a12 = struct.unpack('f',file.read(4))
            a13 = struct.unpack('f',file.read(4))
            a14 = struct.unpack('f',file.read(4))
            a21 = struct.unpack('f',file.read(4))
            a22 = struct.unpack('f',file.read(4))
            a23 = struct.unpack('f',file.read(4))
            a24 = struct.unpack('f',file.read(4))
            a31 = struct.unpack('f',file.read(4))
            a32 = struct.unpack('f',file.read(4))
            a33 = struct.unpack('f',file.read(4))
            a34 = struct.unpack('f',file.read(4))
            a41 = struct.unpack('f',file.read(4))
            a42 = struct.unpack('f',file.read(4))
            a43 = struct.unpack('f',file.read(4))
            a44 = struct.unpack('f',file.read(4))		