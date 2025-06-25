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
    def __init2__(self):
        print("so cool")
        
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
        
    def writeMesh(self, f):
        # placeholder(will write gfsection here after we know the length of the material section (possec1start - possec1end))
        f.write(bytes(16))
        possec1start = f.tell()
        #does this not get updated? uhhhh
        f.write(self.namehash)
        bytearray1 = bytearray(self.namestr, "utf-8")
        bytearray1 = bytearray1[:64]
        #pad out rest of string
        bytearray1 += bytearray(64 - len(bytearray1))
        f.write(bytearray1)
        helperfunctions.skippadding1(4,f)
        self.boundingboxminvector.writeVec4(f)
        self.boundingboxmaxvector.writeVec4(f)
        f.write(self.submeshescount.to_bytes(4, 'little'))
        f.write(self.boneindicespervertex.to_bytes(4, 'little'))
        f.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')
        f.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')
        
        for x in range(self.commandscount):    
            self.GFMeshCommandses[x].writeGFMeshCommands(f)
            
        self.GFSubMeshes.writeSubMeshes(f)
        #where the gfsection ends
        possec1end = f.tell()
        f.seek(possec1start - 16)
        #write gfsection
        newGFSection = GFSection.GFSection.__new__(GFSection.GFSection)
        newGFSection.__init2__("mesh",(possec1end - possec1start))
        newGFSection.writenewsection(f)
        f.seek(possec1end)   
    
    def getfixedattributes(self,submesh,submesh_index):
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
        
        enablecommands = self.GFMeshCommandses[0+(3*submesh_index)].commands
        print(enablecommands)
        picacommands = PicaCommandReader.PicaCommandReader(enablecommands)
        
        #get parameters we need from commands
        i = 0
        for x in range(len(picacommands.commands)):
            currcommand = picacommands.commands[i]
            if(currcommand.register.name == "GPUREG_ATTRIBBUFFERS_FORMAT_LOW"):
                bufferformats |= currcommand.parameters[0] << 0
                print(bufferformats)
            if(currcommand.register.name == "GPUREG_ATTRIBBUFFERS_FORMAT_HIGH"):
                bufferformats |= currcommand.parameters[0] << 32
                print("bufferformats")
                print(bufferformats)
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
            print(submesh.gfsubmeshpart1.submeshname)
            print("attributes")
            print(i2)
            print(((bufferformats >> (48+i2)) & 1))
            if(((bufferformats >> (48+i2)) & 1) != 0):
                scale = 1
                name = PicaAttributeName.PicaAttributeName((bufferpermutation >>(i2*4))&0xf).name
                print(name)
                picaname =  PicaAttributeName.PicaAttributeName((bufferpermutation >>(i2*4))&0xf)
                if(name == "Color"):
                    scale = 3
                if(name == "BoneWeight"):
                    scale = 0.007874016          
                fixed[i2].mul(scale)
                submesh.fixedattributes.append(PicaFixedAttribute.PicaFixedAttribute(picaname,fixed[i2]))
            #attributes
            else:
                permutationidx = ((bufferattributes >> i2*4) & 0xf)
                attributename = ((bufferpermutation >> permutationidx*4) & 0xf)
                attributefmt = ((bufferformats >> permutationidx*4) & 0xf)
                attrib = PicaAttribute.PicaAttribute(PicaAttributeName.PicaAttributeName(attributename),PicaAttributeFormat.PicaAttributeFormat(attributefmt&3),(attributefmt >> 2)+1,scales[attributefmt & 3])
                print(attrib.name)
                if(attrib.name == "BoneIndex"):
                    attrib.scale = 1
                print(attrib.scale)
                    
                
                submesh.attributes.append(attrib)
            print()
            i2 += 1
            
                
                
        #skipping index commands for now until something breaks
    def getfixedattributestest(self):
        self.getfixedattributes(self.GFSubMeshes.GFSubMeshes[0])
                
