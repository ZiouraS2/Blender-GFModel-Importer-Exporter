import bpy
import os
import sys
import io
import struct
import numpy as np
from mathutils import Vector, Matrix

# Import the Niji library
# Module is now local to addon
from Niji.Model.GFModel import GFModel
from Niji.Model.PicaCommandReader import PicaCommandReader

def load_gfmdl(filepath, import_bones=True, import_materials=True):
    print(f"Loading GFMDL file: {filepath}")
    model_name = os.path.basename(filepath).rsplit('.', 1)[0].replace(".PSSG", "")
    
    # Open the file
    with open(filepath, 'rb') as f:
        # Check if file was split
        if f.read(4) != b'\x17\x21\x12\x15':
            f.seek(128)
        else:
            f.seek(0)
        
        # Parse the model
        gfmodel = GFModel(f)
        
        # Create a dictionary to hold the created objects
        created_objects = []
        
        # Import bones if enabled
        armature = None
        if import_bones and gfmodel.bonescount > 0:
            armature = create_armature(gfmodel, model_name)
        
        # Import materials if enabled
        materials = {}
        if import_materials and len(gfmodel.GFMaterials) > 0:
            materials = create_materials(gfmodel)
        
        # Process each mesh in the model
        for mesh_idx, gfmesh in enumerate(gfmodel.GFMeshes):
            mesh_name = f"{model_name}_{mesh_idx}"
            if gfmesh.namestr.strip('\x00'):
                mesh_name = gfmesh.namestr.strip('\x00')
            
            # Process each submesh
            for submesh_idx, submesh in enumerate(gfmesh.GFSubMeshes.GFSubMeshes):
                # Get the attributes for the submesh
                gfmesh.getfixedattributes(submesh)
                
                # Extract vertex data
                vertices, normals, uvs, colors, bone_weights, bone_indices = extract_vertex_data(submesh)
                
                # Extract face indices
                faces = extract_face_indices(submesh)
                
                if not vertices or not faces:
                    continue
                
                # Create the mesh
                submesh_name = f"{mesh_name}_{submesh_idx}"
                if hasattr(submesh.gfsubmeshpart1, 'submeshname') and submesh.gfsubmeshpart1.submeshname.strip('\x00'):
                    submesh_name = submesh.gfsubmeshpart1.submeshname.strip('\x00')
                
                # Create Blender mesh
                me = bpy.data.meshes.new(submesh_name)
                me.from_pydata(vertices, [], faces)
                me.update()
                
                # Add normals if available
                if normals:
                    # In Blender 4.3, simply set the normals directly
                    me.normals_split_custom_set_from_vertices(normals)
                
                # Add UVs if available
                if uvs:
                    me.uv_layers.new(name="UVMap")
                    for i, loop in enumerate(me.loops):
                        me.uv_layers[0].data[i].uv = uvs[loop.vertex_index]
                
                # Add vertex colors if available
                if colors:
                    vcol_layer = me.vertex_colors.new(name="Col")
                    for i, loop in enumerate(me.loops):
                        vcol_layer.data[i].color = colors[loop.vertex_index]
                
                # Create the object
                obj = bpy.data.objects.new(submesh_name, me)
                bpy.context.collection.objects.link(obj)
                

                # commenting out because material export will be a bit more complicated than this
                
                #if materials and mesh_idx < len(gfmodel.GFMeshes):
                    #if mesh_idx < len(gfmodel.GFMaterials):
                        #mat = materials.get(mesh_idx)
                        #if mat:
                            #me.materials.append(mat)
                
                
                # Add armature modifier if we have bones
                if armature and (bone_weights or bone_indices):
                    # Create vertex groups for bones
                    if bone_weights and bone_indices:
                        for v_idx, (weights, indices) in enumerate(zip(bone_weights, bone_indices)):
                            for b_idx, (weight, index) in enumerate(zip(weights, indices)):
                                if weight > 0:
                                    # Convert index to integer
                                    bone_index = int(index)
                                    bone_name = f"Bone_{bone_index}"
                                    if bone_index < len(gfmodel.GFBones):
                                        if hasattr(gfmodel.GFBones[int(index)], 'name') and gfmodel.GFBones[int(index)].name.strip('\x00'):
                                            bone_name = gfmodel.GFBones[int(index)].name.strip('\x00')
                                    
                                    # Create vertex group if it doesn't exist
                                    if bone_name not in obj.vertex_groups:
                                        obj.vertex_groups.new(name=bone_name)
                                    
                                    # Add vertex to group
                                    obj.vertex_groups[bone_name].add([v_idx], weight, 'REPLACE')
                    
                    # Add armature modifier
                    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
                    mod.object = armature
                    mod.use_bone_envelopes = False
                    mod.use_vertex_groups = True
                    
                    # Parent object to armature
                    obj.parent = armature
                
                created_objects.append(obj)
                
        # Select all created objects
        for obj in created_objects:
            obj.select_set(True)
        
        if created_objects:
            bpy.context.view_layer.objects.active = created_objects[0]
    
    return {'FINISHED'}

def extract_vertex_data(submesh):
    vertices = []
    normals = []
    uvs = []
    colors = []
    bone_weights = []
    bone_indices = []
    
    # Get raw buffer and attributes
    rawbuffer = submesh.gfsubmeshpart2.rawbuffer
    attributes = submesh.attributes
    vertexstride = submesh.vertexstride
    verticeslength = submesh.gfsubmeshpart1.verticeslength
    
    # Calculate how many vertices we have
    num_vertices = int(verticeslength / vertexstride)
    
    # Map to keep track of attribute data by name
    attr_map = {}
    
    # Process each vertex
    for v_idx in range(num_vertices):
        rawbuffer.seek(v_idx * vertexstride)
        
        # Reset temporary storage for this vertex
        vertex_data = {
            'position': None,
            'normal': None,
            'texcoord0': None,
            'color': None,
            'boneweight': None,
            'boneindex': None
        }
        
        # Read all attributes for this vertex
        for attr in attributes:
            attr_name = attr.name.name.lower()
            elements = []
            
            # Read the elements for this attribute
            for e in range(attr.elements):
                if attr.attribformat.name == "Float":
                    # why does struct use tuples lmao
                    value = struct.unpack('f', rawbuffer.read(4))[0]
                elif attr.attribformat.name == "Short": 
                    value = int.from_bytes(rawbuffer.read(2), "little")
                elif attr.attribformat.name == "Ubyte":
                    value = int.from_bytes(rawbuffer.read(1), "little")
                elif attr.attribformat.name == "Byte":
                    value = struct.unpack('h', rawbuffer.read(4))[0]
                else:
                    rawbuffer.read(4)  # Skip unknown format
                    value = 0
                
                # Apply scale if needed
                # always apply scale actually
                value = float(value) * attr.scale
                elements.append(value)
            
            # Store the data by attribute name
            vertex_data[attr_name] = elements
        
        # Add position (required)
        if vertex_data['position']:
            x, y, z = vertex_data['position'][:3]
            vertices.append((x, y, z))
        
        # Add normal if available
        if vertex_data['normal']:
            nx, ny, nz = vertex_data['normal'][:3]
            normals.append(Vector((nx, ny, nz)).normalized())
        
        # Add UV if available
        if vertex_data['texcoord0']:
            u, v = vertex_data['texcoord0'][:2]
            uvs.append((u, v))  # Flip Y-coordinate for Blender # Seems to actually be incorrect this way, reverting change
        
        # Add color if available
        if vertex_data['color']:
            if len(vertex_data['color']) >= 4:
                r, g, b, a = vertex_data['color'][:4]
                colors.append((r, g, b, a))
            elif len(vertex_data['color']) == 3:
                r, g, b = vertex_data['color']
                colors.append((r, g, b, 1.0))
        
        # Add bone weights and indices if available
        if vertex_data['boneweight']:
            bone_weights.append(vertex_data['boneweight'])
        if vertex_data['boneindex']:
            bone_indices.append(vertex_data['boneindex'])
    
    return vertices, normals, uvs, colors, bone_weights, bone_indices

def extract_face_indices(submesh):
    faces = []
    indices_buffer = submesh.gfsubmeshpart2.indices
    indices_buffer.seek(0)
    
    # Get the number of indices
    indices_count = submesh.gfsubmeshpart1.indicescount
    
    # Read all indices
    all_indices = []
    for i in range(indices_count):
        index = int.from_bytes(indices_buffer.read(2), "little")
        all_indices.append(index)
    
    # Convert indices to faces
    # Assuming triangles
    for i in range(0, len(all_indices), 3):
        if i + 2 < len(all_indices):
            faces.append((all_indices[i], all_indices[i+1], all_indices[i+2]))
    
    return faces

def create_armature(gfmodel, model_name):
    # Create armature
    arm_data = bpy.data.armatures.new(f"{model_name}_Armature")
    arm_obj = bpy.data.objects.new(f"{model_name}_Skeleton", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    
    # Make armature active and enter edit mode
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Create bones
    bones = {}
    for bone_idx, gfbone in enumerate(gfmodel.GFBones):
        bone_name = f"Bone_{bone_idx}"
        if hasattr(gfbone, 'name') and gfbone.name.strip('\x00'):
            bone_name = gfbone.name.strip('\x00')
        
        bone = arm_data.edit_bones.new(bone_name)
        bone.head = (0, 0, 0)
        bone.tail = (0, 0.1, 0)  # Give it some length
        
        # Set parent if it has one
        if hasattr(gfbone, 'parent') and gfbone.parent != -1 and gfbone.parent < bone_idx:
            parent_name = f"Bone_{gfbone.parent}"
            if gfbone.parent < len(gfmodel.GFBones):
                if hasattr(gfmodel.GFBones[gfbone.parent], 'name') and gfmodel.GFBones[gfbone.parent].name.strip('\x00'):
                    parent_name = gfmodel.GFBones[gfbone.parent].name.strip('\x00')
            
            if parent_name in arm_data.edit_bones:
                bone.parent = arm_data.edit_bones[parent_name]
        
        # Store the bone for later use
        bones[bone_name] = bone
    
    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Apply bone transforms if available
    if hasattr(gfmodel, 'transformmatrix'):
        for bone_idx, gfbone in enumerate(gfmodel.GFBones):
            bone_name = f"Bone_{bone_idx}"
            if hasattr(gfbone, 'name') and gfbone.name.strip('\x00'):
                bone_name = gfbone.name.strip('\x00')
            
            # Create transformation matrix
            if hasattr(gfbone, 'matrix') and gfbone.matrix:
                mat = Matrix()
                for i in range(4):
                    for j in range(4):
                        mat[i][j] = gfbone.matrix.matrix[i][j]
                
                # Apply matrix to pose bone
                if bone_name in arm_obj.pose.bones:
                    arm_obj.pose.bones[bone_name].matrix = mat
    
    return arm_obj

def create_materials(gfmodel):
    materials = {}
    
    for mat_idx, gfmaterial in enumerate(gfmodel.GFMaterials):
        mat_name = f"Material_{mat_idx}"
        if hasattr(gfmaterial, 'name') and gfmaterial.name.strip('\x00'):
            mat_name = gfmaterial.name.strip('\x00')
        
        # Create new material
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        
        # Add texture if available
        if hasattr(gfmaterial, 'textures') and gfmaterial.textures:
            for tex_idx, texture in enumerate(gfmaterial.textures):
                if tex_idx == 0 and texture:  # Just use the first texture for now
                    # Create texture node
                    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    tex_image.image = bpy.data.images.new(
                        name=f"{mat_name}_Tex", 
                        width=256, 
                        height=256
                    )
                    # Connect texture to material
                    mat.node_tree.links.new(
                        tex_image.outputs['Color'],
                        bsdf.inputs['Base Color']
                    )
        
        materials[mat_idx] = mat
    
    return materials 