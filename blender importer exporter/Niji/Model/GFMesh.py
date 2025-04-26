import os
import sys
import struct
import numpy as np
from . import helperfunctions
from . import GFSection
from . import GFHashName
from . import GFTextureCoord
from . import GFHashName2
from . import RGBA
from . import Vector4
from . import GFMeshCommands
from . import GFSubMesh
from . import PicaRegisters
from . import PicaCommandReader
from . import PicaFloatVector24
from . import PicaAttributeName
from . import PicaFixedAttribute
from . import PicaAttribute
from . import PicaAttributeFormat



class GFMesh(object):         

        
    def __init__(self,file):
        self.meshgfsection = GFSection.GFSection(file)
        self.namehash = file.read(4)
        print(file.tell())
        self.namestr = file.read(64).decode("utf-8")
        print(self.namestr)
        helperfunctions.skippadding1(4,file)
        self.boundingboxminvector = Vector4.Vector4(file)
        self.boundingboxmaxvector = Vector4.Vector4(file)
        self.submeshescount = int.from_bytes(file.read(4),"little")
        self.boneindicespervertex = int.from_bytes(file.read(4),"little")
        helperfunctions.skippadding1(16,file)
        
        helperfunctions.skippadding1(8,file)
        self.commandscount = int.from_bytes(file.read(4),"little")
        helperfunctions.skippadding1(-12,file)
        
        self.GFMeshCommandses = []
        for x in range(self.commandscount):    
            tempGFMeshCommand = GFMeshCommands.GFMeshCommands(file)
            self.GFMeshCommandses.append(tempGFMeshCommand)
            
        #no looping here because it makes it easier to digest
        self.GFSubMeshes = GFSubMesh.GFSubMeshes(file,self.submeshescount)
    
    def getfixedattributes(self,submesh):
        scales = np.array([0.007874016,0.003921569,3.051851E-05,1])
        fixedattributetable = []
        
        bufferformats = 0
        bufferattributes = 0
        bufferpermutation = 0
        attributescount = 0
        attributestotal = 0
        fixedindex = 0
        fixed = []
        for x in range(12):
            tempVec = PicaFloatVector24.PicaVectorFloat24()
            fixed.append(tempVec)
        
        enablecommands = self.GFMeshCommandses[0].commands
    
        picacommands = PicaCommandReader.PicaCommandReader(enablecommands)
        
        #get parameters we need from commands
        i = 0
        for x in range(len(picacommands.commands)):
            currcommand = picacommands.commands[i]
            if(currcommand.register.name == "GPUREG_ATTRIBBUFFERS_FORMAT_LOW"):
                bufferformats |= currcommand.parameters[0] << 0
            if(currcommand.register.name == "GPUREG_ATTRIBBUFFERS_FORMAT_HIGH"):
                bufferformats |= currcommand.parameters[0] << 32
            if(currcommand.register.name == "GPUREG_ATTRIBBUFFER0_CONFIG1"):
                bufferattributes |= currcommand.parameters[0]
            if(currcommand.register.name == "GPUREG_ATTRIBBUFFER0_CONFIG2"):
                bufferattributes |= (currcommand.parameters[0] & 0xffff) << 32
                submesh.vertexstride = ((currcommand.parameters[0] >> 16)&0xff)#we only want the last byte for some reason
                print(submesh.vertexstride)
                attributescount = (currcommand.parameters[0] >> 28)
            if(currcommand.register.name == "GPUREG_FIXEDATTRIB_INDEX"):
                fixedindex = currcommand.parameters[0]
            if(currcommand.register.name == "GPUREG_FIXEDATTRIB_DATA0"):
                fixed[fixedindex].setword0(currcommand.parameters[0])
            if(currcommand.register.name == "GPUREG_FIXEDATTRIB_DATA1"):
                fixed[fixedindex].setword1(currcommand.parameters[0])
            if(currcommand.register.name == "GPUREG_FIXEDATTRIB_DATA2"):
                fixed[fixedindex].setword2(currcommand.parameters[0])
            if(currcommand.register.name == "GPUREG_VSH_NUM_ATTR"):
                attributestotal = currcommand.parameters[0] + 1
            if(currcommand.register.name == "GPUREG_VSH_ATTRIBUTES_PERMUTATION_LOW"):
                bufferpermutation |= currcommand.parameters[0] << 0
            if(currcommand.register.name == "GPUREG_VSH_ATTRIBUTES_PERMUTATION_HIGH"):
                bufferpermutation |= (currcommand.parameters[0] << 32)
                
        
            i += 1
        i2 = 0
        for x in range(attributestotal):
            #fixed attributes
            print("attributes")
            print(i2)
            print(((bufferformats >> (48+i2)) & 1))
            if(((bufferformats >> (48+i2)) & 1) != 0):
                scale = 1
                name = PicaAttributeName.PicaAttributeName((bufferpermutation >>(i2*4))&0xf).name
                picaname =  PicaAttributeName.PicaAttributeName((bufferpermutation >>(i2*4))&0xf)
                if(name == "Color"):
                    scale = 3
                if(name == "BoneWeight"):
                    scale = 0.007874016          
                fixed[i2].mul(scale)
                print("fixed")
                print(fixed[i2])
                submesh.fixedattributes.append(PicaFixedAttribute.PicaFixedAttribute(picaname,fixed[i2]))
            #attributes
            else:
                permutationidx = ((bufferattributes >> i2*4) & 0xf)
                attributename = ((bufferpermutation >> permutationidx*4) & 0xf)
                attributefmt = ((bufferformats >> permutationidx*4) & 0xf)
                attrib = PicaAttribute.PicaAttribute(PicaAttributeName.PicaAttributeName(attributename),PicaAttributeFormat.PicaAttributeFormat(attributefmt&3),(attributefmt >> 2)+1,scales[attributefmt & 3])
                if(attrib.name == "BoneIndex"):
                    attrib.scale = 1
                    
                submesh.attributes.append(attrib)
            i2 += 1
            
                
                
        #skipping index commands for now until something breaks
    def getfixedattributestest(self):
        self.getfixedattributes(self.GFSubMeshes.GFSubMeshes[0])
                
