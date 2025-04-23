import bpy
import os
import sys
import io
import struct
import numpy as np
import bmesh
from mathutils import Vector, Matrix

def save_gfmdl(filepath, objects, export_materials=True, export_bones=True):
    print(f"Exporting to: {filepath}")
    
    # Check if we have objects to export
    if not objects:
        print("No objects to export")
        return {'CANCELLED'}
    
    # Get the first armature in the scene if available
    armature = None
    if export_bones:
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
    
    # Create a new GFModel
    model_data = create_gfmodel_data(objects, armature, export_materials)
    
    # Write the model data to file
    with open(filepath, 'wb') as f:
        # Write file signature
        f.write(b'\x17\x21\x12\x15')
        
        # Write sections count (placeholder, will be updated later)
        f.write((1).to_bytes(4, byteorder='little'))
        
        # Write padding
        f.write(bytes(8))
        
        # Write model section
        write_model_section(f, model_data)
    
    print(f"Successfully exported to {filepath}")
    return {'FINISHED'}

def write_model_section(f, model_data):
    # Write section identifier (GFMO)
    f.write(b'GFMO\x00\x00\x00\x00')
    
    # Write placeholder section size (will be updated later)
    section_start_pos = f.tell()
    f.write((0).to_bytes(4, byteorder='little'))
    
    # Write offset (0x10)
    f.write((0x10).to_bytes(4, byteorder='little'))
    
    # Write placeholder padding
    f.write(bytes(8))
    
    # Remember start of data
    data_start_pos = f.tell()
    
    # Write shader names section
    write_hash_names(f, model_data['shader_names'])
    
    # Write texture names section
    write_hash_names(f, model_data['texture_names'])
    
    # Write material names section
    write_hash_names(f, model_data['material_names'])
    
    # Write mesh names section
    write_hash_names(f, model_data['mesh_names'])
    
    # Write bounding box min
    write_vector4(f, model_data['bounding_box_min'])
    
    # Write bounding box max
    write_vector4(f, model_data['bounding_box_max'])
    
    # Write transform matrix
    write_matrix4x4(f, model_data['transform_matrix'])
    
    # Write unknown data (placeholder)
    f.write((0).to_bytes(4, byteorder='little'))  # length
    f.write((0).to_bytes(4, byteorder='little'))  # offset
    f.write(bytes(8))  # padding
    
    # Write bones
    write_bones(f, model_data['bones'])
    
    # Write padding
    align_to_16(f)
    
    # Write LUTs
    write_luts(f, model_data['luts'])
    
    # Write materials
    write_materials(f, model_data['materials'])
    
    # Write meshes
    write_meshes(f, model_data['meshes'])
    
    # Calculate section size
    section_end_pos = f.tell()
    section_size = section_end_pos - data_start_pos
    
    # Update section size
    f.seek(section_start_pos)
    f.write(section_size.to_bytes(4, byteorder='little'))
    
    # Return to end of file
    f.seek(section_end_pos)

def write_hash_names(f, hash_names):
    # Write count
    f.write(len(hash_names).to_bytes(4, byteorder='little'))
    
    # Write padding
    f.write(bytes(12))
    
    # Write hashes
    for name in hash_names:
        # Write hash value (or zeros if not available)
        if isinstance(name, tuple) and len(name) > 1:
            hash_value = name[1]
            if isinstance(hash_value, bytes) and len(hash_value) == 4:
                f.write(hash_value)
            else:
                f.write(bytes(4))
        else:
            f.write(bytes(4))
        
        # Write string
        if isinstance(name, tuple) and len(name) > 0:
            string_val = name[0]
            if isinstance(string_val, str):
                # Ensure string is null-terminated and padded to 16 bytes
                encoded_str = string_val.encode('utf-8') + b'\x00'
                padding_len = 16 - (len(encoded_str) % 16)
                encoded_str += bytes(padding_len)
                f.write(encoded_str)
            else:
                f.write(bytes(16))
        else:
            f.write(bytes(16))

def write_vector4(f, vector):
    for value in vector:
        f.write(struct.pack('f', float(value)))

def write_matrix4x4(f, matrix):
    for row in range(4):
        for col in range(4):
            f.write(struct.pack('f', float(matrix[row][col])))

def write_bones(f, bones):
    # Write bone count
    f.write(len(bones).to_bytes(4, byteorder='little'))
    
    # Write padding
    f.write(bytes(12))
    
    # Write each bone
    for bone in bones:
        # Write parent index
        f.write(bone['parent'].to_bytes(4, byteorder='little', signed=True))
        
        # Write bone name (64 bytes, null-terminated)
        name_bytes = bone['name'].encode('utf-8') + b'\x00'
        name_bytes = name_bytes.ljust(64, b'\x00')
        f.write(name_bytes[:64])
        
        # Write bone matrix
        for row in range(4):
            for col in range(4):
                f.write(struct.pack('f', float(bone['matrix'][row][col])))

def write_luts(f, luts):
    # Write LUT count
    f.write(len(luts).to_bytes(4, byteorder='little'))
    
    # Write LUT length
    f.write((16).to_bytes(4, byteorder='little'))  # Standard LUT length
    
    # Write padding
    f.write(bytes(8))
    
    # Write LUTs
    for lut in luts:
        f.write(lut['data'])

def write_materials(f, materials):
    for material in materials:
        # Write section identifier (MTRL)
        f.write(b'MTRL\x00\x00\x00\x00')
        
        # Write section size (placeholder)
        section_start_pos = f.tell()
        f.write((0).to_bytes(4, byteorder='little'))
        
        # Write section offset (0x10)
        f.write((0x10).to_bytes(4, byteorder='little'))
        
        # Write padding
        f.write(bytes(8))
        
        # Remember start of material data
        material_start_pos = f.tell()
        
        # Write material data
        f.write(material['hash_value'])
        f.write(material['name'].encode('utf-8').ljust(64, b'\x00')[:64])
        
        # Write material parameters
        f.write(material['parameters'])
        
        # Write texture count
        f.write(len(material['textures']).to_bytes(4, byteorder='little'))
        
        # Write textures
        for texture in material['textures']:
            # Write texture hash
            f.write(texture['hash_value'])
            
            # Write sampler hash
            f.write(texture['sampler_hash'])
            
            # Write unknown data
            f.write(bytes(8))
        
        # Calculate section size
        material_end_pos = f.tell()
        material_size = material_end_pos - material_start_pos
        
        # Update section size
        f.seek(section_start_pos)
        f.write(material_size.to_bytes(4, byteorder='little'))
        
        # Return to end of material
        f.seek(material_end_pos)
        
        # Align to 16-byte boundary
        align_to_16(f)

def write_meshes(f, meshes):
    for mesh in meshes:
        # Write section identifier (MESH)
        f.write(b'MESH\x00\x00\x00\x00')
        
        # Write section size (placeholder)
        section_start_pos = f.tell()
        f.write((0).to_bytes(4, byteorder='little'))
        
        # Write section offset (0x10)
        f.write((0x10).to_bytes(4, byteorder='little'))
        
        # Write padding
        f.write(bytes(8))
        
        # Remember start of mesh data
        mesh_start_pos = f.tell()
        
        # Write mesh data
        f.write(mesh['hash_value'])
        f.write(mesh['name'].encode('utf-8').ljust(64, b'\x00')[:64])
        
        # Write padding
        f.write(bytes(4))
        
        # Write bounding box
        write_vector4(f, mesh['bounding_box_min'])
        write_vector4(f, mesh['bounding_box_max'])
        
        # Write submesh count
        f.write(len(mesh['submeshes']).to_bytes(4, byteorder='little'))
        
        # Write bone indices per vertex
        f.write(mesh['bone_indices_per_vertex'].to_bytes(4, byteorder='little'))
        
        # Write padding
        f.write(bytes(16))
        
        # Write padding
        f.write(bytes(8))
        
        # Write command count
        f.write(len(mesh['commands']).to_bytes(4, byteorder='little'))
        
        # Write padding
        f.write(int(-12).to_bytes(4, byteorder='little', signed=True))
        
        # Write mesh commands
        for command in mesh['commands']:
            # Write command register
            f.write(command['register'].to_bytes(4, byteorder='little'))
            
            # Write command parameter
            f.write(command['parameter'].to_bytes(4, byteorder='little'))
        
        # Write submeshes part 1
        for submesh in mesh['submeshes']:
            f.write(submesh['hash_value'])
            
            # Write string length
            name_bytes = submesh['name'].encode('utf-8') + b'\x00'
            f.write(len(name_bytes).to_bytes(4, byteorder='little'))
            
            # Write submesh name
            f.write(name_bytes)
            
            # Write bone indices count
            f.write(submesh['bone_indices_count'].to_bytes(1, byteorder='little'))
            
            # Write bone indices
            for index in submesh['bone_indices']:
                f.write(index.to_bytes(1, byteorder='little'))
            
            # Ensure 31 bytes of bone indices
            padding_needed = 31 - len(submesh['bone_indices'])
            if padding_needed > 0:
                f.write(bytes(padding_needed))
            
            # Write vertex count
            f.write(submesh['vertex_count'].to_bytes(4, byteorder='little'))
            
            # Write index count
            f.write(submesh['index_count'].to_bytes(4, byteorder='little'))
            
            # Write vertex data length
            f.write(submesh['vertex_data_length'].to_bytes(4, byteorder='little'))
            
            # Write index data length
            f.write(submesh['index_data_length'].to_bytes(4, byteorder='little'))
        
        # Write submeshes part 2
        for submesh in mesh['submeshes']:
            # Write vertex data
            f.write(submesh['vertex_data'])
            
            # Write index data
            f.write(submesh['index_data'])
            
            # Align to 16-byte boundary
            align_to_16(f)
        
        # Calculate section size
        mesh_end_pos = f.tell()
        mesh_size = mesh_end_pos - mesh_start_pos
        
        # Update section size
        f.seek(section_start_pos)
        f.write(mesh_size.to_bytes(4, byteorder='little'))
        
        # Return to end of mesh
        f.seek(mesh_end_pos)

def align_to_16(f):
    # Get current position
    pos = f.tell()
    
    # Calculate padding needed
    padding = (16 - (pos % 16)) % 16
    
    # Write padding
    if padding > 0:
        f.write(bytes(padding))

def create_gfmodel_data(objects, armature, export_materials):
    # Create model data structure
    model_data = {
        'shader_names': [],
        'texture_names': [],
        'material_names': [],
        'mesh_names': [],
        'bounding_box_min': [float('inf'), float('inf'), float('inf'), 1.0],
        'bounding_box_max': [float('-inf'), float('-inf'), float('-inf'), 1.0],
        'transform_matrix': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        'bones': [],
        'luts': [],
        'materials': [],
        'meshes': []
    }
    
    # Process armature if available
    if armature:
        process_armature(model_data, armature)
    
    # Process materials if enabled
    if export_materials:
        process_materials(model_data, objects)
    
    # Process meshes
    process_meshes(model_data, objects, armature)
    
    return model_data

def process_armature(model_data, armature):
    # Process bones
    for bone in armature.pose.bones:
        # Get parent index
        parent_idx = -1
        if bone.parent:
            parent_idx = list(armature.pose.bones).index(bone.parent)
        
        # Get bone matrix
        mat = bone.matrix.copy()
        mat_list = [[0.0 for _ in range(4)] for _ in range(4)]
        for i in range(4):
            for j in range(4):
                mat_list[i][j] = mat[i][j]
        
        # Add bone data
        model_data['bones'].append({
            'name': bone.name,
            'parent': parent_idx,
            'matrix': mat_list
        })

def process_materials(model_data, objects):
    # Get unique materials
    materials = set()
    for obj in objects:
        if obj.type == 'MESH':
            for mat in obj.data.materials:
                if mat:
                    materials.add(mat)
    
    # Process each material
    for mat_idx, mat in enumerate(materials):
        # Create material name
        mat_name = mat.name
        model_data['material_names'].append((mat_name, bytes(4)))  # No hash for now
        
        # Get textures
        textures = []
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    tex_name = node.image.name
                    model_data['texture_names'].append((tex_name, bytes(4)))  # No hash for now
                    
                    # Add texture data
                    textures.append({
                        'hash_value': bytes(4),
                        'sampler_hash': bytes(4)
                    })
        
        # Add material data
        model_data['materials'].append({
            'hash_value': bytes(4),
            'name': mat_name,
            'parameters': bytes(24),  # Placeholder parameters
            'textures': textures
        })

def process_meshes(model_data, objects, armature):
    for obj_idx, obj in enumerate(objects):
        if obj.type != 'MESH':
            continue
        
        # Create mesh name
        mesh_name = obj.name
        model_data['mesh_names'].append((mesh_name, bytes(4)))  # No hash for now
        
        # Calculate bounding box
        calc_bounding_box(model_data, obj)
        
        # Create mesh data
        mesh_data = {
            'hash_value': bytes(4),
            'name': mesh_name,
            'bounding_box_min': model_data['bounding_box_min'],
            'bounding_box_max': model_data['bounding_box_max'],
            'bone_indices_per_vertex': 0,
            'commands': create_mesh_commands(obj),
            'submeshes': create_submeshes(obj, armature)
        }
        
        model_data['meshes'].append(mesh_data)

def calc_bounding_box(model_data, obj):
    # Get world matrix
    world_mat = obj.matrix_world
    
    # Update bounding box
    for v in obj.data.vertices:
        # Transform vertex to world space
        co = world_mat @ v.co
        
        # Update min
        model_data['bounding_box_min'][0] = min(model_data['bounding_box_min'][0], co.x)
        model_data['bounding_box_min'][1] = min(model_data['bounding_box_min'][1], co.y)
        model_data['bounding_box_min'][2] = min(model_data['bounding_box_min'][2], co.z)
        
        # Update max
        model_data['bounding_box_max'][0] = max(model_data['bounding_box_max'][0], co.x)
        model_data['bounding_box_max'][1] = max(model_data['bounding_box_max'][1], co.y)
        model_data['bounding_box_max'][2] = max(model_data['bounding_box_max'][2], co.z)

def create_mesh_commands(obj):
    # This is a placeholder for creating the PICA commands that define the mesh format
    # These commands would typically be derived from the mesh attributes
    
    # For now, create some basic commands for position, normal, and uv
    commands = []
    
    # Add position attribute command
    commands.append({
        'register': 0x283,  # GPUREG_ATTRIBBUFFERS_FORMAT_LOW
        'parameter': 0x10000
    })
    
    # Add normal attribute command
    commands.append({
        'register': 0x284,  # GPUREG_ATTRIBBUFFERS_FORMAT_HIGH
        'parameter': 0x00001
    })
    
    # Add UV attribute command
    commands.append({
        'register': 0x242,  # GPUREG_ATTRIBBUFFER0_CONFIG1
        'parameter': 0x001
    })
    
    # Vertex stride
    commands.append({
        'register': 0x244,  # GPUREG_ATTRIBBUFFER0_CONFIG2
        'parameter': 0x120000  # 12 bytes vertex stride, 3 attributes
    })
    
    return commands

def create_submeshes(obj, armature):
    submeshes = []
    
    # Create a bmesh to triangulate if needed
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    # Create a new mesh from bmesh
    me = bpy.data.meshes.new("temp")
    bm.to_mesh(me)
    bm.free()
    
    # Create vertex data
    vertex_data = bytearray()
    
    # Get mesh data
    vertices = me.vertices
    
    # Process vertices
    for v in vertices:
        # Position (3 floats, 12 bytes)
        vertex_data.extend(struct.pack('fff', v.co.x, v.co.y, v.co.z))
        
        # Normal (3 floats, 12 bytes)
        vertex_data.extend(struct.pack('fff', v.normal.x, v.normal.y, v.normal.z))
    
    # Create index data
    index_data = bytearray()
    
    # Process faces
    for f in me.polygons:
        # Triangle indices
        for idx in f.vertices:
            index_data.extend(idx.to_bytes(2, byteorder='little'))
    
    # Clean up temporary mesh
    bpy.data.meshes.remove(me)
    
    # Create submesh data
    submesh = {
        'hash_value': bytes(4),
        'name': obj.name,
        'bone_indices_count': 0,
        'bone_indices': [],
        'vertex_count': len(vertices),
        'index_count': len(index_data) // 2,
        'vertex_data_length': len(vertex_data),
        'index_data_length': len(index_data),
        'vertex_data': vertex_data,
        'index_data': index_data
    }
    
    # Process bone weights if armature exists and vertex groups are set up
    if armature and obj.vertex_groups:
        # Get all bone names from armature
        bone_names = [bone.name for bone in armature.pose.bones]
        
        # Map vertex groups to bones
        bone_indices = []
        for group in obj.vertex_groups:
            if group.name in bone_names:
                bone_idx = bone_names.index(group.name)
                bone_indices.append(bone_idx)
                
        submesh['bone_indices'] = [min(idx, 255) for idx in bone_indices]
        submesh['bone_indices_count'] = len(bone_indices)
    
    submeshes.append(submesh)
    return submeshes 