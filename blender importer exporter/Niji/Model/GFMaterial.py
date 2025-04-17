import os
import sys
import struct
from . import helperfunctions
from . import GFSection
from . import GFHashName
from . import GFTextureCoord
from . import GFHashName2
from . import RGBA


class GFMaterial(object):         

        
    def __init__(self,file):
        self.materialgfsection = GFSection.GFSection(file)
        self.materialname = GFHashName2.GFHashName2(file)
        self.shadername = GFHashName2.GFHashName2(file)
        self.fragshadername = GFHashName2.GFHashName2(file)
        self.vtxshadername = GFHashName2.GFHashName2(file)
        self.luthash0id = int.from_bytes(file.read(4),"little")
        self.luthash1id = int.from_bytes(file.read(4),"little")
        self.luthash2id = int.from_bytes(file.read(4),"little")
        helperfunctions.skippadding1(4,file)
        self.bumptexture = int.from_bytes(file.read(1),"little")
        self.constant0assignment = int.from_bytes(file.read(1),"little")
        self.constant1assignment = int.from_bytes(file.read(1),"little")
        self.constant2assignment = int.from_bytes(file.read(1),"little")
        self.constant3assignment = int.from_bytes(file.read(1),"little")
        self.constant4assignment = int.from_bytes(file.read(1),"little")
        self.constant5assignment = int.from_bytes(file.read(1),"little")
        helperfunctions.skippadding1(1,file)
        self.constant0color = RGBA.RGBA(file)
        self.constant1color = RGBA.RGBA(file)
        self.constant2color = RGBA.RGBA(file)
        self.constant3color = RGBA.RGBA(file)
        self.constant4color = RGBA.RGBA(file)
        self.constant5color = RGBA.RGBA(file)
        self.specular0color = RGBA.RGBA(file)
        self.specular1color = RGBA.RGBA(file)
        self.blendcolor = RGBA.RGBA(file)
        self.emissioncolor = RGBA.RGBA(file)
        self.ambientcolor = RGBA.RGBA(file)
        self.diffusecolor = RGBA.RGBA(file)
        self.edgetype = int.from_bytes(file.read(4),"little")
        self.idedgeenable = int.from_bytes(file.read(4),"little")
        self.edgeid = int.from_bytes(file.read(4),"little")
        self.projectiontype = int.from_bytes(file.read(4),"little")
        self.rimpower = struct.unpack('f',file.read(4))
        self.rimscale = struct.unpack('f',file.read(4))
        self.phongpower = struct.unpack('f',file.read(4))
        self.phongscale = struct.unpack('f',file.read(4))
        self.idedgeoffsetenable = int.from_bytes(file.read(4),"little")
        self.edgemapalphamask = int.from_bytes(file.read(4),"little")
        self.baketexture0 = int.from_bytes(file.read(4),"little")

        self.baketexture1 = int.from_bytes(file.read(4),"little")
        self.baketexture2 = int.from_bytes(file.read(4),"little")
        self.bakeconstant0 = int.from_bytes(file.read(4),"little")
        self.bakeconstant1 = int.from_bytes(file.read(4),"little")
        self.bakeconstant2 = int.from_bytes(file.read(4),"little")
        self.bakeconstant3 = int.from_bytes(file.read(4),"little")
        self.bakeconstant4 = int.from_bytes(file.read(4),"little")
        self.bakeconstant5 = int.from_bytes(file.read(4),"little")
        self.vertexshadertype = int.from_bytes(file.read(4),"little")
        self.shaderparam0 = struct.unpack('f',file.read(4))
        self.shaderparam1 = struct.unpack('f',file.read(4))
        self.shaderparam2 = struct.unpack('f',file.read(4))
        self.shaderparam3 = struct.unpack('f',file.read(4))
        self.unitscount = int.from_bytes(file.read(4),"little")
        coords = []
        for x in range(self.unitscount):
            tempGFTexCoord = GFTextureCoord.GFTextureCoord(file)
            coords.append(tempGFTexCoord)
        helperfunctions.skippadding3(file)
        self.commandslength = int.from_bytes(file.read(4),"little")
        self.renderpriority = int.from_bytes(file.read(4),"little")
        self.materialhash = int.from_bytes(file.read(4),"little")
        self.renderlayer = int.from_bytes(file.read(4),"little")
        self.reflectionr = RGBA.RGBA(file)
        self.reflectiong = RGBA.RGBA(file)
        self.reflectionb = RGBA.RGBA(file)
        self.reflectionidk = int.from_bytes(file.read(4),"little")
        self.picacommands = []
        for x in range(self.commandslength >> 2):
            self.picacommands.append(file.read(4))
        helperfunctions.skippadding1(16,file)