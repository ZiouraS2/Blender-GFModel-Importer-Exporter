import os
import sys
from . import helperfunctions


class GFHashName2(object):   

    def readHashName(self,file,hashlist):
        temparray = []
        temparray.append(file.read(4))#hash
        namelength = int.from_bytes(file.read(1),"little")
        temparray.append(file.read(namelength).decode("utf-8"))#hashname(non-fixed length)
        hashlist.append(temparray)
        
    
    def __init__(self,file):
        self.file = file
        self.hashes = []
        self.readHashName(file,self.hashes)