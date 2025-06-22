import os
import sys
from . import helperfunctions


class GFSection(object): 
    def writenewsection(self,f):
        bytearray1 = bytearray(self.magic, "utf-8")
        bytearray1 = bytearray1[:8]
        bytearray1 += bytearray(8 - len(bytearray1))
        f.write(bytearray1)
        #8 byte ASCII character value
        f.write(self.length.to_bytes(4, 'little'))
        f.write(b'\xFF\xFF\xFF\xFF')

    def readSection(self,file):
        self.magic = file.read(8).decode("utf-8");
        #8 byte ASCII character value
        self.length = int.from_bytes(file.read(4),"little")
        helperfunctions.skippadding1(4,file)
    
    def __init2__(self,sectionstring,length):
        self.magic = sectionstring
        self.length = length
    
    def __init__(self,file):
        self.file = file
        self.magic = "placeholder"
        self.length = 0
        self.readSection(file)
        
        
    