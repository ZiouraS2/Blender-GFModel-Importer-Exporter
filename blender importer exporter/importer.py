import bpy
import os
import sys
import io
import struct
import mathutils
import math
import numpy as np
from mathutils import Vector, Matrix, Euler

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
        gfmodel = GFModel(f,model_name)
        
        #add to blender internal 'storage'
        if ((hasattr(bpy.types.Scene, 'gfmodels')) == False):
            bpy.types.Scene.gfmodels = []
            bpy.types.Scene.gfmodels.append(gfmodel)
        else:
            bpy.types.Scene.gfmodels.append(gfmodel)
            
            
        
        # Create a dictionary to hold the created objects
        created_objects = []
        
        # Import bones if enabled
        armature = None
        if import_bones and gfmodel.bonescount > 0:
            armature = create_armature(gfmodel, model_name)
        
        #import possible textures in model directory automatically
        import_textures(gfmodel,filepath)
        
        # Process each mesh in the model
        for mesh_idx, gfmesh in enumerate(gfmodel.GFMeshes):
            mesh_name = f"{model_name}_{mesh_idx}"
            if gfmesh.namestr.strip('\x00'):
                mesh_name = gfmesh.namestr.strip('\x00')
            
            # Process each submesh
            for submesh_idx, submesh in enumerate(gfmesh.GFSubMeshes.GFSubMeshes):
                # Get the attributes for the submesh
                gfmesh.getfixedattributes(submesh,submesh_idx)
                
                # Extract vertex data
                vertices, normals, tangents, uvs, colors, bone_weights, bone_indices, uvs1, uvs2 = extract_vertex_data(submesh)
                
                # Extract face indices
                faces = extract_face_indices(submesh)
                
                if not vertices or not faces:
                    continue
                
                # Create the mesh
                submesh_name = f"{mesh_name}_{submesh_idx}"
                if hasattr(submesh.gfsubmeshpart1, 'submeshname') and submesh.gfsubmeshpart1.submeshname.strip('\x00'):
                    submesh_name = submesh.gfsubmeshpart1.submeshname.strip('\x00')
                    mesh_name = gfmesh.namestr.strip('\x00')
                
                # Create Blender mesh
                # Adding mesh and submesh names in the same string for more clarity
                if bpy.data.meshes.find(submesh_name) != -1:
                    me = bpy.data.meshes.new(submesh_name)
                else:
                    me = bpy.data.meshes.new(submesh_name+"submesh")
                me.from_pydata(vertices, [], faces)
                me.update()
                
                # Add normals if available
                if normals:
                    # In Blender 4.3, simply set the normals directly
                    me.normals_split_custom_set_from_vertices(normals)
                    
                if tangents:
                    # new vertex color layer because blender tangents aren't persistent
                    vcol_layer = me.vertex_colors.new(name="CustomTangent")
                    for i, loop in enumerate(me.loops):
                            loop = me.loops[i]
                            vert_idx = loop.vertex_index

                            tangent = tangents[vert_idx]

                            # Set RGBA 
                            vcol_layer.data[i].color = (tangent.x, tangent.y, tangent.z, 1.0)
                            
                print(submesh_name)
                # Add UVs if available
                if uvs:
                    me.uv_layers.new(name="UVMap0")
                    if uvs1:
                        print("uv1")
                        print(len(uvs1))
                        me.uv_layers.new(name="UVMap1")
                    if uvs2:
                        print("uv2")
                        print(len(uvs2))
                        me.uv_layers.new(name="UVMap2")
                    for i, loop in enumerate(me.loops):
                        me.uv_layers[0].data[i].uv = uvs[loop.vertex_index]
                        if uvs1:
                            me.uv_layers[1].data[i].uv = uvs1[loop.vertex_index]
                        if uvs2:
                            me.uv_layers[2].data[i].uv = uvs2[loop.vertex_index]
                
                # Add vertex colors if available
                if colors:
                    vcol_layer2 = me.vertex_colors.new(name="Col")
                    for i, loop in enumerate(me.loops):
                        vcol_layer2.data[i].color = colors[loop.vertex_index]
                
                # Create the object
                obj = bpy.data.objects.new(submesh_name, me)
                bpy.context.collection.objects.link(obj)
                

                # commenting out because material export will be a bit more complicated than this
                            
                me.materials.append(create_material(gfmodel,me))
                for f in me.polygons:
                    f.use_smooth = True
                
                
                # Add armature modifier if we have bones
                if armature and (bone_weights or bone_indices):
                    # Create vertex groups for bones
                    print("bone indicess")
                    print(submesh_name)
                    print(len(bone_indices))
                    if bone_weights and bone_indices:
                        for v_idx, (weights, indices) in enumerate(zip(bone_weights, bone_indices)):
                            for b_idx, (weight, index) in enumerate(zip(weights, indices)):
                                if weight > 0:
                                    # Convert index to integer
                                    indices = submesh.gfsubmeshpart1.boneindices
                                    index = int(index)
                                    
                                    #access list of bones used in this submesh for the correct armature bone
                                    bone_index = indices[index]
                                    
                                    bone_name = f"Bone_{bone_index}"
                                    
                                    if bone_index < len(gfmodel.GFBones):
                                        if hasattr(gfmodel.GFBones[int(index)], 'bonename') and gfmodel.GFBones[int(index)].bonename.strip('\x00'):
                                            bone_name = gfmodel.GFBones[bone_index].bonename.strip('\x00')
                                            
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
                else:
                    print("no bone indicess")
                    print(submesh_name)
                
                #add each model to unique collection
                
                
                created_objects.append(obj)
                
        # Orient mesh properly
        obj = [o for o in created_objects if o.type == 'MESH']
        for o in obj:
            RotateObj(o, 90, 'X')
            
        my_coll = bpy.data.collections.new(model_name)
        bpy.context.scene.collection.children.link(my_coll)
        

        # Select all created objects
    

        for obj in created_objects:
            for other_col in obj.users_collection:
                other_col.objects.unlink(obj)
            my_coll.objects.link(obj)
            obj.select_set(True)
        if armature:
            for other_col in armature.users_collection:
                other_col.objects.unlink(armature)
            my_coll.objects.link(armature)


            
        
        if created_objects:
            bpy.context.view_layer.objects.active = created_objects[0]
    
    return {'FINISHED'}

def extract_vertex_data(submesh):
    vertices = []
    normals = []
    tangents = []
    uvs = []
    uvs1 = []
    uvs2 = []
    colors = []
    bone_weights = []
    bone_indices = []
    
    # Get raw buffer and attributes
    rawbuffer = submesh.gfsubmeshpart2.rawbuffer
    attributes = submesh.attributes
    fixedattributes = submesh.fixedattributes
    vertexstride = submesh.vertexstride
    verticeslength = submesh.gfsubmeshpart1.verticeslength
    submesh_name2 = submesh.gfsubmeshpart1.submeshname.strip('\x00')
    
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
            'tangent': None,
            'texcoord0': None,
            'color': None,
            'boneweight': None,
            'boneindex': None,
            'texcoord1': None,
            'texcoord2': None
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
                    value = struct.unpack('h', rawbuffer.read(1))[0]
                else:
                    rawbuffer.read(4)  # Skip unknown format
                    value = 0
                
                # Apply scale if needed
                # always apply scale unless bone index(lol)
                if(attr.name.name == "BoneIndex"):
                    value = float(value) * 1
                else:
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
            
        if vertex_data['tangent']:
            tx, ty, tz = vertex_data['tangent'][:3]
            tangents.append(Vector((tx, ty, tz)).normalized())
        # Add UV if available
        if vertex_data['texcoord0']:
            u, v = vertex_data['texcoord0'][:2]
            uvs.append((u, v))  # Flip Y-coordinate for Blender # Seems to actually be incorrect this way, reverting change
            
        if vertex_data['texcoord1']:
            u, v = vertex_data['texcoord1'][:2]
            uvs1.append((u, v))  
            
        if vertex_data['texcoord2']:
            u, v = vertex_data['texcoord2'][:2]
            uvs2.append((u, v))  
        
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
            #each access to this array will have another array with a list of bone weights
            bone_weights.append(vertex_data['boneweight'])
        if vertex_data['boneindex']:
            #each access to this array will have another array with a list of bone indexes(aka elements[])
            #print(vertex_data['boneindex'])
            bone_indices.append(vertex_data['boneindex'])

    # add attributes from fixed attributes:
    for fixattr in fixedattributes:
        fixattrname = fixattr.name.name.lower()
        #print("fixedattrbute")
        #print(fixattrname)
        #print(fixattr.value)
        
        if (fixattrname == "boneweight"):
            values = np.array([fixattr.value.X,fixattr.value.Y,fixattr.value.Z,fixattr.value.W])
            temparray = np.vstack((values,)*num_vertices)
            bone_weights = temparray.tolist()
        if (fixattrname == "boneindex"):
            values = np.array([fixattr.value.X,fixattr.value.Y,fixattr.value.Z,fixattr.value.W])
            temparray = np.vstack((values,)*num_vertices)
            bone_indices = temparray.tolist()
        if (fixattrname == "texcoord0"):
            values = np.array([fixattr.value.X,fixattr.value.Y])
            temparray = np.vstack((values,)*num_vertices)
            uvs = temparray.tolist()
        if (fixattrname == "texcoord1"):
            values = np.array([fixattr.value.X,fixattr.value.Y])
            temparray = np.vstack((values,)*num_vertices)
            uvs1 = temparray.tolist()
        if (fixattrname == "texcoord2"):
            values = np.array([fixattr.value.X,fixattr.value.Y])
            temparray = np.vstack((values,)*num_vertices)
            uvs2 = temparray.tolist()
    
    return vertices, normals, tangents, uvs, colors, bone_weights, bone_indices, uvs1, uvs2

def extract_face_indices(submesh):
    #need to add support for models wiht byte indices
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

#from reisaskyu gfbmdl plugin
def RotateObj(obj, angle, axis):
    rot_mat = Matrix.Rotation(math.radians(angle), 4, axis)

    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
    orig_loc_mat = Matrix.Translation(orig_loc)
    orig_rot_mat = orig_rot.to_matrix().to_4x4()
    orig_scale_mat = Matrix.Scale(orig_scale[0],4,(1,0,0)) @ Matrix.Scale(orig_scale[1],4,(0,1,0)) @ Matrix.Scale(orig_scale[2],4,(0,0,1))

    obj.matrix_world = orig_loc_mat @ rot_mat @ orig_rot_mat @ orig_scale_mat 

def create_armature(gfmodel, model_name):
    # Create armature
    arm_data = bpy.data.armatures.new(f"{model_name}_Armature")
    arm_obj = bpy.data.objects.new(f"{model_name}_Skeleton", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    print(type(arm_obj))
    
    # Make armature active and enter edit mode
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Create bones
    bones = {}
    for bone_idx, gfbone in enumerate(gfmodel.GFBones):
        bone_name = f"Bone_{bone_idx}"
        if hasattr(gfbone, 'bonename') and gfbone.bonename.strip('\x00'):
            bone_name = gfbone.bonename.strip('\x00')
        
        bone = arm_data.edit_bones.new(bone_name)
        #bone.use_connect = False
        #bone.use_inherit_rotation = True
        
        #create matrix based on bone positions(which are relative to parent positions)
        bone_matrix = mathutils.Matrix.LocRotScale((round(gfbone.TranslationX[0],6),round(gfbone.TranslationY[0],6), round(gfbone.TranslationZ[0],6)),mathutils.Euler((round(gfbone.RotationX[0],6),round(gfbone.RotationY[0],6),round(gfbone.RotationZ[0],6)), 'XYZ'),(gfbone.ScaleX[0],gfbone.ScaleY[0], gfbone.ScaleZ[0]))
        
      
        #make tail slightly bigger so blender no delete
        bone.head = (0,0,0)
        bone.tail = (0,0,0.001)
        
        
        
        if(gfbone.boneparentname != "placeholder"):
            key = arm_obj.data.edit_bones.find(gfbone.boneparentname)
            if(key != -1):
                parentbone = arm_obj.data.edit_bones[gfbone.boneparentname]
            else:
                bone.matrix = bone_matrix
            bone.parent = parentbone
            #bone.head = parentbone.tail
            bone.matrix = parentbone.matrix @ bone_matrix
            reversematrix = parentbone.matrix.inverted() @ bone.matrix
            print("gfmdl bone location")
            print("gfmdl bone location")
            print(gfbone.bonename)
            np.set_printoptions(precision=10, suppress=False)
            print(bone_matrix)
            print(np.array(bone.matrix))
            print(parentbone.matrix)
            print(parentbone.matrix.inverted())
            print(reversematrix)
            
      

        
        


                      
        # Store the bone for later use
        bones[bone_name] = bone
        


                
            
    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')
    for x in bpy.context.collection.objects:    
        if x.type == 'ARMATURE':
            for bone in x.data.bones:
                print("after exit edit")
                print(bone.name)  
                np.set_printoptions(precision=10, suppress=False)
                print(np.array(bone.matrix_local.to_4x4()))
                if bone.parent is not None:
                    print(np.array(bone.parent.matrix_local.to_4x4().inverted() @ bone.matrix_local.to_4x4()))


    
    return arm_obj
#thank you stack overflow
def path_iterator(folder_path):
    for fp in os.listdir(folder_path):
        if fp.endswith( tuple( bpy.path.extensions_image ) ):
            yield fp

def import_textures(gfmodel,filepath):
    indx = len(bpy.data.images)-1
    for imgPath in path_iterator(filepath.rsplit('\\', 1)[0]):
        print("textureinfolder")
        print(imgPath)
        fullPath = os.path.join( filepath.rsplit('\\', 1)[0], imgPath )
        bpy.ops.image.open( filepath = fullPath )
        
        img = bpy.data.images[imgPath]
        print("imgname")
        print(img.name)
        if((len(img.name.rsplit('.', 1)) > 1)):
            newname = img.name.rsplit('.', 1)[0]
            ext = img.name.rsplit('.', 1)[1]
            print(newname)
            print(ext)
            if((ext != "tga")and(len(newname) > 1)):
                img.name = newname
            

        

def create_material(gfmodel,mesh):
        meshname = mesh.name.split('.')
        print(meshname[0])
        for x in range(len(gfmodel.GFMaterials)):
            print(gfmodel.GFMaterials[x].materialname.hashes[0][1])
            if(gfmodel.GFMaterials[x].materialname.hashes[0][1] in meshname[0]):
                gfmaterial = gfmodel.GFMaterials[x]
        
        if hasattr(gfmaterial, 'materialname'):
            mat_name = gfmaterial.materialname.hashes[0][1].strip('\x00')
        
        # Create new material
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        mat.blend_method = 'CLIP' 
        mat.alpha_threshold = 0.01
        #mat.location[0] = mat.location[0] + (1800.0)
        #add bsdf
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        
        for i, o in enumerate(bsdf.inputs):
            if(o.name == 'Specular' or o.name == 'Specular IOR Level'):
                bsdf.inputs[i].default_value = 0.0
                
                
        bsdf.location[0] = bsdf.location[0] + (1600.0)
        
        # Add texture if we have texcoord data in the materials
        if gfmaterial.unitscount > 0:
            for texindex, texcoord in enumerate(gfmaterial.coords):
                # Create texture node
                tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    
                if(texcoord.wrapu.name == "ClampToEdge" or "ClampToBorder"):
                    tex_image.extension = 'CLIP'
                if(texcoord.wrapu.name == "Repeat"):
                    tex_image.extension = "REPEAT"
                if(texcoord.wrapu.name == "Mirror"):
                    tex_image.extension = "MIRROR"
                imagedatablock = bpy.data.images.get(texcoord.texturename.hashes[0][1])
                if(imagedatablock is None):
                    tex_image.image = bpy.data.images.new(
                        name= texcoord.texturename.hashes[0][1], 
                        width=256, 
                        height=256
                    )
                else:
                    tex_image.image = imagedatablock
                
                
                tex_image.location[0] = tex_image.location[0] + 700.0
                tex_image.location[1] = tex_image.location[1] + (300.0*texindex)
                
                uvs = texcoord.mappingtype.name == "UvCoordinateMap"
                
                if(uvs):
                    print("length of texsources")
                    print(len(gfmaterial.texturesources))
                    uvmapnode = mat.node_tree.nodes.new('ShaderNodeUVMap')
                    if(len(gfmaterial.texturesources) <= 0):
                        uvmapnode.uv_map = "UVMap"+str(gfmaterial.unitindex)
                    else:
                        uvmapnode.uv_map = "UVMap"+str(int(gfmaterial.texturesources[texindex]))
                    
                    uvmapnode.location[0] = uvmapnode.location[0] + 200.0
                    uvmapnode.location[1] = uvmapnode.location[1] + (300.0*texindex)
                
                
                #if mapping type is not based on uvs
                nodelocation = 0
                if(not uvs):
                    texcoordnode = mat.node_tree.nodes.new('ShaderNodeTexCoord')
                
                    texcoordnode.location[0] = texcoordnode.location[0] + 200.0
                    texcoordnode.location[1] = texcoordnode.location[1] + (300.0*texindex)
                    
                    if texcoord.mappingtype.name == "CameraCubeEnvMap" or "CameraSphereEnvMap":
                        nodelocation = 6
                    if texcoord.mappingtype.name == "ProjectionMap":
                        nodelocation = 5
                mapnode = mat.node_tree.nodes.new('ShaderNodeMapping')
                
                mapnode.location[0] = mapnode.location[0] + 500.0
                mapnode.location[1] = mapnode.location[1] + (300.0*texindex)
                
                #probably inaccurate? idk really
                mapnode.inputs['Rotation'].default_value[0] = math.radians(texcoord.rotation[0])
                
                # i love blender so-f-df-s-s-f- much!
                mapnode.inputs['Location'].default_value[0]  = texcoord.translation.X*2.0
                mapnode.inputs['Location'].default_value[1]  = texcoord.translation.Y*2.0
                
                print("scales")
                print(texcoord.scale.X)
                print(texcoord.scale.Y)
                mapnode.inputs['Scale'].default_value[0] = texcoord.scale.X
                mapnode.inputs['Scale'].default_value[1] = texcoord.scale.Y
                #link tex coord to mapping
                
                if(uvs):
                    mat.node_tree.links.new(uvmapnode.outputs[0],mapnode.inputs[0])
                else:
                    mat.node_tree.links.new(texcoordnode.outputs[nodelocation],mapnode.inputs[0])
                
                if ("Col" in mesh.vertex_colors):
                    #add color attribute node
                    colorattribnode = mat.node_tree.nodes.new('ShaderNodeVertexColor')
                    colorattribnode.layer_name = "Col"
                    
                    colorattribnode.location[0] = colorattribnode.location[0] - 200.0
                    colorattribnode.location[1] = colorattribnode.location[1] + (300.0*texindex)
                
                    #link mapping to texture node
                    mat.node_tree.links.new(mapnode.outputs['Vector'],tex_image.inputs['Vector'])
                    #add mix node for vertex colors
                    mixrgbnode = mat.node_tree.nodes.new('ShaderNodeMixRGB')
                    mixrgbnode.inputs[0].default_value = 1.00
                    mixrgbnode.blend_type = "MULTIPLY"
                    
                    mixrgbnode.location[0] = mixrgbnode.location[0] + 1200.0
                    mixrgbnode.location[1] = mixrgbnode.location[1] + (300.0*texindex)
                    
                    #mix colors
                    if texindex == 0:
                        mat.node_tree.links.new(
                            tex_image.outputs['Color'],
                            mixrgbnode.inputs[1]
                        )
                        mat.node_tree.links.new(
                            tex_image.outputs['Alpha'],
                            bsdf.inputs['Alpha']
                        )
                        mat.node_tree.links.new(colorattribnode.outputs['Color'],mixrgbnode.inputs[2])
                        
                        #send mix shader to bsdf
                        mat.node_tree.links.new(mixrgbnode.outputs[0],bsdf.inputs['Base Color'])
                else:
                    #link mapping to texture node
                    mat.node_tree.links.new(mapnode.outputs['Vector'],tex_image.inputs['Vector'])
                    if texindex == 0:
                        #send image to bsdf
                        mat.node_tree.links.new(
                            tex_image.outputs['Alpha'],
                            bsdf.inputs['Alpha']
                        )
                        mat.node_tree.links.new(tex_image.outputs[0],bsdf.inputs['Base Color'])
                    
            return mat