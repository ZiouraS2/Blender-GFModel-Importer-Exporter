import os
import sys
import struct
from . import helperfunctions
from . import GFNV1


class GFHashName(object):   
    #https://stackoverflow.com/questions/4459703/how-to-make-lists-contain-only-distinct-element-in-python
    def _f(self,seq, idfun=None):  
        seen = set()
        return [x for x in seq if x not in seen and not seen.add(x)]

    def writeHashName(self,f):
        #make list unique so we don't have dups
        f.write((len(self.hashes)).to_bytes(4, byteorder='little'))
        for hashe in self.hashes:
            #bruh i'm actually braindead
            #unilist = list(self._f(hashe[1],None))
 
            fnv = GFNV1.GFNV1()
            print(hashe[1])
            fnv.hashstring(hashe[1])
            print(fnv.hashcode.value)
            print("gfhashnamehash")
            print(fnv.hashcode.value.to_bytes(4, byteorder='little'))
            f.write(fnv.hashcode.value.to_bytes(4, byteorder='little'))
            bytearray1 = bytearray(hashe[1], "utf-8") 
            bytearray1 = bytearray1[:64]
            f.write(bytearray1)

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
         
    def __init2__(self,stringlist):
        self.numofhashes = len(stringlist)
        self.hashes = []
        for string in stringlist:
            fnv = GFNV1.GFNV1()
            fnv.hashstring(string)
            temparray = []
            print(fnv.hashcode.value)
            temparray.append(fnv.hashcode.value)#hash
            bytearray1 = bytearray(string, "utf-8")
            bytearray1 = bytearray1[:64]
            #pad out rest of string
            bytearray1 += bytearray(64 - len(bytearray1))
            temparray.append(bytearray1.decode("utf-8"))#hashname(fixed length)
            self.hashes.append(temparray)
        
        
 