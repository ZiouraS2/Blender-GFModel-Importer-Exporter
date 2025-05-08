import os
import sys
import struct
from . import helperfunctions
from . import Vector2
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
    def __init__(self,file):
        self.readGFTextureCoord(file)