import os
import sys
import io
from . import helperfunctions
from . import PicaCommandReader
from . import PicaFixedAttribute

#formatted weirdly because the data for each submesh is split up into two sections
class GFSubMeshPart1(object): 
    def __init__(self,file,submeshescount):
            self.SMNameHash = file.read(4)
            self.stringlength = int.from_bytes(file.read(4),"little")
            self.submeshname = file.read(self.stringlength).decode("utf-8")
            self.boneindicescount = int.from_bytes(file.read(1),"little")
            self.boneindices = []
            #bone indices count but 31 fixed length anyway???? lol?
            for x in range(31):
                self.boneindices.append(int.from_bytes(file.read(1),"little"))
            self.verticescount = int.from_bytes(file.read(4),"little")
            self.indicescount = int.from_bytes(file.read(4),"little")
            self.verticeslength = int.from_bytes(file.read(4),"little")
            self.indiceslength = int.from_bytes(file.read(4),"little")
            
class GFSubMeshPart2(object): 
    def __init__(self,file,i,GFSubMeshesPart1):
            # storing in ram so we don't ever accidentally write over the original model data
            self.rawbuffer = io.BytesIO(file.read(GFSubMeshesPart1[i].verticeslength))
            self.indices = io.BytesIO(file.read(GFSubMeshesPart1[i].indiceslength))
            

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
class GFSubMesh(object):        
    
    def __init__(self,submeshparts,i):
            self.gfsubmeshpart1 = submeshparts.GFSubMeshesPart1[i]
            self.gfsubmeshpart2 = submeshparts.GFSubMeshesPart2[i]
            self.vertexstride = 0
            self.attributes = []
            self.fixedattributes = []
            
class GFSubMeshes(object):  
    def __init__(self,file,submeshescount):
        self.submeshparts = GFSubMeshParts(file,submeshescount)
        self.GFSubMeshes = []
        count = 0
        for x in range(submeshescount):
            tempGFSubMesh = GFSubMesh(self.submeshparts,count)
            self.GFSubMeshes.append(tempGFSubMesh)
            count = count + 1
        
