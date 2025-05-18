import os
import sys
import flatbuffers
from Niji.Model.GFModel import GFModel
from Niji.Model.PicaCommandReader import PicaCommandReader

class Test():
    filepath = sys.argv[1]
    print(filepath)
    f = open(filepath,'rb');
    
    # lazy check to see if it was split
    if(f.read(4) != b'\x17\x21\x12\x15'):
        f.seek(128)
    else:
        f.seek(0)
    
    gfmodel = GFModel(f)
    
    gfmodel.GFMeshes[0].getfixedattributestest()
    fattributes = gfmodel.GFMeshes[0].GFSubMeshes.GFSubMeshes[0].fixedattributes
    attributes = gfmodel.GFMeshes[0].GFSubMeshes.GFSubMeshes[0].attributes
    i = 0
    for x in range(len(fattributes)):
        print(fattributes[i].name)
        i += 1
    print("---------------")
    i2 = 0
    for x in range(len(attributes)):
        print(attributes[i2].name)
        print(attributes[i2].attribformat.name)
        i2 += 1
        
    
    f.close()

