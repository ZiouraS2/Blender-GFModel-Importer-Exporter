bl_info = {
    "name": "Gen7 GFMDL Import",
    "blender": (4, 2, 0),
    "category": "Import-Export",
    "location": "File > Import > GFMDL (.gfmodel)",
    "description": "",
    "author": "ZiouraS2",
    "version": (1, 5, 7),
    "support": ""
}

import bpy
import sys
import os
import io
import struct
import numpy as np
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, CollectionProperty


from Niji.Model.GFModel import GFModel
from Niji.Model.PicaCommandReader import PicaCommandReader

def load_gfmdl(filepath):
    objects = {}
    current_object = None
    jmdl_name = os.path.basename(filepath).rsplit('.', 1)[0].replace(".PSSG", "")
    uv_layers = []
    objects[0] = {"vertices": [], "faces": [], "colors": [], "uvs": {}}
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
    rawbuffer = gfmodel.GFMeshes[0].GFSubMeshes.GFSubMeshes[0].gfsubmeshpart2.rawbuffer
    indices = gfmodel.GFMeshes[0].GFSubMeshes.GFSubMeshes[0].gfsubmeshpart2.indices
    vertexstride = gfmodel.GFMeshes[0].GFSubMeshes.GFSubMeshes[0].vertexstride
    verticeslength = gfmodel.GFMeshes[0].GFSubMeshes.GFSubMeshes[0].gfsubmeshpart1.verticeslength
    i = 0
    for x in range(len(fattributes)):
        print(fattributes[i].name)
        i += 1
    print("---------------")
    print(verticeslength)
    print(vertexstride)
    listlength = int(verticeslength/vertexstride)
    print(listlength)
    print(listlength)
    i2 = 0
    for x in range(listlength):
        i2 = 0
        print("scale")
        for x in range(len(attributes)):
            print(i2)
            print(attributes[i2].name)
            print(attributes[i2].attribformat.name)
            i3 = 0
            
            readtype = 0
            usestruct = False
            scale = attributes[i2].scale
            print(scale)
            if(attributes[i2].attribformat.name == "Byte"):
                readtype = 1
            if(attributes[i2].attribformat.name == "Ubyte"):
                readtype = 1
            if(attributes[i2].attribformat.name == "Short"):
                readtype = 2
            if(attributes[i2].attribformat.name == "Float"):
                readtype = 4
                usestruct = True
            elements = []
            print(usestruct)
            for x in range(attributes[i2].elements):
                if(usestruct):
                    elements.append(struct.unpack('f',rawbuffer.read(readtype)))
                else:
                    elements.append(int.from_bytes(rawbuffer.read(readtype),"little"))
                i3 += 1
            print(elements[0])
            print(np.float32(elements[0])*scale)
            if(attributes[i2].name.name == "Position"):
                objects[0]["vertices"].append((np.float32(elements[0])*scale, np.float32(elements[1])*scale, np.float32(elements[2])*scale))
            i2 += 1
        mesh = bpy.data.meshes.new(name="test")
        obj = bpy.data.objects.new(name="test", object_data=mesh)
        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(objects[0]["vertices"], [], [])
        mesh.update()
                
            
        
    
    f.close()
    return objects

class ImportGFMDL (bpy.types.Operator,ImportHelper):
    bl_idname = "import_scene.gfmdl"
    bl_label = "Import GFMDL"
    filename_ext = ".bin"
    #not filtering by extension because i don't feel like it
    #filter_glob: StringProperty(default="*.bin", options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        for file in self.files:
            load_gfmdl(os.path.join(directory, file.name))
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportGFMDL.bl_idname, text="GFMDL (.gfmodel)")

def register():
    bpy.utils.register_class(ImportGFMDL)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportGFMDL)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()