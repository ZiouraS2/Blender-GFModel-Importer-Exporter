import os
import sys


#just takes number you want to offset the stream by and seeks pointer + that
def skippadding1(number,file):
	file.seek(file.tell() + number)
    
#keeps going until it finds a byte that's not 0
def skippadding(file):
    if(int.from_bytes(file.read(1),"little") == 0): 
        skippadding(file)    
    else:
        file.seek(file.tell() - 1)
    
# goes until the last byte in current file position is 0
def skippadding3(file):
    if((file.tell() & 0xF) != 0):
        file.seek(file.tell()+1)
        skippadding3(file)