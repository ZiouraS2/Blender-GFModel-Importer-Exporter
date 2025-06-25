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
            
    def writeGFMeshCommands(self,f):
        f.write(self.commandslength.to_bytes(4, 'little'))
        f.write(self.commandsindex)
        f.write(self.commandscount)
        f.write(bytes(4))
        print(self.commandslength) 
        #print(self.commandslength >> 2)
        print(len(self.commands))
        for x in range(self.commandslength >> 2):
            f.write(self.commands[x].to_bytes(4, 'little'))
    
    def __init__(self,file):
        self.readGFMeshCommands(file)
        
    def __init2__(self,commandslength,commandsindex,commandscount,commands):
        self.commandslength = commandslength
        self.commandsindex = commandsindex
        self.commandscount = commandscount
        self.commands = commands