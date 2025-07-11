import os
import sys
import struct
import numpy as np
from enum import Enum
from . import helperfunctions
from . import PicaRegisters
from . import PicaCommand
from . import UniformManager
from . import PicaFloatVector24

class PicaCommandReader:

    def setindexcommand(self,cmd):
        self.uniformindex = (cmd & 0xff) << 2
        self.uniform32bits = (cmd >> 31) != 0
        #print(self.uniformindex)
        #print(self.uniform32bits)
        
    def setvalueparameters(self,params,uniformindex):
        for x in range(len(params)):
            UIdx = (self.uniformindex >> 2) & 0x5f
            if(self.uniform32bits):
                valuearr = struct.unpack('f', struct.pack('I', params[x]))[0]
                if((self.uniformindex & 3) == 0):
                    self.vtxuniforms.uniforms[UIdx][3] = valuearr
                if((self.uniformindex & 3) == 1):
                    self.vtxuniforms.uniforms[UIdx][2] = valuearr
                if((self.uniformindex & 3) == 2):
                    self.vtxuniforms.uniforms[UIdx][1] = valuearr
                if((self.uniformindex & 3) == 3):
                    self.vtxuniforms.uniforms[UIdx][0] = valuearr
            else:
                if((self.uniformindex & 3) == 0):
                    self.vecF24.Word0 = params[x]
                if((self.uniformindex & 3) == 1):
                    self.vecF24.Word1 = params[x]
                if((self.uniformindex & 3) == 2):
                    self.vecF24.Word2 = params[x]
                    
                if((self.uniformindex & 3) == 2):
                    self.uniformindex = self.uniformindex + 1
                    self.vtxuniforms.uniforms[UIdx][0] = self.vecF24.X
                    self.vtxuniforms.uniforms[UIdx][1] = self.vecF24.Y
                    self.vtxuniforms.uniforms[UIdx][2] = self.vecF24.Z
                    
            self.uniformindex = self.uniformindex + 1
         
    def checkvtxunifromscmd(self,cmd):
        if(cmd.register.value == 0x02C0):
            self.setindexcommand(cmd.parameters[0])
        if(cmd.register.value >= 0x02C1 and cmd.register.value <= 0x02C8):
            self.setvalueparameters(cmd.parameters,self.uniformindex)
    
    def __init2__(self,commands):
        self.commands = commands
        self.vecF24 = PicaFloatVector24.PicaVectorFloat24()
        self.uniformindex = 0
        self.uniform32bits = True
        self.vtxuniforms = UniformManager.UniformManager()
    
    def __init__(self,binarydata):	
        self.commands = []
        self.uintcommands = []
        self.vecF24 = PicaFloatVector24.PicaVectorFloat24()
        self.uniformindex = 0
        self.uniform32bits = True
        self.vtxuniforms = UniformManager.UniformManager()
        
        index = 0
        while(index < len(binarydata)):
            param = binarydata[index]
            index+=1
            #print(param)
            command = binarydata[index]
            index+=1
            #print(command)
            
            commandid = (command >> 0) & 0xffff
            mask = (command >> 16) & 0xffff
            extraparams = (command >> 20) & 0x7ff
            #print("extraparams")
            #print(extraparams)
            consecutive = ((command >> 31) != 0)
            
            if(consecutive):
                index2 = 0
                for x in range(extraparams+1):
                    parameters = []
                    parameters.append(param)
                    #print(PicaRegisters.PicaRegisters(commandid).name)
                    
                    cmd = PicaCommand.PicaCommand(PicaRegisters.PicaRegisters(commandid),parameters,mask,False)
                    commandid += 1
                    
                    self.checkvtxunifromscmd(cmd)
                    
                    self.commands.append(cmd)
                    if(index2 < extraparams):
                        param = binarydata[index]
                        index+=1
                    index2+=1
                        
            else:
                parameters = []
                parameters.append(param)
                for x in range(extraparams):
                    parameters.append(binarydata[index])
                    index+=1
                    
                #print(PicaRegisters.PicaRegisters(commandid).name)
                cmd = PicaCommand.PicaCommand(PicaRegisters.PicaRegisters(commandid),parameters,mask,False)
                
                self.checkvtxunifromscmd(cmd)
                
                self.commands.append(cmd)
            
            if((index & 1) != 0):
                index+=1
                
    def serialize_commands(self):
        commandlist = []
        for x in range(len(self.commands)):
            currcommand = self.commands[x]
            #print(currcommand.register.name)
            #append first parameter first
            commandlist.append(currcommand.parameters[0])
            #check is command is consecutive
            consecutivebit = (2147483648 if currcommand.consecutive == True else 0)
            
            #command is next, btu we need to rebuild it from the data in the picacommand
            if(len(currcommand.parameters) > 1):
                extraparams = (((len(currcommand.parameters) - 1) & 0x7ff) << 20)
                newcommand = (currcommand.register.value | (currcommand.mask << 16) | extraparams | consecutivebit)
                #add command
                commandlist.append(newcommand)
                for x in range(len(currcommand.parameters) - 1):
                    commandlist.append(currcommand.parameters[x+1])
                    #align stuff
                if((len(commandlist) & 1) != 0):
                        commandlist.append(0)
            else:
                newcommand = (currcommand.register.value | (currcommand.mask << 16))
                #add command
                commandlist.append(newcommand)
                
            #print(commandlist)
        #allignment to 16 bytes
        while (((len(commandlist)+2) & 3) != 0):
            print("commandlist length")
            print(len(commandlist))
            commandlist.append(0)
        #end command
        commandlist.append(1)
        commandlist.append(983613)
        return commandlist