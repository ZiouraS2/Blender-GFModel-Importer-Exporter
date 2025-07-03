import bpy
import os
import sys
import io
import struct
import math
import numpy as np
import bmesh
import ctypes
from mathutils import Vector, Matrix

from Niji.Model.GFModel import GFModel
from Niji.Model.GFMesh import GFMesh
from Niji.Model.GFSubMesh import GFSubMesh
from Niji.Model.GFSubMesh import GFSubMeshes
from Niji.Model.RGBA import RGBA
from Niji.Model.Matrix4x4 import Matrix4x4
from Niji.Model.Vector4 import Vector4
from Niji.Model.GFMaterial import GFMaterial
from Niji.Model.PicaCommandReader import PicaCommandReader
from Niji.Model.GFHashName import GFHashName
from Niji.Model.GFHashName2 import GFHashName2
from Niji.Model.GFNV1 import GFNV1
from Niji.Model.GFBone import GFBone
from Niji.Model.GFMaterial import GFMaterial
from Niji.Model.GFTextureCoord import GFTextureCoord
from Niji.Model.GFTextureWrap import GFTextureWrap
from Niji.Model.PicaRegisters import PicaRegisters
from Niji.Model.PicaCommand import PicaCommand
from Niji.Model.UniformManager import UniformManager
from Niji.Model.PicaFloatVector24 import PicaVectorFloat24
from Niji.Model.GFMeshCommands import GFMeshCommands
from Niji.Model.PicaAttributeName import PicaAttributeName
from Niji.Model.PicaAttributeFormat import PicaAttributeFormat
from Niji.Model.PicaAttribute import PicaAttribute
from Niji.Model.PicaFixedAttribute import PicaFixedAttribute

#for model bounding box
modelmaxx = 0
modelmaxy = 0
modelmaxz = 0
modelminx = 0
modelminy = 0
modelminz = 0

#warning booleans
isvertcountunsupported = False
isbonecountunsupported = False
isbonesubmeshcountunsupported = False
isbonesubmeshweightcountunsupported = False

def save_gfmdl(filepath, objects):
    global isvertcountunsupported 
    global isbonecountunsupported
    global isbonesubmeshcountunsupported 
    global isbonesubmeshweightcountunsupported 
    
    print(f"Exporting to: {filepath}")
    model_name = os.path.basename(filepath).rsplit('.', 1)[0].replace(".PSSG", "")
    
    # Check if we have objects to export
    if not objects:
        print("No objects to export")
        return {'CANCELLED'}
            
    currcoll = None    
    gfmodeldata = None
    #Find collecton containing selected objects
    for col in bpy.data.collections:    
        for obj in objects:
            if obj.name in col.objects:
                print("Found collection with selected objects: ")
                print(col.name)
                currcoll = col
                break
    if currcoll == None:
        print("Collection not found")
        return {'CANCELLED'}
    
    # access internal gfmodel data saved
    #print((hasattr(bpy.types.Scene, 'gfmodels') and hasattr(currcoll, 'name') ))
    if (hasattr(bpy.types.Scene, 'gfmodels') and hasattr(currcoll, 'name') ):
        gfmodels = bpy.types.Scene.gfmodels
        for x in range(len(bpy.types.Scene.gfmodels)):
            print(gfmodels[x].name)
            print(currcoll.name)
            if(gfmodels[x].name in currcoll.name):
                print("found match between gfmodel data and blender data")
                print(gfmodels[x].name)
                gfmodeldata = gfmodels[x]
            else:
                print("no match found this time")
    
    
    
    #Create or Re-create GFModel data based on whether data is found
    if(gfmodeldata != None):
        print("Found previously gfmodel data, will copy over settings")
        gfmodel = recreate_gfmodel_data(currcoll, gfmodeldata)
    else:
        print("No previously found gfmodel data, will create new model")
        print("recreating gfmodeldata")
        gfmodel = create_new_gfmodel_data(currcoll)
    
    #Write the model data to file
    with open(filepath, 'wb') as f:      
        # Write model
        if(gfmodeldata != None):
            gfmodeldata.writeModel(f,currcoll)
        else:
            gfmodel.writeModel(f,currcoll)
            
    #User warnings for format limitations
    if isvertcountunsupported:
        print("Vert count is more than the 2 byte integer limit, and will look incorrect.")
    if isbonecountunsupported:
        print("Bone count is more than the 110, and may break in game.")
    if isbonesubmeshcountunsupported:
        print("One or more submeshes has more than 31 bones in their indices. This may break in game.")    
    if isbonesubmeshweightcountunsupported:
        print("One or more vertices has more than 4 bones affecting it's weights. Some have been removed for compatibility in-game.") 
    
    print(f"Successfully exported to {filepath}")
    return {'FINISHED'}
    
#https://stackoverflow.com/questions/4459703/how-to-make-lists-contain-only-distinct-element-in-python
def _f(seq):  
        seen = set()
        return [x for x in seq if x not in seen and not seen.add(x)]    
        
def repackvertexdata(submeshes, gfmeshdata, gfbones):
    #for mesh boundinb box(which is unused on pokemon models??)
    global modelmaxx
    global modelmaxy
    global modelmaxz
    global modelminx
    global modelminy
    global modelminz
    
    maxx = 0
    maxy = 0
    maxz = 0
    minx = 0
    miny = 0
    minz = 0 
    
    global isvertcountunsupported 
    global isbonesubmeshcountunsupported
    global isbonesubmeshweightcountunsupported
    
    
    for x1 in range(len(submeshes)):
        currsubmesh = submeshes[x1]
        # get number of vertices
        num_vertices = len(currsubmesh.data.vertices)
        if num_vertices > 65535:
            isvertcountunsupported = True
               
        # not all submeshes will have these so not all of them will be used
        # need to add submesh renaming changes
        vertices = []
        normals = []
        #precuationary measure because apparently uv maps in blender don't require every vertice to be used
        uvs = [None]*num_vertices
        uvs1 = [None]*num_vertices
        uvs2 = [None]*num_vertices
        colors = []
        bone_weights = []
        bone_indices = []
    
        # Get past raw buffer and attributes
        attributes = gfmeshdata.GFSubMeshes.GFSubMeshes[x1].attributes
        fixedattributes = gfmeshdata.GFSubMeshes.GFSubMeshes[x1].fixedattributes
        boneindices = []
        submesh_name = gfmeshdata.GFSubMeshes.GFSubMeshes[x1].gfsubmeshpart1.submeshname.strip('\x00')
        
    
        newrawbuffer = io.BytesIO()
    
        # Map to keep track of attribute data by name
        attr_map = {}
    
        # Process each vertex
        
        haveuv0 = (len(currsubmesh.data.uv_layers) > 0)
        haveuv1 = (len(currsubmesh.data.uv_layers) > 1)
        haveuv2 = (len(currsubmesh.data.uv_layers) > 2)
        #get correct uvs? first one in loop that matches vertex index
        for v_idx in range(num_vertices):
            for i, loop in enumerate(currsubmesh.data.loops):
                if loop.vertex_index == v_idx:
                    if haveuv0:
                        uv = currsubmesh.data.uv_layers[0].data[i].uv
                        uvs[v_idx] = uv.copy()
                    if haveuv1:
                        uv1 = currsubmesh.data.uv_layers[1].data[i].uv
                        uvs1[v_idx] = uv1.copy()
                    if haveuv2:
                        uv2 = currsubmesh.data.uv_layers[2].data[i].uv
                        uvs2[v_idx] = uv2.copy()
                    break
        
        for v_idx in range(num_vertices):
        
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
                if v_idx < 2:
                    print(attr_name)
                elements = []
                values = []
                # Add position (required)
                if attr_name == 'position':
                    x, y, z = list(currsubmesh.data.vertices[v_idx].co)
                    float(x) / attr.scale
                    float(y) / attr.scale
                    float(z) / attr.scale
                    #bounding box calc
                    if x > maxx:
                        maxx = x
                    if y > maxy:
                        maxy = y
                    if z > maxz:
                        maxz = z
                    if x < minx:
                        minx = x
                    if y < miny:
                        miny = y
                    if z < minz:
                        minz = z
                    
                    
                    values.append((x, y, z))
                
                # Add normal if available
                if attr_name == 'normal':
                    nx, ny, nz = list(currsubmesh.data.vertices[v_idx].normal)
                    float(nx) / attr.scale
                    float(ny) / attr.scale
                    float(nz) / attr.scale
                    values.append((nx, ny, nz))
                    
                # Add tangent if available    
                if attr_name == 'tangent':
                    if (currsubmesh.data.vertex_colors.find("CustomTangent") != 1):
                        r, g, b, a = list(currsubmesh.data.vertex_colors["CustomTangent"].data[v_idx].color)
                        values.append((r, g, b))
                    else:
                        values.append((0.0, 0.0, 0.0))
                    
                # Add UV if available
                if attr_name == 'texcoord0':
                    if v_idx < 2:
                        print("uvs")
                        print(uvs[v_idx])
                    if uvs[v_idx] != None:
                        u, v = list(uvs[v_idx])
                    else:
                        u, v = [0.0,0.0]
                    values.append((float(u) / attr.scale, float(v / attr.scale)))  # Flip Y-coordinate for Blender # Seems to actually be incorrect this way, reverting change
            
                if attr_name == 'texcoord1':
                    if uvs1[v_idx] != None:
                        u, v = list(uvs1[v_idx])
                    else:
                        u, v = [0.0,0.0]
                    values.append((float(u) / attr.scale, float(v) / attr.scale))  
            
                if attr_name == 'texcoord2':
                    if uvs2[v_idx] != None:
                        u, v = list(uvs2[v_idx])
                    else:
                        u, v = [0.0,0.0]
                    values.append((float(u) / attr.scale, float(v) / attr.scale))  # Flip Y-coordinate for Blender # Seems to actually be incorrect this way, reverting change 
        
                # Add color if available
                if attr_name == 'color':
                    r, g, b, a = list(currsubmesh.data.vertex_colors["Col"].data[v_idx].color)
                    values.append((float(r) / attr.scale, float(g) / attr.scale, float(b) / attr.scale, float(a) / attr.scale))
        
                # Add bone weights and indices if available
                if attr_name == 'boneweight':
                    #each access to this array will have another array with a list of bone weights
                    boneweights = []
                    
                    #check to see if amount of weights are above limit
                    if isbonesubmeshweightcountunsupported == False:
                        if len(currsubmesh.data.vertices[v_idx].groups) > 4:
                            isbonesubmeshweightcountunsupported = True
                            
                    for group in currsubmesh.data.vertices[v_idx].groups:
                        
                        boneweights.append(group.weight / attr.scale)
                    # add the weights that are zero for stuff that got deleted?
                    for x in range(attr.elements - len(boneweights)):
                        boneweights.append(float(0))
                    values.append(boneweights)
                    
                if attr_name == 'boneindex':
                    boneindicesindex = []
                    for group in currsubmesh.data.vertices[v_idx].groups:
                        #blender bone index name
                        name = currsubmesh.vertex_groups[group.group].name
                        #match up to gfbone order which(might?) not be the same
                        #also updating boneindices because the buffer references the index of the boneindices instead of just the bones(convoluted)
                        #this also means you can't have more than 31 bones acting on said submesh as a result
                        index = 0
                        for x in range(len(gfbones)):
                            if gfbones[x].bonename == name:
                                index = x 
                                #indices are added in order found in buffer? doesn't really matter anyway as long as the boneindice and buffer index to boneindices are consistent
                                if (index not in boneindices):
                                    if(len(boneindices) < 20):
                                        boneindices.append(index)
                                        boneindicesindex.append(len(boneindices)-1)
                                    else:
                                        isbonesubmeshcountunsupported = True
                                else:
                                    for x in range(len(boneindices)):      
                                        if (boneindices[x] == index):                                       
                                           boneindicesindex.append(x)

                    # add the weights that are zero
                    #should be 0th element for said submeshes boneindex, not just 0 overall
                    for x in range(attr.elements - len(boneindicesindex)):
                        boneindicesindex.append(0xFF)
                    values.append(boneindicesindex)
                
            
                # Write the elements for this attribute
                for e in range(attr.elements):
                    if attr.attribformat.name == "Float":
                        # why does struct use tuples lmao
                        value = struct.pack('f', values[0][e])
                        newrawbuffer.write(value)
                    elif attr.attribformat.name == "Short": 
                        value = struct.pack('h', values[0][e])
                        newrawbuffer.write(value)
                    elif attr.attribformat.name == "Ubyte":
                        value = struct.pack('B', int(values[0][e]))
                        newrawbuffer.write(value)
                    elif attr.attribformat.name == "Byte":
                        value = struct.pack('b', int(values[0][e]))
                        newrawbuffer.write(value)
                
 
            
                # Store the data by attribute name
                vertex_data[attr_name] = elements
                
        gfmeshdata.GFSubMeshes.GFSubMeshes[x1].gfsubmeshpart1.boneindicescount = len(boneindices)        
        #add padding for boneindices        
        for x in range(31 - len(boneindices)):
            boneindices.append(0)
        # changin nothing for fixattr for now they will just remain as they were for said model
        for fixattr in fixedattributes:
            fixattrname = fixattr.name.name.lower()
            #put first boneindex in boneindices for first attribute
            
            if (len(currsubmesh.vertex_groups) > 0): 
                name = currsubmesh.vertex_groups[0].name
                for x in range(len(gfbones)):
                    if gfbones[x].bonename == name:
                        index = x
                if (fixattrname == "boneindex"):
                    boneindices[0] = index
            else:
                boneindices[0] = 0xFF 
            
        gfmeshdata.GFSubMeshes.GFSubMeshes[x1].gfsubmeshpart2.rawbuffer = None
        gfmeshdata.GFSubMeshes.GFSubMeshes[x1].gfsubmeshpart2.rawbuffer = newrawbuffer
        
        gfmeshdata.GFSubMeshes.GFSubMeshes[x1].gfsubmeshpart1.verticescount = num_vertices
        gfmeshdata.GFSubMeshes.GFSubMeshes[x1].gfsubmeshpart1.verticeslength = len(newrawbuffer.getvalue())
        
        gfmeshdata.GFSubMeshes.GFSubMeshes[x1].gfsubmeshpart1.boneindices = boneindices
    
    #bounding box model calc
    if modelmaxx < maxx:
        modelmaxx = maxx
    if modelmaxy < maxy:
        modelmaxy = maxy
    if modelmaxz < maxz:
        modelmaxz = maxz
    if minx < modelminx:
        modelminx = minx
    if miny < modelminy:
        modelminy = miny
    if minz < modelminz:
        modelminz = minz
        
    newboundingboxminvector = Vector4.__new__(Vector4)
    newboundingboxminvector.__init2__(minx,miny,minz,1.0)     
    gfmeshdata.boundingboxminvector = newboundingboxminvector
    
    newboundingboxmaxvector = Vector4.__new__(Vector4)
    newboundingboxmaxvector.__init2__(maxx,maxy,maxz,1.0)     
    gfmeshdata.boundingboxmaxvector = newboundingboxmaxvector
    
    
   
   

def repackindices(submeshes, gfmeshdata):
    #this should be right... maybe?
    #tris only 
    for x in range(len(submeshes)):
        new_indices_buffer = io.BytesIO()
        for tri in submeshes[x].data.loop_triangles:
            indices = tri.vertices[:]
            new_indices_buffer.write(struct.pack('h', indices[0]))
            new_indices_buffer.write(struct.pack('h', indices[1]))
            new_indices_buffer.write(struct.pack('h', indices[2]))       
        gfmeshdata.GFSubMeshes.GFSubMeshes[x].gfsubmeshpart2.indices = new_indices_buffer
        gfmeshdata.GFSubMeshes.GFSubMeshes[x].gfsubmeshpart1.indicescount = len(submeshes[x].data.loop_triangles)*3
        gfmeshdata.GFSubMeshes.GFSubMeshes[x].gfsubmeshpart1.indiceslength = len(new_indices_buffer.getvalue())

    
def recreate_gfmodel_data(coll, gfmodel):
        global modelmaxx
        global modelmaxy
        global modelmaxz
        global modelminx
        global modelminy
        global modelminz
        global isbonecountunsupported

        #create new hashnames for new meshes
        meshnamelist = []
        for obj in coll.objects:
            if obj.type == 'MESH' and not 'submesh' in obj.name:
                #making sure submeshes aren't included
                meshname = obj.name
                meshnamelist.append(obj.name)              
        newmeshnames = GFHashName.__new__(GFHashName)
        newmeshnames.__init2__(meshnamelist) 
        gfmodel.meshnames = newmeshnames
        

        #re-create gfbones
        newgfbones = []
        for obj in coll.objects:
            if obj.type == 'ARMATURE':
                arm = obj.data
                if len(arm.bones) > 110:
                    isbonecountunsupported = True
                for bone in arm.bones:                   
                    if bone.parent == None:
                        tempnewGFBone = GFBone.__new__(GFBone)
                        translationvec = bone.head
                        rotation = bone.matrix.to_4x4()  # convert 3x3 to 4x4
                        full_matrix = Matrix.Translation(translationvec) @ rotation
                        
                        #rotation will be zerod out for unparented ones until i figure out how RotateObj affects armatures
                        tempnewGFBone.__init2__(bone.name,"placeholder",1.0,1.0,1.0,0.0,0.0,0.0,full_matrix.to_translation().x,full_matrix.to_translation().y,full_matrix.to_translation().z)
                        newgfbones.append(tempnewGFBone)
                    else:
                        key = arm.bones.find(bone.parent.name)
                        if(key != -1):
                            parentbone = arm.bones[bone.parent.name]                                        
                        bonematrix = bone.matrix_local.to_4x4()  # convert 3x3 to 4x4
                        parentmatrix = parentbone.matrix_local.to_4x4() 
                        combmatrix = parentmatrix.inverted() @ bonematrix       
                              
                        tempnewGFBone = GFBone.__new__(GFBone)
                        tempnewGFBone.__init2__(bone.name,parentbone.name,1.0,1.0,1.0,combmatrix.to_euler('XYZ').x,combmatrix.to_euler('XYZ').y,combmatrix.to_euler('XYZ').z,combmatrix.to_translation().x,combmatrix.to_translation().y,combmatrix.to_translation().z)
                        newgfbones.append(tempnewGFBone)
     
        gfmodel.GFBones = newgfbones
        gfmodel.bonescount = len(newgfbones)
                        
        #add/create new material stuff
        #for stuff that didn't already have material data we will need to also change matereialhash and picacommands values
        for obj in coll.objects:
            #find submeshes
            texturenames = []

            if obj.type == 'MESH':
                mat = obj.data.materials[0]
                #maybe change to find based on mesh name and not mat name in case people change material names
                gfmat = [mat1 for mat1 in gfmodel.GFMaterials if mat1.materialname.hashes[0][1] == mat.name.rsplit('.')[0]]    
                #edit/change texture coords
                tex_image_nodes = [node for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE']
                tex_coord_nodes = [node for node in mat.node_tree.nodes if node.type == 'MAPPING']
                textureuvmaps = [0,0,0]

                gfmat[0].unitscount = len(tex_coord_nodes)
                if (len(tex_coord_nodes) > 3):
                    gfmat[0].unitscount = 3        
                #set some default values just in case
                for x in range(gfmat[0].unitscount):
                    gfmat[0].coords[x].scale.X = (1.0,)
                    gfmat[0].coords[x].scale.Y = (1.0,)
                
                for x in range(len(tex_coord_nodes)):      
                    texturenames.append(tex_image_nodes[x].image.name)
                    if(tex_image_nodes[x].extension == 'CLIP'):
                        gfmat[0].coords[x].wrapu = GFTextureWrap.ClampToEdge
                    if(tex_image_nodes[x].extension == "REPEAT"):
                        gfmat[0].coords[x].wrapu = GFTextureWrap.Repeat
                    if(tex_image_nodes[x].extension == "MIRROR"):
                        gfmat[0].coords[x].wrapu = GFTextureWrap.Mirror
                    #to update uv map-> texture connection
                    for output in tex_image_nodes[x].outputs:
                        for link in output.links:
                            target_node = link.to_node
                            if target_node.type == 'MAPPING':    
                                vector_input = mapping_node.inputs['Vector']
                                if vector_input.is_linked:
                                    from_node = vector_input.links[0].from_node
                                    if from_node.type == 'UVMAP':
                                        uv_map_name = from_node.uv_map
                                        for x in mesh.data.uv_layers:
                                            if x.name == uv_map_name:
                                                textureuvmaps[x] = x
                            if target_node.type == 'UVMAP':       
                                uv_map_name = target_node.uv_map
                                for x in mesh.data.uv_layers:
                                    if x.name == uv_map_name:
                                        textureuvmaps[x] = x
                            
                for x in range(len(tex_coord_nodes)):          
                    gfmat[0].coords[x].rotation = (math.degrees(tex_coord_nodes[x].inputs['Rotation'].default_value[0]),)
                    # i love blender so-f-df-s-s-f- much!
                    gfmat[0].coords[x].translation.X = ((tex_coord_nodes[x].inputs['Location'].default_value[0])/2,)
                    gfmat[0].coords[x].translation.Y = ((tex_coord_nodes[x].inputs['Location'].default_value[1])/2,)            
                    gfmat[0].coords[x].scale.X = ((tex_coord_nodes[x].inputs['Scale'].default_value[0]),)
                    gfmat[0].coords[x].scale.Y = ((tex_coord_nodes[x].inputs['Scale'].default_value[1]),)                  
                #to update material texture uv map source  
                picacommands = PicaCommandReader(gfmat[0].picacommands)
                for x in range(len(picacommands.commands)):
                    if(picacommands.commands[x].register.name == "VSH_FLOATUNIFORM_DATA0"):
                        picacommands.commands[x].parameters[0] = struct.unpack('I', struct.pack('f', float(textureuvmaps[0])))
                    if(picacommands.commands[x].register.name == "VSH_FLOATUNIFORM_DATA1"):
                        picacommands.commands[x].parameters[0] = struct.unpack('I', struct.pack('f', float(textureuvmaps[1])))
                    if(picacommands.commands[x].register.name == "VSH_FLOATUNIFORM_DATA2"):
                        picacommands.commands[x].parameters[0] = struct.unpack('I', struct.pack('f', float(textureuvmaps[2])))
                #
            newtexturenames = GFHashName.__new__(GFHashName)
            newtexturenames.__init2__(texturenames) 
            gfmodel.texturenames = newtexturenames
        
        #re-create meshes
        for obj in coll.objects:
            defaultvaluesmesh = gfmodel.GFMeshes[0]
            newmeshes = []
            submsh_idx = 0
            if obj.type == 'MESH' and not 'submesh' in obj.name:
                mesh = obj
                ogmesh = None
                meshesfound = []
                submeshesfound1 = []
                for obj in coll.objects:
                    if obj.type == 'MESH':
                        submeshnme = obj.name+"submesh"
                        if (submeshnme in obj.name):
                            submeshesfound1.append(obj.name)
                submesh_name = obj.name.rsplit('submesh')[0]
                mesh_name = obj.name.rsplit('.')[0]
                for x in range(len(gfmodel.GFMeshes)):
                    ##UPDATE THIS
                    ##the blender mesh names are based on submesh names not mesh names and they don't always match up meaning i need to actually check submesh names
                    print(submesh_name)
                    print(mesh_name)
                    print(gfmodel.GFMeshes[x].namestr.strip('\x00'))
                    if mesh_name in gfmodel.GFMeshes[x].namestr.strip('\x00') :
                        meshesfound.append(mesh_name)
                        ogmesh = gfmodel.GFMeshes[x]

                if(ogmesh == None):
                    print("Could not find original mesh for "+obj.name)
                    
                else:
                    #check to make sure it's not actually a submesh

                    gfmesh = ogmesh
                    gfmesh.namestr = obj.name+"_OptMesh"
                    hasher = GFNV1()
                    hasher.hashstring(obj.name)
                    gfmesh.namehash = (hasher.hashcode.value).to_bytes(4, 'little')
                    blendersubmeshes = []
                    blendersubmeshes.append(mesh)
                    blendersubmeshes = [node for node in submeshesfound1 if node.type == 'MESH']
                    gfmesh.submeshescount = len(blendersubmeshes)
                        
                    #convoluted way to obtain the correct value for this
                    if len(obj.vertex_groups) > 0:
                        maxcount = 0
                        for v in obj.data.vertices:
                            count = 0
                            for g in v.groups:
                                weight = g.weight
                                if (weight > 0):
                                    count = count + 1
                                else:
                                    break
                            if count > maxcount:
                                maxcount = count                                                            
                        gfmesh.boneindicespervertex = maxcount
                    else:
                        gfmesh.boneindicespervertex = 0
                    
                    #change index commands that need to update
                    for x in range(gfmesh.submeshescount):
                        indexcommands = gfmesh.GFMeshCommandses[(3*submsh_idx)+2].commands
                        picacommands2 = PicaCommandReader(indexcommands)
                        for x in range(len(picacommands2.commands)):
                            if(picacommands2.commands[x].register.name == "GPUREG_NUMVERTICES"):
                                picacommands2.commands[x].parameters[0] = len(obj.data.polygons)*3
                            if(picacommands2.commands[x].register.name == "GPUREG_INDEXBUFFER_CONFIG"):
                                picacommands2.commands[x].parameters[0] = 0x81999999
                         
                        #set to new commands
                        gfmesh.GFMeshCommandses[(3*submsh_idx)+2].commands = picacommands2.serialize_commands()
                        gfmesh.GFMeshCommandses[(3*submsh_idx)+2].commandslength = (len(gfmesh.GFMeshCommandses[(3*submsh_idx)+2].commands))*4 
                    
                    #recreate rawbuffer and indices
                    repackvertexdata(blendersubmeshes, gfmesh, gfmodel.GFBones)
                    repackindices(blendersubmeshes, gfmesh)
                
                submsh_idx = submsh_idx + 1
                
        newboundingboxminvector = Vector4.__new__(Vector4)
        newboundingboxminvector.__init2__(modelminx,modelminy,modelminz,1.0)     
        gfmodel.boundingboxminvector = newboundingboxminvector

        newboundingboxmaxvector = Vector4.__new__(Vector4)
        newboundingboxmaxvector.__init2__(modelmaxx,modelmaxy,modelmaxz,1.0)     
        gfmodel.boundingboxmaxvector = newboundingboxmaxvector

def create_gfmaterial_data(coll, gfmodel, mesh, materialnames, shadernames, texturenames):
    material = mesh.data.materials[0]
    if 'submesh' not in mesh.name and mesh.name not in materialnames:
        materialnames.append(mesh.name.rsplit('\x00'))
        gfmaterialdata = GFMaterial.__new__(GFMaterial)
        newmaterialname = GFHashName2.__new__(GFHashName2)
        newmaterialname.__init2__(mesh.name.rsplit('\x00'))      
        #the frag/vert shader will have to be exported with files
        newfragshadername = GFHashName2.__new__(GFHashName2)
        newfragshadername.__init2__("Map00_default_AGREF")       
        newvertshadername = GFHashName2.__new__(GFHashName2)
        newvertshadername.__init2__("Default")
        gfmaterialdata.materialname = newmaterialname
        gfmaterialdata.shadername = newfragshadername
        gfmaterialdata.fragshadername = newfragshadername
        gfmaterialdata.vtxshadername = newvertshadername
        gfmaterialdata.luthash0id = 0
        gfmaterialdata.luthash1id = 0
        gfmaterialdata.luthash2id = 0
        #bumptexture is seemingly the index for normal maps which i'm not allowing here yet
        gfmaterialdata.bumptexture = -1
        gfmaterialdata.constant0assignment = 0
        gfmaterialdata.constant1assignment = 0
        gfmaterialdata.constant2assignment = 0
        gfmaterialdata.constant3assignment = 0
        gfmaterialdata.constant4assignment = 0
        gfmaterialdata.constant5assignment = 0
        newconstcolor = RGBA.__new__(RGBA)
        newconstcolor.__init2__(255,255,255,255)
        gfmaterialdata.constant0color = newconstcolor
        gfmaterialdata.constant1color = newconstcolor
        gfmaterialdata.constant2color = newconstcolor
        gfmaterialdata.constant3color = newconstcolor
        gfmaterialdata.constant4color = newconstcolor
        gfmaterialdata.constant5color = newconstcolor
        gfmaterialdata.specular0color = newconstcolor
        gfmaterialdata.specular1color = newconstcolor
        gfmaterialdata.blendcolor = newconstcolor
        gfmaterialdata.emissioncolor = newconstcolor
        gfmaterialdata.ambientcolor = newconstcolor
        gfmaterialdata.diffusecolor = newconstcolor
        gfmaterialdata.edgetype = 0
        gfmaterialdata.idedgeenable = 0
        gfmaterialdata.edgeid = 0
        gfmaterialdata.projectiontype = 0
        gfmaterialdata.rimpower = (8.0,)
        gfmaterialdata.rimscale = (1.0,)
        gfmaterialdata.phongpower = (8.0,)
        gfmaterialdata.phongpower = (8.0,)
        gfmaterialdata.phongscale = (1.0,)
        gfmaterialdata.idedgeoffsetenable = 1
        gfmaterialdata.edgemapalphamask = -1
        gfmaterialdata.baketexture0 = 0
        gfmaterialdata.baketexture1 = 0
        gfmaterialdata.baketexture2 = 0
        gfmaterialdata.bakeconstant0 = 0
        gfmaterialdata.bakeconstant1 = 0
        gfmaterialdata.bakeconstant2 = 0
        gfmaterialdata.bakeconstant3 = 0
        gfmaterialdata.bakeconstant4 = 0
        gfmaterialdata.bakeconstant5 = 0
        gfmaterialdata.vertexshadertype = 0
        gfmaterialdata.shaderparam0 = (1.0,)
        gfmaterialdata.shaderparam1 = (1.0,)
        gfmaterialdata.shaderparam2 = (1.0,)
        gfmaterialdata.shaderparam3 = (1.0,)
        gfmaterialdata.coords = []
        
        texcoordcount = 0
        #texcoord section
        tex_image_nodes = [node for node in material.node_tree.nodes if node.type == 'TEX_IMAGE'][:3]
        tex_coord_nodes = [node for node in material.node_tree.nodes if node.type == 'MAPPING'][:3]
        gfmaterialdata.unitscount = len(tex_image_nodes)
        textureuvmaps = [0,0,0]
        if (len(tex_coord_nodes) > 3):
            gfmaterialdata.unitscount = 3        
        for x in range(gfmaterialdata.unitscount):
            newtexcoord = GFTextureCoord.__new__(GFTextureCoord)
            newtexcoord.__init2__()
            newtexcoord.translation.X = (0.0,)
            newtexcoord.translation.Y = (0.0,)
            newtexcoord.scale.X = (1.0,)
            newtexcoord.scale.Y = (1.0,)
            newtexcoord.unitindex = x
            gfmaterialdata.coords.append(newtexcoord)
        for x in range(len(tex_image_nodes)):           
            #print([i.name for i in tex_coord_nodes[x].inputs])
            #print([i.enabled for i in tex_coord_nodes[x].inputs])
            
            #add materials found in tex image nodes to texture list
            if tex_image_nodes[x].image.name not in texturenames:
                texturenames.append(tex_image_nodes[x].image.name)
            texnamehash = GFHashName2.__new__(GFHashName2)
            texnamehash.__init2__(tex_image_nodes[x].image.name)
            gfmaterialdata.coords[x].texturename = texnamehash
            if(tex_image_nodes[x].extension == 'CLIP'):
                gfmaterialdata.coords[x].wrapu = GFTextureWrap.ClampToEdge
                gfmaterialdata.coords[x].wrapv = GFTextureWrap.ClampToEdge
            if(tex_image_nodes[x].extension == "REPEAT"):
                gfmaterialdata.coords[x].wrapu = GFTextureWrap.Repeat
                gfmaterialdata.coords[x].wrapv = GFTextureWrap.Repeat
            if(tex_image_nodes[x].extension == "MIRROR"):
                gfmaterialdata.coords[x].wrapu = GFTextureWrap.Mirror
                gfmaterialdata.coords[x].wrapv = GFTextureWrap.Mirror
            #maybe make the formatting better  
            #get the uvmap index for the vtxuniforms
            for output in tex_image_nodes[x].outputs:
                for link in output.links:
                    target_node = link.to_node
                    if target_node.type == 'MAPPING':    
                        vector_input = mapping_node.inputs['Vector']
                        if vector_input.is_linked:
                            from_node = vector_input.links[0].from_node
                            if from_node.type == 'UVMAP':
                                uv_map_name = from_node.uv_map
                                for x in mesh.data.uv_layers:
                                    if x.name == uv_map_name:
                                        textureuvmaps[x] = x
                    if target_node.type == 'UVMAP':       
                        uv_map_name = target_node.uv_map
                        for x in mesh.data.uv_layers:
                            if x.name == uv_map_name:
                                textureuvmaps[x] = x
                                
            print("textureuvmaps")
            print(textureuvmaps)
      
        for x in range(len(tex_coord_nodes)):          
            gfmaterialdata.coords[x].rotation = (math.degrees(tex_coord_nodes[x].inputs['Rotation'].default_value[0]),)
            # i love blender so-f-df-s-s-f- much!
            gfmaterialdata.coords[x].translation.X = ((tex_coord_nodes[x].inputs['Location'].default_value[0])/2,)
            gfmaterialdata.coords[x].translation.Y = ((tex_coord_nodes[x].inputs['Location'].default_value[1])/2,)            
            gfmaterialdata.coords[x].scale.X = (tex_coord_nodes[x].inputs['Scale'].default_value[0],)
            gfmaterialdata.coords[x].scale.Y = (tex_coord_nodes[x].inputs['Scale'].default_value[1],)
            
        #tex coord matrix for vertex shaders??(idk really)
        texmatrix = []
        for x in range(gfmaterialdata.unitscount):
            matrix = gfmaterialdata.coords[x].gettransform()
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a41[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a31[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a21[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a11[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a42[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a32[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a22[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a12[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a43[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a33[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a23[0]))[0])
            texmatrix.append(struct.unpack('I', struct.pack('f', matrix.a13[0]))[0])
            
        print("texmatrix")
        print(texmatrix)
        #will need to create new picacommands here
        picacommands = []
        #around 31 commands
        #params based off either spica or values found in models
        
        #the float uniform data here is purely for the uv map 'pointer' for a texture stage
        #though the parameter value is a float, it must be treated as a uint so the index goes from int to float to uint
        commandtexsources = [2147483648,0,textureuvmaps[2],textureuvmaps[1],textureuvmaps[0]]
        picacommands.append(PicaCommand(PicaRegisters(704),commandtexsources,15,True))
        picacommands.append(PicaCommand(PicaRegisters(704),[2147483649],15,False))
        if gfmaterialdata.unitscount > 0:    
            picacommands.append(PicaCommand(PicaRegisters(705),texmatrix,15,False))
        picacommands.append(PicaCommand(PicaRegisters(64),[2],15,False))
        picacommands.append(PicaCommand(PicaRegisters(256),[14942464],3,False))
        picacommands.append(PicaCommand(PicaRegisters(257),[16842752],15,False))
        picacommands.append(PicaCommand(PicaRegisters(260),[97],3,False))
        picacommands.append(PicaCommand(PicaRegisters(261),[4294967057],15,False))
        picacommands.append(PicaCommand(PicaRegisters(262),[512],15,False))
        picacommands.append(PicaCommand(PicaRegisters(263),[8017],15,False))
        picacommands.append(PicaCommand(PicaRegisters(109),[1],15,False))
        picacommands.append(PicaCommand(PicaRegisters(77),[12517376],15,False))
        picacommands.append(PicaCommand(PicaRegisters(273),[1],15,False))
        picacommands.append(PicaCommand(PicaRegisters(272),[1],15,False))
        picacommands.append(PicaCommand(PicaRegisters(274),[1],0,False))
        picacommands.append(PicaCommand(PicaRegisters(275),[1],15,False))
        picacommands.append(PicaCommand(PicaRegisters(276),[3],1,False))
        picacommands.append(PicaCommand(PicaRegisters(277),[3],1,False))
        texunitconfigbase = 12288  
        texunitconfigbase |= (1 if gfmaterialdata.unitscount > 0 else 0)
        texunitconfigbase |= (1 if gfmaterialdata.unitscount > 1 else 0)
        texunitconfigbase |= (1 if gfmaterialdata.unitscount > 2 else 0)
        picacommands.append(PicaCommand(PicaRegisters(128),[0,0,0],0,False))
        picacommands.append(PicaCommand(PicaRegisters(128),[texunitconfigbase],0,False))
        picacommands.append(PicaCommand(PicaRegisters(129),[0],15,False))
        picacommands.append(PicaCommand(PicaRegisters(145),[0],15,False))
        picacommands.append(PicaCommand(PicaRegisters(464),[35791394],15,False))
        picacommands.append(PicaCommand(PicaRegisters(465),[33554432],15,False))
        picacommands.append(PicaCommand(PicaRegisters(466),[0],15,False))
        print("material picacommands")
        picacommands2 = PicaCommandReader.__new__(PicaCommandReader)
        picacommands2.__init2__(picacommands)
        gfmaterialdata.picacommands = picacommands2.serialize_commands()
        gfmaterialdata.commandslength = len(gfmaterialdata.picacommands) << 2
        gfmaterialdata.renderpriority = 0
        #we have to make it binary bruh
        binaryhashcommands = io.BytesIO()
        for x in range(gfmaterialdata.commandslength >> 2):
            binaryhashcommands.write(gfmaterialdata.picacommands[x].to_bytes(4, 'little'))
        
        fnv = GFNV1.__init24__()
        fnv.HASH24(binaryhashcommands)
        #this hash is special..
        gfmaterialdata.materialhash = (fnv.hashcode.value >> 24)^(fnv.hashcode.value & 0x00FFFFFF)
        #should be constant
        gfmaterialdata.renderlayer = 0
        gfmaterialdata.reflectionidk = 3441483069
        #copy of lut hash ids
        gfmaterialdata.reflectionr = 0
        gfmaterialdata.reflectiong = 0
        gfmaterialdata.reflectionb = 0
        #end of commands section
        
        #check to only add unique materials

        return gfmaterialdata
            

def create_new_gfmodel_data(coll):
        global modelmaxx
        global modelmaxy
        global modelmaxz
        global modelminx
        global modelminy
        global modelminz
        
        #initialize new gfmodel 
        gfmodeldata = GFModel.__new__(GFModel)
        gfmodeldata.GFMeshes = []
        #add materials that are found in blender materials to list
        materialnames = []
        texturenames = []
        shadernames = []
    
    
        #create gfbones
        print(coll.name)
        newgfbones = []
        for obj in coll.objects:
            if obj.type == 'ARMATURE':
                arm = obj.data
                if len(arm.bones) > 110:
                    isbonecountunsupported = True
                for bone in arm.bones:
                    #print(bone.name)                      
                    if bone.parent == None:
                        tempnewGFBone = GFBone.__new__(GFBone)
                        translationvec = bone.head
                        rotation = bone.matrix.to_4x4()  # convert 3x3 to 4x4
                        full_matrix = Matrix.Translation(translationvec) @ rotation
                        
                        #rotation will be zerod out for unparented ones until i figure out how RotateObj affects armatures
                        tempnewGFBone.__init2__(bone.name,"placeholder",1.0,1.0,1.0,0.0,0.0,0.0,full_matrix.to_translation().x,full_matrix.to_translation().y,full_matrix.to_translation().z)
                        newgfbones.append(tempnewGFBone)
                    else:
                        key = arm.bones.find(bone.parent.name)
                        if(key != -1):
                            parentbone = arm.bones[bone.parent.name]                                        
                        bonematrix = bone.matrix_local.to_4x4()  # convert 3x3 to 4x4
                        parentmatrix = parentbone.matrix_local.to_4x4() 
                        combmatrix = parentmatrix.inverted() @ bonematrix       
                              
                        tempnewGFBone = GFBone.__new__(GFBone)
                        tempnewGFBone.__init2__(bone.name,parentbone.name,1.0,1.0,1.0,combmatrix.to_euler('XYZ').x,combmatrix.to_euler('XYZ').y,combmatrix.to_euler('XYZ').z,combmatrix.to_translation().x,combmatrix.to_translation().y,combmatrix.to_translation().z)
                        newgfbones.append(tempnewGFBone)
        gfmodeldata.GFBones = newgfbones
        gfmodeldata.bonescount = len(newgfbones)
        
        gfmodeldata.lutsCount = 0
        gfmodeldata.lutslength = 0
        
        #create new hashnames for new meshes
        meshnamelist = []
        submeshesfound1 = []
        submesh_name = "placeholder"
        mesh_name = "placeholder"
        for obj in coll.objects:
            if obj.type == 'MESH':
                #making sure submeshes aren't included
                print("name checks")
                print(obj.name)
                print(('-' not in obj.name and 'submesh' not in obj.name))
                if ('-' not in obj.name and 'submesh' not in obj.name):
                    mesh_name = obj.name+"_OptMesh"
                    if mesh_name not in meshnamelist:
                        meshnamelist.append(mesh_name)
                else:
                    print('-' in obj.name)
                    if '-' in obj.name:
                        mesh_name = blendersubmeshes[x].name.rsplit('-')[1]
                        submeshesfound1.append(obj.name)
                        if mesh_name not in meshnamelist:
                            meshnamelist.append(mesh_name) 
                    else:
                        submeshesfound1.append(obj.name)
        newmeshnames = GFHashName.__new__(GFHashName)
        newmeshnames.__init2__(meshnamelist) 
        gfmodeldata.meshnames = newmeshnames
        shadernames.append("Map00_default_AGREF")
        print("len meshname list")
        print(len(meshnamelist))
        print(submeshesfound1)
        
        #create new meshes and materials
        gfmodeldata.GFMaterials = []
        newmeshes = []
        submsh_idx = 0
        for obj in coll.objects:
            submeshesfound = []
            if obj.type == 'MESH' and not obj.name in submeshesfound1:
                mesh = obj
                ogmesh = None
                submeshnamelist = []
                newgfmesh = GFMesh.__new__(GFMesh)
                newgfmesh.GFMeshCommandses = []
                submesh_name = obj.name
                mesh_name2 = ""
                print("submesh name")
                print(submesh_name)
                #create material for mesh
                gfmat = create_gfmaterial_data(coll, gfmodeldata, mesh, materialnames, shadernames, texturenames)
                    
                if ('-' not in obj.name):
                    mesh_name2 = obj.name+"_OptMesh"
                else:
                    if '-' in obj.name:
                        mesh_name2 = blendersubmeshes[x].name.rsplit('-')[1]    
                    
                gfmodeldata.GFMaterials.append(gfmat)
                   
                   
                #check to make sure it's not actually a submesh
                if (obj.name in submeshesfound1) == False:
                    newgfmesh.namestr = mesh_name2
                    hasher = GFNV1()
                    hasher.hashstring(mesh_name2)
                    newgfmesh.namehash = (hasher.hashcode.value).to_bytes(4, 'little')
                    blendersubmeshes = [node for node in coll.objects if node.type == 'MESH' and submesh_name in node.name]
                        
                newgfmesh.submeshescount = len(blendersubmeshes)
                    
                #get submesh names
                for x in range(len(blendersubmeshes)):  
                    if ('-' not in submesh_name and 'submesh' not in submesh_name):
                        submeshnamelist.append(submesh_name)
                    else:
                        if '-' in obj.name:
                            submesh_name = blendersubmeshes[x].name.rsplit('-')[0]
                            submeshnamelist.append(submesh_name)
                        else:
                            submesh_name = blendersubmeshes[x].name.rsplit('submesh')[0]
                            submeshnamelist.append(submesh_name)
                print("submeshnames")
                print(submeshnamelist)
                print(len(blendersubmeshes))
                
                #convoluted way to obtain the correct value for boneindicespervertex
                areallweightssame = True
                maxcount = 0
                firstweights = [0.0,0.0,0.0,0.0]
                if obj.vertex_groups:
                    firstweight = obj.data.vertices[0].groups[0].weight
                    firstweights[0] = firstweight
                    if len(obj.data.vertices[0].groups) > 1:
                        secondweight = obj.data.vertices[0].groups[1].weight
                        firstweights[1] = secondweight
                    if len(obj.data.vertices[0].groups) > 2:    
                        thirdweight = obj.data.vertices[0].groups[2].weight
                        firstweights[2] = thirdweight
                    if len(obj.data.vertices[0].groups) > 3:
                        fourthweight = obj.data.vertices[0].groups[3].weight
                        firstweights[3] = fourthweight
                    for v in obj.data.vertices:
                        count = 0
                        groupindex = 0
                        for g in v.groups:
                            if groupindex < len(obj.data.vertices[0].groups):
                                weight = g.weight  
                                if (weight != obj.data.vertices[0].groups[groupindex].weight):
                                    areallweightssame = False
                                if (weight > 0):
                                    count = count + 1
                            groupindex = groupindex + 1                               
                        if count > maxcount:
                            maxcount = count
                else:
                    areallweightssame = False
                            
                areallindicessame = True
                firstgroups = [0,0,0,0]
                if obj.vertex_groups:
                    firstgroup = obj.data.vertices[0].groups[0].group
                    firstgroups[0] = firstgroup
                    if len(obj.data.vertices[0].groups) > 1:
                        secondgroup = obj.data.vertices[0].groups[1].group
                        firstgroups[1] = secondgroup
                    if len(obj.data.vertices[0].groups) > 2:
                        thirdgroup = obj.data.vertices[0].groups[2].group
                        firstgroups[2] = thirdgroup
                    if len(obj.data.vertices[0].groups) > 3:
                        fourthgroup = obj.data.vertices[0].groups[3].group
                        firstgroups[3] = fourthgroup
                    print(v.groups)
                    for v in obj.data.vertices:
                        if len(v.groups) > 0:
                            group = v.groups[0]
                            for g in v.groups:
                                if (g.group != group):
                                    areallindicessame = False
                                    break 
                else:
                    areallindicessame = False
                                        
                newgfmesh.boneindicespervertex = maxcount
                newgfmesh.commandscount = newgfmesh.submeshescount*3
                print("submesh counts")
                print(newgfmesh.submeshescount)
                print(blendersubmeshes)
                print(submeshnamelist)
                
                #initialize new submeshes
                newgfsubmeshes = GFSubMeshes.__new__(GFSubMeshes)
                newgfsubmeshes.__init2__(newgfmesh.submeshescount,submeshnamelist) 

                newgfmesh.GFSubMeshes = newgfsubmeshes
                        
                #create new attributes and meshcommands
                for x in range(newgfmesh.submeshescount):
                    currsubmesh = blendersubmeshes[x]
                    nouv0 = (len(currsubmesh.data.uv_layers) == 0)
                    nouv1 = (len(currsubmesh.data.uv_layers) < 2)
                    nouv2 = (len(currsubmesh.data.uv_layers) < 3)
                    #enable commands
                    attributes = []
                    fixedattributes = []
                    #very long if statement to determine attributes
                    if gfmodeldata.bonescount == 0:
                        boneindexfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                        #7 is bone index(set to 0 for meshes w/o )
                        boneindexfixedattribute.name = PicaAttributeName(7)
                        boneindexfixedattribute.value = PicaVectorFloat24()
                        fixedattributes.append(boneindexfixedattribute)

                        boneweightfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                        #8 is bone weight
                        boneweightfixedattribute.name = PicaAttributeName(8)
                        boneweightfixedattribute.value = PicaVectorFloat24()
                        boneweightfixedattribute.value.setx(0.0)
                        boneweightfixedattribute.value.sety(0.003921568)
                        boneweightfixedattribute.value.setz(0.007843137)
                        boneweightfixedattribute.value.setw(0.01176465)
                        fixedattributes.append(boneweightfixedattribute)
                    else:
                        if areallweightssame == True:
                            boneindexfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                            #7 is bone index
                            boneindexfixedattribute.name = PicaAttributeName(7)
                            boneindexfixedattribute.value = PicaVectorFloat24()
                            boneindexfixedattribute.value.setx(firstweights[0])
                            if len(obj.data.vertices[0].groups) > 1:
                                boneindexfixedattribute.value.sety(firstweights[1])
                            if len(obj.data.vertices[0].groups) > 2:
                                boneindexfixedattribute.value.setz(firstweights[2])
                            if len(obj.data.vertices[0].groups) > 3:
                                boneindexfixedattribute.value.setw(firstweights[3])
                            fixedattributes.append(boneindexfixedattribute)
                        if areallindicessame == True:
                            boneweightfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                            #8 is bone weight
                            boneweightfixedattribute.name = PicaAttributeName(8)
                            boneweightfixedattribute.value = PicaVectorFloat24()
                            boneweightfixedattribute.value.setx(firstgroups[0])
                            if len(obj.data.vertices[0].groups) > 1:
                                boneweightfixedattribute.value.sety(firstgroups[1])
                            if len(obj.data.vertices[0].groups) > 2:    
                                boneweightfixedattribute.value.setz(firstgroups[2])
                            if len(obj.data.vertices[0].groups) > 3:    
                                boneweightfixedattribute.value.setw(firstgroups[3])
                            fixedattributes.append(boneweightfixedattribute)
                            
                    if nouv0:
                        texcoordfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                        #4 is texcoord0
                        texcoordfixedattribute.name = PicaAttributeName(4)
                        texcoordfixedattribute.value = PicaVectorFloat24()
                        texcoordfixedattribute.value.setx(0.0)
                        texcoordfixedattribute.value.sety(0.0)
                        texcoordfixedattribute.value.setz(0.0)
                        texcoordfixedattribute.value.setw(1.0)
                        fixedattributes.append(texcoordfixedattribute)
                    if nouv1:
                        texcoordfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                        #5 is texcoord1
                        texcoordfixedattribute.name = PicaAttributeName(5)
                        texcoordfixedattribute.value = PicaVectorFloat24()
                        texcoordfixedattribute.value.setx(0.0)
                        texcoordfixedattribute.value.sety(0.0)
                        texcoordfixedattribute.value.setz(0.0)
                        texcoordfixedattribute.value.setw(1.0)
                        fixedattributes.append(texcoordfixedattribute)
                    if nouv2:
                        texcoordfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                        #6 is texcoord2
                        texcoordfixedattribute.name = PicaAttributeName(6)
                        texcoordfixedattribute.value = PicaVectorFloat24()
                        texcoordfixedattribute.value.setx(0.0)
                        texcoordfixedattribute.value.sety(0.0)
                        texcoordfixedattribute.value.setz(0.0)
                        texcoordfixedattribute.value.setw(1.0)
                        fixedattributes.append(texcoordfixedattribute)
                    if len(obj.data.vertex_colors) == 0:
                        colorfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                        #3 is color
                        colorfixedattribute.name = PicaAttributeName(3)
                        colorfixedattribute.value = PicaVectorFloat24()
                        colorfixedattribute.value.setx(1.0)
                        colorfixedattribute.value.sety(1.0)
                        colorfixedattribute.value.setz(1.0)
                        colorfixedattribute.value.setw(1.0)
                        fixedattributes.append(colorfixedattribute)
                    #you will have no choice on tangents for now
                    tanfixedattribute = PicaFixedAttribute.__new__(PicaFixedAttribute)
                    #2 is tangent
                    tanfixedattribute.name = PicaAttributeName(2)
                    tanfixedattribute.value = PicaVectorFloat24()
                    tanfixedattribute.value.setx(0.0)
                    tanfixedattribute.value.sety(0.0)
                    tanfixedattribute.value.setz(0.0)
                    tanfixedattribute.value.setw(1.0)
                    fixedattributes.append(tanfixedattribute)
                    
                    
                    #now on to regular attributes
                    positionattribute = PicaAttribute.__new__(PicaAttribute)
                    #0 is position
                    positionattribute.name = PicaAttributeName(0)
                    #3 is float
                    positionattribute.attribformat = PicaAttributeFormat(3)
                    positionattribute.elements = 3
                    positionattribute.scale = 1.0
                    attributes.append(positionattribute)
                    
                    #1 is normal
                    normalattribute = PicaAttribute.__new__(PicaAttribute)
                    normalattribute.name = PicaAttributeName(1)
                    normalattribute.attribformat = PicaAttributeFormat(3)
                    normalattribute.elements = 3
                    normalattribute.scale = 1.0
                    attributes.append(normalattribute)
                    
                    if(nouv0 == False):
                        #4 is texcoord0
                        texcoordattribute = PicaAttribute.__new__(PicaAttribute)
                        texcoordattribute.name = PicaAttributeName(4)
                        texcoordattribute.attribformat = PicaAttributeFormat(3)
                        texcoordattribute.elements = 2
                        texcoordattribute.scale = 1.0
                        attributes.append(texcoordattribute)
                    if(nouv1 == False):
                        #5 is texcoord1
                        texcoord1attribute = PicaAttribute.__new__(PicaAttribute)
                        texcoord1attribute.name = PicaAttributeName(5)
                        texcoord1attribute.attribformat = PicaAttributeFormat(3)
                        texcoord1attribute.elements = 2
                        texcoord1attribute.scale = 1.0
                        attributes.append(texcoord1attribute)
                    if(nouv2 == False):
                        #6 is texcoord2
                        texcoord2attribute = PicaAttribute.__new__(PicaAttribute)
                        texcoord2attribute.name = PicaAttributeName(6)
                        texcoord2attribute.attribformat = PicaAttributeFormat(3)
                        texcoord2attribute.elements = 2
                        texcoord2attribute.scale = 1.0
                        attributes.append(texcoord2attribute)
                    if areallweightssame == False:
                        boneweightattribute = PicaAttribute.__new__(PicaAttribute)
                        boneweightattribute.name = PicaAttributeName(8)
                        boneweightattribute.attribformat = PicaAttributeFormat(1)
                        boneweightattribute.elements = 4
                        boneweightattribute.scale = 0.003921569
                        attributes.append(boneweightattribute)
                    if areallindicessame == False:
                        boneindicesattribute = PicaAttribute.__new__(PicaAttribute)
                        boneindicesattribute.name = PicaAttributeName(7)
                        boneindicesattribute.attribformat = PicaAttributeFormat(1)
                        boneindicesattribute.elements = 4
                        boneindicesattribute.scale = 1.0
                        attributes.append(boneindicesattribute)
                    if len(obj.data.vertex_colors) > 0:
                        colorsattribute = PicaAttribute.__new__(PicaAttribute)
                        colorsattribute.name = PicaAttributeName(3)
                        colorsattribute.attribformat = PicaAttributeFormat(1)
                        colorsattribute.elements = 4
                        colorsattribute.scale = 0.003921569
                        attributes.append(colorsattribute)
                    print("fixedatt") 
                    for attribu in fixedattributes:
                        print(attribu.name.name)
                    print("att")     
                    for attribu in attributes:
                        print(attribu.name.name)    
                        
                    #calculate vertexstride
                    vertexstride = 0
                    for x in range(len(attributes)):
                        currattribute = attributes[x]
                        if currattribute.attribformat.name == "Byte":                             
                            vertexstride = vertexstride + (1*currattribute.elements) 
                        if currattribute.attribformat.name == "Ubyte":                             
                            vertexstride = vertexstride + (1*currattribute.elements)  
                        if currattribute.attribformat.name == "Short":                             
                            vertexstride = vertexstride + (2*currattribute.elements) 
                        if currattribute.attribformat.name == "Float":                             
                            vertexstride = vertexstride + (4*currattribute.elements)     
                        
                    #only now can we set the picacommands    
                    bufferformats = 0
                    bufferattributes = 0
                    bufferpermutation = 0
                    attributestotal = 0    
                    for x in range(len(attributes)):
                        currattribute = attributes[x]
                        shift = attributestotal*4
                        attribfmt = 0
                        attributestotal = attributestotal + 1
                        attribfmt = currattribute.attribformat.value
                        attribfmt |= ((currattribute.elements - 1) & 3) << 2
                        print("attribfmt")
                        print(attribfmt)
                        print(currattribute.name.name) 
                        print(currattribute.name.value)
                        
                        bufferformats |= attribfmt << shift
                        bufferpermutation |= currattribute.name.value << shift
                        bufferattributes |= x << shift
                        
                    bufferattributes |= (vertexstride & 0xff) << 48
                    bufferattributes |= len(attributes) << 60
                    for x in range(len(fixedattributes)):
                        currfixedattribute = fixedattributes[x]
                        bufferformats |= (1 << (48+attributestotal))
                        bufferpermutation |= (currfixedattribute.name.value << (attributestotal*4))
                        attributestotal = attributestotal + 1
                        print("bufferpermutation")
                        print(bufferpermutation)
                        print(currfixedattribute.name.name) 
                        print(currfixedattribute.name.value)
                        
                    bufferformats |= (attributestotal -1) << 60
                    enablecommands = []
                    enablecommands.append(PicaCommand(PicaRegisters(697),[(2684354560 |(attributestotal-1))],11,False))
                    enablecommands.append(PicaCommand(PicaRegisters(578),[(attributestotal-1)],1,False))
                    enablecommands.append(PicaCommand(PicaRegisters(699),[(ctypes.c_uint32(bufferpermutation >> 0)).value],15,False))
                    enablecommands.append(PicaCommand(PicaRegisters(700),[(ctypes.c_uint32(bufferpermutation >> 32)).value],15,False))
                    attribbufferslocation = []
                    #attribbufferslocation.append(1)
                    attribbufferslocation.append(0x03000000)
                    attribbufferslocation.append(ctypes.c_uint32(bufferformats >> 0).value)
                    attribbufferslocation.append(ctypes.c_uint32(bufferformats >> 32).value)
                    attribbufferslocation.append(0x99999999)
                    attribbufferslocation.append(ctypes.c_uint32(bufferattributes >> 0).value)
                    attribbufferslocation.append(ctypes.c_uint32(bufferattributes >> 32).value)
                    enablecommands.append(PicaCommand(PicaRegisters(512),attribbufferslocation,15,True))
                    for x in range(len(fixedattributes)):
                        currfixedattribute = fixedattributes[x]
                        scale = 1.0
                        if (currfixedattribute.name.name == "Color" or currfixedattribute.name.name == "BoneWeight"): 
                            scale = 0.0039215686
                        currfixedattribute.value.div(scale)    
                        fixedattribindex = []
                        #fixedattribindex.append(1)
                        fixedattribindex.append(len(fixedattributes)+x)
                        fixedattribindex.append(ctypes.c_uint32(currfixedattribute.value.Word0).value)
                        fixedattribindex.append(ctypes.c_uint32(currfixedattribute.value.Word1).value)
                        fixedattribindex.append(ctypes.c_uint32(currfixedattribute.value.Word2).value)
                        enablecommands.append(PicaCommand(PicaRegisters(562),fixedattribindex,15,True)) 
                    enablecommands2 = PicaCommandReader.__new__(PicaCommandReader)
                    enablecommands2.__init2__(enablecommands)
                    bufferdata = enablecommands2.serialize_commands()
                    enablecommandsobject = GFMeshCommands.__new__(GFMeshCommands)  
                    enablecommandsobject.__init2__(len(bufferdata)*4,len(newgfmesh.GFMeshCommandses),newgfmesh.submeshescount*3,bufferdata)
                    newgfmesh.GFMeshCommandses.append(enablecommandsobject)
                    
                    
                    #end of enable commands and start of disable commands
                    disablecommands = []
                    #locks position out of being a fixed attribute
                    disablecommands.append(PicaCommand(PicaRegisters(515),[0,0,0],15,True))
                    for x in range(12):
                        disablecommands.append(PicaCommand(PicaRegisters(517+(x*3)),[0],15,False))
                        fixattribindexbool = True
                        #double check this
                        for x2 in range(len(fixedattributes)):
                            if fixedattributes[x2].name.value == x:
                                fixattribindexbool = False
                        if fixattribindexbool == False:
                            disablecommands.append(PicaCommand(PicaRegisters(562),[x,0,0,0],15,True))       
                    disablecommands2 = PicaCommandReader.__new__(PicaCommandReader)
                    disablecommands2.__init2__(disablecommands)
                    bufferdata2 = disablecommands2.serialize_commands() 
                    disablecommandsobject = GFMeshCommands.__new__(GFMeshCommands)  
                    disablecommandsobject.__init2__(len(bufferdata2)*4,len(newgfmesh.GFMeshCommandses),newgfmesh.submeshescount*3,bufferdata2)
                    newgfmesh.GFMeshCommandses.append(disablecommandsobject)
                    
                    #end of disable commands and start of index commands
                    indexcommands = []
                    indexcommands.append(PicaCommand(PicaRegisters(607),[1],15,False))
                    #make sure to check this
                    indexcommands.append(PicaCommand(PicaRegisters(551),[0x81999999],15,False))
                    indexcommands.append(PicaCommand(PicaRegisters(552),[len(obj.data.polygons)*3],15,False))
                    indexcommands.append(PicaCommand(PicaRegisters(581),[0],1,False))
                    indexcommands.append(PicaCommand(PicaRegisters(559),[1],15,False))
                    indexcommands.append(PicaCommand(PicaRegisters(581),[1],1,False))
                    indexcommands.append(PicaCommand(PicaRegisters(561),[1],15,False))
                    #primitive mode locked to tris
                    indexcommands.append(PicaCommand(PicaRegisters(606),[0 << 8],8,False))
                    indexcommands.append(PicaCommand(PicaRegisters(606),[0 << 8],8,False))
                    indexcommands2 = PicaCommandReader.__new__(PicaCommandReader)
                    indexcommands2.__init2__(indexcommands)
                    rawbufferdata3 = indexcommands2.serialize_commands()
                    indexcommandsobject = GFMeshCommands.__new__(GFMeshCommands)  
                    indexcommandsobject.__init2__(len(rawbufferdata3)*4,len(newgfmesh.GFMeshCommandses),newgfmesh.submeshescount*3,rawbufferdata3)
                    newgfmesh.GFMeshCommandses.append(indexcommandsobject)
                    #omg it's finally done
                                
                    print("gfmesh commands length")          
                    print(len(newgfmesh.GFMeshCommandses))                         
                #get/set fixed attributes for writing
                for x in range(len(newgfmesh.GFSubMeshes.GFSubMeshes)):
                    newgfmesh.getfixedattributes(newgfmesh.GFSubMeshes.GFSubMeshes[x],x)
                #recreate rawbuffer and indices
                #print(len(blendersubmeshes))
                repackvertexdata(blendersubmeshes, newgfmesh, gfmodeldata.GFBones)
                repackindices(blendersubmeshes, newgfmesh)
                
                #update commands that need data from when after the rawbuffers have been made
                print("gfmesh commands length")          
                print(len(newgfmesh.GFMeshCommandses))  
                for x in range(newgfmesh.submeshescount):
                    indexcommands = newgfmesh.GFMeshCommandses[(3*x)+2].commands
                    picacommands2 = PicaCommandReader(indexcommands)
                    for x2 in range(len(picacommands2.commands)):
                        if(picacommands2.commands[x2].register.name == "GPUREG_NUMVERTICES"):
                            picacommands2.commands[x2].parameters[0] = newgfmesh.GFSubMeshes.GFSubMeshes[x].gfsubmeshpart1.indicescount
                     
                    #set to new commands
                    newgfmesh.GFMeshCommandses[(3*x)+2].commands = picacommands2.serialize_commands()
                    newgfmesh.GFMeshCommandses[(3*x)+2].commandslength = (len(newgfmesh.GFMeshCommandses[(3*x)+2].commands))*4 
                
                gfmodeldata.GFMeshes.append(newgfmesh)
                        
        newboundingboxminvector = Vector4.__new__(Vector4)
        newboundingboxminvector.__init2__(modelminx,modelminy,modelminz,1.0)     
        gfmodeldata.boundingboxminvector = newboundingboxminvector

        newboundingboxmaxvector = Vector4.__new__(Vector4)
        newboundingboxmaxvector.__init2__(modelmaxx,modelmaxy,modelmaxz,1.0)     
        gfmodeldata.boundingboxmaxvector = newboundingboxmaxvector
        
        gfmodeldata.transformmatrix = Matrix4x4.__new__(Matrix4x4)
        gfmodeldata.transformmatrix.__init2__(0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0)
        
        newmaterialnames = GFHashName.__new__(GFHashName)
        newmaterialnames.__init2__(materialnames) 
        gfmodeldata.materialnames = newmaterialnames
        newtexturenames = GFHashName.__new__(GFHashName)
        newtexturenames.__init2__(texturenames) 
        gfmodeldata.texturenames = newtexturenames
        newshadernames = GFHashName.__new__(GFHashName)
        newshadernames.__init2__(shadernames) 
        gfmodeldata.shadernames = newshadernames
        
        return gfmodeldata
    
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