import os
import sys
import struct
from . import helperfunctions


class GFBone(object):   

    def readGFBone(self,file):
            stringlength = int.from_bytes(file.read(1),"little")
            self.bonename = (file.read(stringlength).decode("utf-8"))
            maybestringlength = int.from_bytes(file.read(1),"little")
            if(maybestringlength == 0):
                pass
            else:
                self.boneparentname = (file.read(maybestringlength).decode("utf-8"))
            
            self.boneflag = file.read(1)
            self.ScaleX = struct.unpack('f',file.read(4))
            self.ScaleY = struct.unpack('f',file.read(4))
            self.ScaleZ = struct.unpack('f',file.read(4))
            self.RotationX = struct.unpack('f',file.read(4))
            self.RotationY = struct.unpack('f',file.read(4))
            self.RotationZ = struct.unpack('f',file.read(4))
            self.TranslationX = struct.unpack('f',file.read(4))
            self.TranslationY = struct.unpack('f',file.read(4))
            self.TranslationZ = struct.unpack('f',file.read(4))
            
        

    
    def __init__(self,file):
            self.file = file
            self.bonename = "placeholder"
            self.boneparentname = "placeholder"
            self.boneflags = 0
            self.ScaleX = 0.0
            self.ScaleY = 0.0
            self.ScaleZ = 0.0
            self.RotationX = 0.0
            self.RotationY = 0.0
            self.RotationZ = 0.0
            self.TranslationX = 0.0
            self.TranslationY = 0.0
            self.TranslationZ = 0.0
            self.readGFBone(file)