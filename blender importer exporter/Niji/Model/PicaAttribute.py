import os
import sys
from enum import Enum
from . import helperfunctions
from . import PicaAttributeName

class PicaAttribute:
    def __init__(self,name,attribformat,elements,scale):	
        self.name = name    #picaattribname
        self.attribformat = attribformat #picaattribformay
        self.elements = elements #num of elements in the attribute, for example, color has fout for RGBA
        self.scale = scale