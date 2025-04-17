import os
import sys
from . import helperfunctions


class GFSection(object):   

    def readSection(self,file):
        self.magic = file.read(8).decode("utf-8");
        #8 byte ASCII character value
        self.length = int.from_bytes(file.read(4),"little")
        helperfunctions.skippadding1(4,file)
    
    def __init__(self,file):
        self.file = file
        self.magic = "placeholder"
        self.length = 0
        self.readSection(file)