import os
import sys
from . import helperfunctions


class GFHashName(object):   

    def readHashName(self,file,hashcount,hashlist):
        for x in range(0,hashcount):
            temparray = []
            temparray.append(file.read(4))#hash
            temparray.append(file.read(64).decode("utf-8"))#hashname(fixed length)
            hashlist.append(temparray)
        
    
    def __init__(self,file):
        self.file = file
        self.numofhashes = 0
        self.hashes = []
        self.numofhashes = int.from_bytes(file.read(4),"little");
        self.readHashName(file,self.numofhashes,self.hashes)
        
        
 