import os
import sys
import numpy as np
from enum import Enum
from . import helperfunctions
from . import PicaRegisters
from . import PicaCommand

class PicaVectorFloat24(object):
    def getfloat24(value):	
        word = int(value)
        
    def updatex(self):	
        value = (self.Word2 & 0xffffff)
        floatval = 0
        if((value & 0x7fffff) != 0):
            mantissa = value
            exponent = ((value >> 16) & 0x7f) + 64
            signbit = (value >> 23) & 1
            
            floatval = mantissa << 7
            floatval |= exponent << 23
            floatval |= signbit << 31
        else:
            floatval = ((value & 0x800000) << 8)
        
        self.X = np.float32(floatval)
        
    def updatey(self):	
        value = ((self.Word2 >> 24) | (self.Word1 & 0xffff << 8))
        floatval = 0
        if((value & 0x7fffff) != 0):
            mantissa = value
            exponent = ((value >> 16) & 0x7f) + 64
            signbit = (value >> 23) & 1
            
            floatval = mantissa << 7
            floatval |= exponent << 23
            floatval |= signbit << 31
        else:
            floatval = ((value & 0x800000) << 8)
        
        self.Y = np.float32(floatval)
        
    def updatez(self):	
        value = ((self.Word1 >> 16) | (self.Word0 & 0xff << 16))
        floatval = 0
        if((value & 0x7fffff) != 0):
            mantissa = value
            exponent = ((value >> 16) & 0x7f) + 64
            signbit = (value >> 23) & 1
            
            floatval = mantissa << 7
            floatval |= exponent << 23
            floatval |= signbit << 31
        else:
            floatval = ((value & 0x800000) << 8)
        
        self.Z = np.float32(floatval)
    
    def updatew(self):	
        value = (self.Word0 >> 8)
        floatval = 0
        if((value & 0x7fffff) != 0):
            mantissa = value
            exponent = ((value >> 16) & 0x7f) + 64
            signbit = (value >> 23) & 1
            
            floatval = mantissa << 7
            floatval |= exponent << 23
            floatval |= signbit << 31
        else:
            floatval = ((value & 0x800000) << 8)
        
        self.Z = np.float32(floatval)    
        
    def mul(self, c):
        self.X = self.X*c
        self.Y = self.Y*c
        self.Z = self.Z*c
        self.W = self.W*c
    

    def setword0(self,num):	
        self.Word0 = num
        self.updatez()
        self.updatew()
    def setword1(self,num):	
        self.Word1 = num
        self.updatey()
        self.updatez()
    def setword2(self,num):	
        self.Word2 = num
        self.updatex()
        self.updatey()


    def __init__(self):	
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0
        self.W = 0.0
        
        self.Word0 = 0
        self.Word1 = 0
        self.Word2 = 0