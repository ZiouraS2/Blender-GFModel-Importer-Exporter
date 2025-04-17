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
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, CollectionProperty


from Niji.Model.GFModel import GFModel
from Niji.Model.PicaCommandReader import PicaCommandReader

def load_gfmdl(filepath):
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