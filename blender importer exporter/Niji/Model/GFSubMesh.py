import os
import sys
import io
import struct
from . import helperfunctions
from . import PicaCommandReader
from . import PicaFixedAttribute
from . import GFNV1

#formatted weirdly because the data for each submesh is split up into two sections
class GFSubMeshPart1(object): 
    def __init__(self,file,submeshescount):
            self.SMNameHash = file.read(4)
            self.stringlength = int.from_bytes(file.read(4),"little")
            self.submeshname = file.read(self.stringlength).decode("utf-8")
            self.boneindicescount = int.from_bytes(file.read(1),"little")
            self.boneindices = []
            #bone indices count but 31 fixed length anyway???? lol? nvm the count is actually set to the number of indexes actually used, not the length of the buffer
            for x in range(31):
                self.boneindices.append(int.from_bytes(file.read(1),"little"))
            self.verticescount = int.from_bytes(file.read(4),"little")
            self.indicescount = int.from_bytes(file.read(4),"little")
            self.verticeslength = int.from_bytes(file.read(4),"little")
            self.indiceslength = int.from_bytes(file.read(4),"little")
    def __init2__(self,submeshescount,submeshname): 
            fnv = GFNV1.GFNV1()
            fnv.hashstring(submeshname)
            self.SMNameHash = struct.pack('I',fnv.hashcode.value)
            self.stringlength = len(submeshname)
            self.submeshname = submeshname
            self.boneindicescount = 0
            self.boneindices = []
            self.verticescount = 0
            self.indicescount = 0
            self.verticeslength = 0
            self.indiceslength = 0
            
    def writeGFSubMeshPart1(self,f,submeshescount):
            f.write(self.SMNameHash)
            f.write(self.stringlength.to_bytes(4, 'little'))
            f.write(self.submeshname.encode("utf-8"))
            f.write(self.boneindicescount.to_bytes(1, 'little'))
            print(self.boneindices)
            for x in range(31):
                print(x)
                f.write(self.boneindices[x].to_bytes(1, 'little'))
            f.write(self.verticescount.to_bytes(4, 'little'))
            f.write(self.indicescount.to_bytes(4, 'little'))
            f.write(self.verticeslength.to_bytes(4, 'little'))
            f.write((self.indiceslength).to_bytes(4, 'little'))
            
class GFSubMeshPart2(object): 
    def __init__(self,file,i,GFSubMeshesPart1):
            # storing in ram so we don't ever accidentally write over the original model data
            self.rawbuffer = io.BytesIO(file.read(GFSubMeshesPart1[i].verticeslength))
            self.indices = io.BytesIO(file.read(GFSubMeshesPart1[i].indiceslength))
    def __init2__(self):
        self.rawbuffer = io.BytesIO()
        self.indices = io.BytesIO()
    def writeGFSubMeshPart2(self,f,subsmeshescount):
        f.write(self.rawbuffer.getvalue())
        f.write(self.indices.getvalue())    

class GFSubMeshParts(object):  
    def __init__(self,file,submeshescount):
        self.GFSubMeshesPart1 = []
        for x in range(submeshescount):
            tempGFSubMeshPart1 = GFSubMeshPart1(file,submeshescount)
            self.GFSubMeshesPart1.append(tempGFSubMeshPart1)
            
        count = 0
        self.GFSubMeshesPart2 = []
        for x in range(submeshescount):
            tempGFSubMeshPart2 = GFSubMeshPart2(file,count,self.GFSubMeshesPart1)
            self.GFSubMeshesPart2.append(tempGFSubMeshPart2)
            count = count + 1
        #there's still still a buffer between sections even if indices end inline with the 16th address
        if((file.tell() & 0xF) == 0):
            helperfunctions.skippadding1(16,file)
        else:
            helperfunctions.skippadding3(file)
            
    def __init2__(self,submeshescount,submeshnames):
        self.GFSubMeshesPart1 = []
        for x in range(submeshescount):
            tempGFSubMeshPart1 = GFSubMeshPart1.__new__(GFSubMeshPart1)
            tempGFSubMeshPart1.__init2__(submeshescount,submeshnames[0])
            self.GFSubMeshesPart1.append(tempGFSubMeshPart1)       
        count = 0
        self.GFSubMeshesPart2 = []
        for x in range(submeshescount):
            tempGFSubMeshPart2 = GFSubMeshPart2.__new__(GFSubMeshPart2)
            tempGFSubMeshPart2.__init2__()
            self.GFSubMeshesPart2.append(tempGFSubMeshPart2)
            count = count + 1
            
    def writeSubMeshParts(self, f, submeshescount):
        for x in range(submeshescount):
            self.GFSubMeshesPart1[x].writeGFSubMeshPart1(f,submeshescount)
          
        count = 0  
        for x in range(submeshescount):
            self.GFSubMeshesPart2[x].writeGFSubMeshPart2(f,submeshescount)
            count = count + 1
        #there's still still a buffer between sections even if indices end inline with the 16th address
        if((f.tell() & 0xF) == 0):
            helperfunctions.skippadding1(16,f)
            
        else:
            helperfunctions.skippadding3(f)
class GFSubMesh(object):        
    
    def __init__(self,submeshparts,i):
            self.gfsubmeshpart1 = submeshparts.GFSubMeshesPart1[i]
            self.gfsubmeshpart2 = submeshparts.GFSubMeshesPart2[i]
            self.vertexstride = 0
            self.attributes = []
            self.fixedattributes = []
            
    def __init2__(self,submeshparts,i):        
            self.gfsubmeshpart1 = submeshparts.GFSubMeshesPart1[i]
            self.gfsubmeshpart2 = submeshparts.GFSubMeshesPart2[i]
            self.vertexstride = 0
            self.attributes = []
            self.fixedattributes = []
            
class GFSubMeshes(object):  
    def __init__(self,file,submeshescount):
        self.submeshparts = GFSubMeshParts(file,submeshescount)
        self.submeshescount = submeshescount
        self.GFSubMeshes = []
        count = 0
        for x in range(submeshescount):
            tempGFSubMesh = GFSubMesh(self.submeshparts,count)
            self.GFSubMeshes.append(tempGFSubMesh)
            count = count + 1
    def __init2__(self,submeshescount,submeshnames):  
        self.submeshparts = GFSubMeshParts.__new__(GFSubMeshParts)
        self.submeshparts.__init2__(submeshescount,submeshnames)
        self.submeshescount = submeshescount
        self.GFSubMeshes = []
        for x in range(submeshescount):
            tempGFSubMesh = GFSubMesh(self.submeshparts,x)
            self.GFSubMeshes.append(tempGFSubMesh)
        
            
    def writeSubMeshes(self,f):
        self.submeshparts.writeSubMeshParts(f,self.submeshescount)
        
