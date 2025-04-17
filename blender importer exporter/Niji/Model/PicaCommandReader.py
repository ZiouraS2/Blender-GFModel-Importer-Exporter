import os
import sys
from enum import Enum
from . import helperfunctions
from . import PicaRegisters
from . import PicaCommand

class PicaCommandReader:

    def __init__(self,binarydata):	
        self.commands = []
        
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
                    
                    cmd = PicaCommand.PicaCommand(PicaRegisters.PicaRegisters(commandid),parameters,mask)
                    commandid += 1
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
                cmd = PicaCommand.PicaCommand(PicaRegisters.PicaRegisters(commandid),parameters,mask)
                self.commands.append(cmd)
            
            if((index & 1) != 0):
                index+=1