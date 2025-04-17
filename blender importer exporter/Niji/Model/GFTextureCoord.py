import os
import sys
import struct
from . import helperfunctions
from . import Vector2
from . import GFHashName2


class GFTextureCoord(object):         

    def readGFTextureCoord(self,file):
        self.texturename = GFHashName2.GFHashName2(file)
        self.unitindex = int.from_bytes(file.read(1),"little")
        self.mappingtype = int.from_bytes(file.read(1),"little")
        self.scale = Vector2.Vector2(file)
        self.rotation = struct.unpack('f',file.read(4))
        self.translation = Vector2.Vector2(file)
        self.wrapu = int.from_bytes(file.read(4),"little")
        self.wrapv = int.from_bytes(file.read(4),"little")
        self.magfilter = int.from_bytes(file.read(4),"little")
        self.minfilter = int.from_bytes(file.read(4),"little")
        self.minLOD = int.from_bytes(file.read(4),"little")
    def __init__(self,file):
        self.readGFTextureCoord(file)