import os
import sys
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
            
    def __init__(self,file):
        self.file = file
        self.readModel(file)
            
            
    