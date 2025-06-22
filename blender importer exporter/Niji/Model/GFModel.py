import os
import sys
import ctypes
import bpy
from . import helperfunctions
from . import GFSection
from . import GFHashName
from . import Vector4
from . import Matrix4x4
from . import GFBone
from . import GFLUT
from . import GFMaterial
from . import GFMesh


class GFModel(object):
        
    def readModel(self,file):
        fileType = file.read(4)
        if(fileType == b'\x17\x21\x12\x15'):
            self.sectionscount = file.read(4)
            helperfunctions.skippadding1(8,file)
            self.modelgfsection = GFSection.GFSection(file) 
            self.shadernames = GFHashName.GFHashName(file)
            self.texturenames = GFHashName.GFHashName(file)
            self.materialnames = GFHashName.GFHashName(file)
            self.meshnames = GFHashName.GFHashName(file)
            self.boundingboxminvector = Vector4.Vector4(file)
            self.boundingboxmaxvector = Vector4.Vector4(file)
            self.transformmatrix = Matrix4x4.Matrix4x4(file)
            
            #we have no idea what this is but it seems to stay consistent throughout files
            unknowndatalength = int.from_bytes(file.read(4),"little")
            unknowndataoffset = int.from_bytes(file.read(4),"little")
            helperfunctions.skippadding1(unknowndataoffset+unknowndatalength+8,file)
       
            self.bonescount = int.from_bytes(file.read(4),"little")
            helperfunctions.skippadding1(12,file)
            self.GFBones = []
            
            for i in range(self.bonescount):
                tempGFBone = GFBone.GFBone(file)
                self.GFBones.append(tempGFBone)
                
            helperfunctions.skippadding3(file)
            
            self.lutsCount = int.from_bytes(file.read(4),"little")
            self.lutslength = int.from_bytes(file.read(4),"little")
            helperfunctions.skippadding(file)
            
            
            
            self.GFLUTS = []
            for i in range(self.lutsCount):
                tempGFLUT = GFLUT.GFLUT(file,self.lutslength)
                self.GFLUTS.append(tempGFLUT)
            
            self.GFMaterials = []
    
            for i in range(self.materialnames.numofhashes):
                tempGFmaterial = GFMaterial.GFMaterial(file)
                self.GFMaterials.append(tempGFmaterial)
                
            self.GFMeshes = []    
            for i in range(self.meshnames.numofhashes):
                tempGFmesh = GFMesh.GFMesh(file)
                self.GFMeshes.append(tempGFmesh)

            
            
        else:
            print("incorrect file header found")  
     
    def __init__(self,file,name):
        self.file = file
        self.name = name
        self.readModel(file)
       
        
        
    def writeModel(self,f,collection):  
        f.write(b'\x17\x21\x12\x15')
        f.write((len(self.GFMaterials)+len(self.GFMeshes)+1).to_bytes(4, byteorder='little'))
        #padding
        f.write(bytes(8))
        #placeholder(will write gfsection here after we know the length of the bones section (possec1start - possec1end))
        f.write(bytes(16))
        possec1start = f.tell()
        print(possec1start)
        
        #hashnames section
        self.shadernames.writeHashName(f)
        
        self.texturenames.writeHashName(f)
         
        self.materialnames.writeHashName(f)
         
        self.meshnames.writeHashName(f)
            
        #
        self.boundingboxminvector.writeVec4(f)
        self.boundingboxmaxvector.writeVec4(f)
        self.transformmatrix.writeMatrix4x4(f)
        #constant section?
        f.write(b'\x00\x00\x00\x00')
        f.write(b'\x10\x00\x00\x00')
        f.write(b'\x00\x00\x00\x00')
        f.write(b'\x00\x00\x00\x00')
        f.write(b'\x00\x00\x00\x00')
        f.write(b'\x00\x00\x00\x00')
        f.write(b'\x00\x00\x00\x00')
        f.write(b'\x00\x00\x00\x00')
        
        #gfbones section
        print("gfbones count")
        print(len(self.GFBones))
        f.write(self.bonescount.to_bytes(4, 'little'))
        f.write(bytes(12))
        for i in range(self.bonescount):
            self.GFBones[i].writebone(f)
 
 
        helperfunctions.skippadding3(f)
        
        #gfluts
        f.write(self.lutsCount.to_bytes(4, 'little'))
        f.write(self.lutslength.to_bytes(4, 'little'))
        helperfunctions.skippadding3(f)
        for i in range(self.lutsCount):
            self.GFLUTS[i].writelut(f)
        
        #where the gfsection ends
        possec1end = f.tell()
        print(possec1end)
        f.seek(possec1start - 16)
        #write gfsection
        
        print(GFSection.GFSection)
        newGFSection = GFSection.GFSection.__new__(GFSection.GFSection)
        newGFSection.__init2__("gfmodel",(possec1end - possec1start))
        newGFSection.writenewsection(f)
        f.seek(possec1end)    
        for i in range(self.materialnames.numofhashes):
            print()
            self.GFMaterials[i].writematerial(f)
        
        for i in range(self.meshnames.numofhashes):
            print()
            self.GFMeshes[i].writeMesh(f)