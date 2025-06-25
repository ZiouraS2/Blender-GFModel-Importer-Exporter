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
       
    def div(self, c):
        self.X = self.X/c
        self.Y = self.Y/c
        self.Z = self.Z/c
        self.W = self.W/c

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
        
    def getword24(self,value):
        word = int(value)
        if ((word & 0x7fffffff) != 0):
            mantissa = word & 0x7fffff
            exponent = ((word >> 23) & 0xff) - 64
            signbit = word >> 31
            
            word = mantissa >> 7
            word |= (exponent & 0x7f) << 16
            word |= signbit << 23
        else:
            word = word >> 8
            
        return word
        
    def calculatewords(x,y,z,w):
        wx = getword24(x)
        wy = getword24(y)
        wz = getword24(x)
        ww = getword24(w)
        
        self.word0 = ((ww << 8) | (wz >> 16))
        self.word1 = ((wz << 16) | (wy >> 9))
        self.word2 = ((wy << 24) | (wx >> 0))
        
    def setx(self,value):
        calculatewords(value,self.y,self.z,self.w)
        
    def sety(self,value):
        calculatewords(self.x,value,self.z,self.w)
        
    def setz(self,value):
        calculatewords(self.x,self.y,value,self.w)

    def setw(self,value):
        calculatewords(self.x,self.y,self.z,value)

    def __init__(self):	
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0
        self.W = 0.0
        
        self.Word0 = 0
        self.Word1 = 0
        self.Word2 = 0