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
	
		
            self.a11 = struct.unpack('f',file.read(4))
            self.a12 = struct.unpack('f',file.read(4))
            self.a13 = struct.unpack('f',file.read(4))
            self.a14 = struct.unpack('f',file.read(4))
            self.a21 = struct.unpack('f',file.read(4))
            self.a22 = struct.unpack('f',file.read(4))
            self.a23 = struct.unpack('f',file.read(4))
            self.a24 = struct.unpack('f',file.read(4))
            self.a31 = struct.unpack('f',file.read(4))
            self.a32 = struct.unpack('f',file.read(4))
            self.a33 = struct.unpack('f',file.read(4))
            self.a34 = struct.unpack('f',file.read(4))
            self.a41 = struct.unpack('f',file.read(4))
            self.a42 = struct.unpack('f',file.read(4))
            self.a43 = struct.unpack('f',file.read(4))
            self.a44 = struct.unpack('f',file.read(4))		
    def __init2__(self,a11,a12,a13,a14,a21,a22,a23,a24,a31,a32,a33,a34,a41,a42,a43,a44):
            self.a11 = a11
            self.a12 = a12
            self.a13 = a13
            self.a14 = a14
		
            self.a21 = a21
            self.a22 = a22
            self.a23 = a23
            self.a24 = a24
		
            self.a31 = a31
            self.a32 = a32
            self.a33 = a33
            self.a34 = a34
		
            self.a41 = a41
            self.a42 = a42 
            self.a43 = a43
            self.a44 = a44
            
    def writeMatrix4x4(self,f):
            f.write(struct.pack('f',self.a11[0]))
            f.write(struct.pack('f',self.a12[0]))
            f.write(struct.pack('f',self.a13[0]))
            f.write(struct.pack('f',self.a14[0]))
            f.write(struct.pack('f',self.a21[0]))
            f.write(struct.pack('f',self.a22[0]))
            f.write(struct.pack('f',self.a23[0]))
            f.write(struct.pack('f',self.a24[0]))
            f.write(struct.pack('f',self.a31[0]))
            f.write(struct.pack('f',self.a32[0]))
            f.write(struct.pack('f',self.a33[0]))
            f.write(struct.pack('f',self.a34[0]))
            f.write(struct.pack('f',self.a41[0]))
            f.write(struct.pack('f',self.a42[0]))
            f.write(struct.pack('f',self.a43[0]))
            f.write(struct.pack('f',self.a44[0]))

            