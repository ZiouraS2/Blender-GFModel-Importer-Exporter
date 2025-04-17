import os
import sys
from enum import Enum
from . import helperfunctions
from . import PicaAttributeName

class PicaFixedAttribute:
    def __init__(self,name,value):	
        self.name = name    
        self.value = value