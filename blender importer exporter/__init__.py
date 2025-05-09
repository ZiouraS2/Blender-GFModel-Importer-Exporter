bl_info = {
    "name": "Gen7 GFMDL Import-Export",
    "blender": (4, 3, 0),
    "category": "Import-Export",
    "location": "File > Import/Export > GFMDL (.gfmodel)",
    "description": "Import and export Gen 7 Pokemon model files",
    "author": "ZiouraS2",
    "version": (1, 6, 0),
    "support": "COMMUNITY",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

import os
import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, CollectionProperty, BoolProperty, EnumProperty

# Import all the required modules
from . import importer
from . import exporter

# Define classes for UI
class ImportGFMDL(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.gfmdl"
    bl_label = "Import GFMDL"
    bl_description = "Import Gen 7 Pokemon model files (.gfmodel, .bin)"
    filename_ext = ".bin"
    
    filter_glob: StringProperty(
        default="*.bin;*.gfmodel",
        options={'HIDDEN'},
    )
    
    files: CollectionProperty(
        type=bpy.types.PropertyGroup,
    )
    
    import_bones: BoolProperty(
        name="Import Bones",
        description="Import bone/armature data if available",
        default=True,
    )
    
    import_materials: BoolProperty(
        name="Import Materials",
        description="Import material data if available",
        default=True,
    )

    def execute(self, context):
        # Import here to avoid circular imports
        from . import importer
        
        directory = os.path.dirname(self.filepath)
        for file in self.files:
            importer.load_gfmdl(
                os.path.join(directory, file.name),
                import_bones=self.import_bones,
                import_materials=self.import_materials
            )
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "import_bones")
        layout.prop(self, "import_materials")

class ExportGFMDL(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.gfmdl"
    bl_label = "Export GFMDL"
    bl_description = "Export model to Gen 7 Pokemon model format (.gfmodel)"
    filename_ext = ".gfmodel"
    
    filter_glob: StringProperty(
        default="*.gfmodel",
        options={'HIDDEN'},
    )
    
    export_materials: BoolProperty(
        name="Export Materials",
        description="Export material data",
        default=True,
    )
    
    export_bones: BoolProperty(
        name="Export Bones",
        description="Export bone/armature data",
        default=True,
    )
    
    export_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
    )
    
    def execute(self, context):
        # Import here to avoid circular imports
        from . import exporter
        
        # Get objects to export
        if self.export_selection:
            objects = context.selected_objects
        else:
            objects = context.scene.objects
        
        # Filter to only include mesh objects
        mesh_objects = [obj for obj in objects if obj.type == 'MESH']
        
        return exporter.save_gfmdl(
            self.filepath,
            mesh_objects,
            export_materials=self.export_materials,
            export_bones=self.export_bones
        )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "export_materials")
        layout.prop(self, "export_bones")
        layout.prop(self, "export_selection")

def menu_func_import(self, context):
    self.layout.operator(ImportGFMDL.bl_idname, text="GFMDL (.gfmodel)")

def menu_func_export(self, context):
    self.layout.operator(ExportGFMDL.bl_idname, text="GFMDL (.gfmodel)")

# Classes to register
classes = (
    ImportGFMDL,
    ExportGFMDL,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register() 