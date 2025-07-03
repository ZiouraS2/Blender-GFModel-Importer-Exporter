import os
import sys
import io
import ctypes
import math

from . import helperfunctions
Prime = ctypes.c_uint32(16777619)
Prime24 = 16777619
baseoff = 2166136261

class GFNV1(object):  

    def HASH(self,stringbyte):
        self.hashcode = ctypes.c_uint32(self.hashcode.value*Prime.value)
        self.hashcode = ctypes.c_uint32(self.hashcode.value^stringbyte.value)
    # this one doesn't use u32... for whatever reason
    def HASH24(self,stringbyte):
        self.hashcode = self.hashcode*Prime24
        self.hashcode = self.hashcode^stringbyte    
        

        
    def hashstring(self,string):
        string = string.strip('\x00')
        stringbytearray = bytearray(string, "ascii")
        for byte in stringbytearray:
            self.HASH(ctypes.c_uint32(byte))
    def hashstring24(self,string):    
        for x in len(string):
            byte = string.read(1)
            self.HASH24(byte)

    def __init__(self):
        self.hashcode = Prime
    def __init24__(self):
        self.hashcode = baseoff   
