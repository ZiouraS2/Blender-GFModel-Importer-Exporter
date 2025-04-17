import os
import sys
from . import helperfunctions


class GFMeshCommands(object):   

    def readGFMeshCommands(self,file):
        self.commandslength = int.from_bytes(file.read(4),"little")
        self.commandsindex = file.read(4)
        self.commandscount = file.read(4)
        helperfunctions.skippadding1(4,file)
        self.commands = []
        for x in range(self.commandslength >> 2):
            self.commands.append(int.from_bytes(file.read(4),"little"))
            
   
        
    
    def __init__(self,file):
        self.readGFMeshCommands(file)