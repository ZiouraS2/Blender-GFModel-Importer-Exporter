import os
import sys
import ctypes
import math

from . import helperfunctions
Prime = ctypes.c_uint32(16777619)

class GFNV1(object):  

    def HASH(self,stringbyte):
        self.hashcode = ctypes.c_uint32(self.hashcode.value*Prime.value)
        self.hashcode = ctypes.c_uint32(self.hashcode.value^stringbyte.value)

        
    def hashstring(self,string):
        string = string.strip('\x00')
        stringbytearray = bytearray(string, "ascii")
        for byte in stringbytearray:
            self.HASH(ctypes.c_uint32(byte))

    def __init__(self):
        self.hashcode = Prime
