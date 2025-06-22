import os
import sys
from . import helperfunctions
from . import GFNV1

class GFHashName2(object):   
    #https://stackoverflow.com/questions/4459703/how-to-make-lists-contain-only-distinct-element-in-python
    def _f(seq, idfun=None):  
        ''' Originally proposed by Andrew Dalke '''
        seen = set()
        if idfun is None:
            for x in seq:
                if x not in seen:
                    seen.add(x)
                    yield x
        else:
            for x in seq:
                x = idfun(x)
                if x not in seen:
                    seen.add(x)
                    yield x
                    
    def writeHashName(self, f):
        #make list unique so we don't have dups
        for hashe in self.hashes:
            #unilist = list(self._f(hashe[1],None))
            fnv = GFNV1.GFNV1()
            fnv.hashstring(hashe[1])
            print(fnv.hashcode.value)
            print("gfhashname2hash")
            f.write(fnv.hashcode.value.to_bytes(4, 'little'))
            f.write(len(hashe[1]).to_bytes(1, 'little'))
            f.write(hashe[1].encode("utf-8"))
        
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
        
    def __init2__(self,string):
        self.hashes = []
        
        fnv = GFNV1.GFNV1()
        fnv.hashstring(string)
        temparray = []
        print(fnv.hashcode.value)
        temparray.append(fnv.hashcode.value)#hash

        temparray.append(string)#hashname(fixed length)
        self.hashes.append(temparray)