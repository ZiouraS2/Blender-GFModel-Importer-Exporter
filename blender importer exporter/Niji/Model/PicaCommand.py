import os
import sys
from enum import Enum
from . import helperfunctions
from . import PicaRegisters

class PicaCommand:
    def __init__(self,register,parameters,mask,isconsecutive):	
        self.register = register    
        self.parameters = parameters
        self.mask = mask
        #only used for writing commands, reader will figure out consecutive commands regardless
        self.consecutive = isconsecutive
