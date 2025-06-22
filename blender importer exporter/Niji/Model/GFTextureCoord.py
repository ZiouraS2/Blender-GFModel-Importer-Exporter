import os
import sys
import struct
import math
from . import helperfunctions
from . import Vector2
from . import Matrix4x4
from . import GFHashName2
from . import GFTextureWrap
from . import GFMagFilter
from . import GFMinFilter
from . import GFTextureMappingType

class GFTextureCoord(object):         

    def readGFTextureCoord(self,file):
        self.texturename = GFHashName2.GFHashName2(file)
        self.unitindex = int.from_bytes(file.read(1),"little")
        self.mappingtype = GFTextureMappingType.GFTextureMappingType(int.from_bytes(file.read(1),"little"))
        self.scale = Vector2.Vector2(file)
        print("textue coord reads")
        print(self.texturename.hashes[0][1])
        print(self.scale.X)
        print(self.scale.Y)
        self.rotation = struct.unpack('f',file.read(4))
        self.translation = Vector2.Vector2(file)
        self.wrapu = GFTextureWrap.GFTextureWrap(int.from_bytes(file.read(4),"little"))
        self.wrapv = GFTextureWrap.GFTextureWrap(int.from_bytes(file.read(4),"little"))
        self.magfilter = GFMagFilter.GFMagFilter(int.from_bytes(file.read(4),"little"))
        self.minfilter = GFMinFilter.GFMinFilter(int.from_bytes(file.read(4),"little"))
        self.minLOD = int.from_bytes(file.read(4),"little") #not sure
        
    def writeGFTextureCoord(self, f):
        self.texturename.writeHashName(f)
        f.write(self.unitindex.to_bytes(1, 'little'))
        f.write(self.mappingtype.value.to_bytes(1, 'little'))
        self.scale.writeVec2(f)
        f.write(struct.pack('f',self.rotation))
        self.translation.writeVec2(f)
        f.write(self.wrapu.value.to_bytes(4, 'little'))
        f.write(self.wrapv.value.to_bytes(4, 'little'))
        f.write(self.magfilter.value.to_bytes(4, 'little'))
        f.write(self.minfilter.value.to_bytes(4, 'little'))
        f.write(self.minLOD.to_bytes(4, 'little'))
        
    def __init__(self,file):
        self.readGFTextureCoord(file)
        
    #only one which won't have params    
    def __init2__(self,file):
        texnameplaceholder = GFHashName2.__new__(GFHashName2)
        texnameplaceholder.__init2__("placeholder")
        self.texturename = texnameplaceholder
        self.unitindex = 0
        self.mappingtype = GFTextureMappingType.GFTextureMappingType(0)
        vec2placeholder = Vector2.__new__(Vector2)
        vec2placeholder.__init2__(0,0)
        self.scale = vec2placeholder
        print("textue coord reads")
        print(self.texturename.hashes[0][1])
        print(self.scale.X)
        print(self.scale.Y)
        self.rotation = float(0)
        self.translation = vec2placeholder
        self.wrapu = GFTextureWrap.GFTextureWrap(0)
        self.wrapv = GFTextureWrap.GFTextureWrap(0)
        self.magfilter = GFMagFilter.GFMagFilter(0)
        self.minfilter = GFMinFilter.GFMinFilter(0)
        self.minLOD = 0
        
    def gettransform(self):
        placeholdermatrix = Matrix4x4.__new__(Matrix4x4)
        placeholdermatrix.__init2__(1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0)
        scale,rotation,translation,0
        sx = self.scale.X
        sy = self.scale.Y
        
        tx = self.translation.X
        ty = self.translation.Y
        
        ca = float(math.cos(self.rotation))
        sa = float(math.Sin(self.rotation))
        
        placeholdermatrix.a11 = sx*ca
        placeholdermatrix.a12 = sy*sa
        placeholdermatrix.a21 = sx*(-1*sa)
        placeholdermatrix.a22 = sy*ca
        placeholdermatrix.a41 = ((0.5*sa - 0.5*ca)+0.5 - tx)
        placeholdermatrix.a42 = ((0.5*(-1*sa) - 0.5*ca)+0.5 - ty)
        
        return placeholdermatrix