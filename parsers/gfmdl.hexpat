import std.string;
import std.mem;
import std.core;

s32 lutsLength;
u32 CommandsCount;
u32 SubMeshesCount1;
u32 i1;

enum GFFileType : u32 {
    gfModel = 0x15122117,
    gfTexture = 0x15041213,
    gfMotion = 0x00060000,
    allofthem = 0x14110100

};

fn check_bound() {
    if(($ & 0xF) != 0){
        return true; 
    }
    else{
        return false;
    }
};


struct skippadding {
    s8 array[while( ($[$] == 0))];


};

struct skippadding2 {
    s8 array[while($[$] == 0xFF)];


};

struct skippadding3 {
    if(($ & 0xF) != 0){
        u32 num = 0;
        num = (0x10 - ($ & 0xF));
        s8 array[num];
    }
    else{
        
    }
};

struct skippadding4 {
    if(($ & 0xF) != 0){
        u32 num = 0;
        num = (0x10 - ($ & 0xF));
        s8 array[num];
    }
    else{
        
    }
};

struct skippadding5 {
    if(($ & 0xF) != 0){
        u32 num = 0;
        num = (0x10 - ($ & 0xF));
        s8 array[num];
    }
    else{
        padding[16];
    }
};

struct TypeIdentifier {
    GFFileType gfFileType;
    u32 sectionscount;
    padding[8];
};

struct GFSection {
    char magic[8];
    u32 length;
    padding[4];
};


struct GFHashNameinside {
    u32 Hash;
    char Name[64];

};



struct GFHashName {
    u32 numberofhashes;
    GFHashNameinside Hash1[numberofhashes];
};

struct GFHashName2 {
    u32 Hash;
    u8 NameLength;
    char Name[NameLength];
};    
    
    
struct Vector4 {
    float X;
    float Y;
    float Z;
    float W;
};    
    
struct Vector2 {
    float X;
    float Y;
};    

struct Matrix {
    float a11;
    float a12;
    float a13;
    float a14;
    float a21;
    float a22;
    float a23;
    float a24;
    float a31;
    float a32;
    float a33;
    float a34;
    float a41;
    float a42;
    float a43;
    float a44;

};    

struct UnknownData {
    u32 unknownDataLength;
    u32 unknownDataOffset;
    padding[4];
};  

struct BonesCount {
    s32 bonesCount;
    padding[12];
};  

struct LutCount {
   
    s32 lutLength;



};

struct RGBA {
    u8 Alpha;
    u8 Blue;
    u8 Green;
    u8 Red;

};

struct GFTextureCoord {
    GFHashName2 name;
    u8 UnitIndex;
    u8 MappingType;
    Vector2 Scale;
    float Rotation;
    Vector2 Translation;
    u32 WrapU;
    u32 WrapV;
    u32 MagFilter;
    u32 MinFilter;
    u32 MinLOD;
    
};

struct GFMaterial {
    GFSection materialgfsection;
    GFHashName2 materialname;
    //padding[1];
    GFHashName2 shadername;
    GFHashName2 fragshadername;
    GFHashName2 vtxshadername;
    u32 LUT0HashId;
    u32 LUT1HashId;
    u32 LUT2HashId;
    padding[4];
    s8 BumpTexture;
    u8 Constant0Assignment;
    u8 Constant1Assignment;
    u8 Constant2Assignment;
    u8 Constant3Assignment;
    u8 Constant4Assignment;
    u8 Constant5Assignment;
    padding[1];
    RGBA Constant0Color;
    RGBA Constant1Color;
    RGBA Constant2Color;
    RGBA Constant3Color;
    RGBA Constant4Color;
    RGBA Constant5Color;
    RGBA Specular0Color;
    RGBA Specular1Color;
    RGBA BlendColor;
    RGBA EmissionColor;
    RGBA AmbientColor;
    RGBA DiffuseColor;
    s32 EdgeType;
    s32 IDEdgeEnable;
    s32 EdgeID;
    s32 ProjectionType;
    float RimPower;
    float RimScale;
    float PhongPower;
    float PhongScale;
    s32 IDEdgeOffsetEnable;
    s32 EdgeMapAlphaMask;
    s32 BakeTexture0;
    s32 BakeTexture1;
    s32 BakeTexture2;
    s32 BakeConstant0;
    s32 BakeConstant1;
    s32 BakeConstant2;
    s32 BakeConstant3;
    s32 BakeConstant4;
    s32 BakeConstant5;
    s32 VertexShaderType;
    float ShaderParam0;
    float ShaderParam1;
    float ShaderParam2;
    float ShaderParam3;
    s32 UnitsCount;
    //std::print("{}",UnitsCount);
    GFTextureCoord coords[UnitsCount];
    skippadding2;
    u32 CommandsLength;
    s32 RenderPriority;
    u32 idkman;
    s32 Renderlayer;
    RGBA ReflectionR;
    RGBA ReflectionG;
    RGBA ReflectionB;
    u32 Reflectionidk;  
    u32 Commands[(CommandsLength >> 2)];
    padding[16];
};

struct SubMeshSize {
    u32 VerticesCount; 
    u32 IndicesCount;
    u32 VerticesLength;
    u32 IndicesLength;

};

struct GFSubMesh1 {
    u32 SMNameHash;
    u32 StringLength;
    char SMName[StringLength];
    u8 BoneIndicesCount;
    u8 BoneIndices[31];
    u32 VerticesCount; 
    u32 IndicesCount;
    u32 VerticesLength;
    u32 IndicesLength;

};


fn readBuffers(GFSubMesh1 gfsubmesh) {
     
     for(u8 i = 0, i < std::core::member_count(gfsubmesh), i += 1) {
         u8 RawBuffer[gfsubmesh[i].VerticesLength];
         u8 Indices[gfsubmesh[i].IndicesLength];
     }

};



struct GFSubMesh2<T, auto tempGFSubMesh> {
   u8 RawBuffer[tempGFSubMesh[i1].VerticesLength];
   u8 Indices[tempGFSubMesh[i1].IndicesLength];
   i1 += 1;

};

struct GFMeshCommands1{
    u32 CommandsLength; 
    u32 CommandsIndex; 
    u32 CommandsCount1; 
    CommandsCount = CommandsCount1;
    padding[4];
    u32 Commands[(CommandsLength >> 2)];
};

struct GFMeshCommands{
    u32 CommandsLength; 
    u32 CommandsIndex; 
    u32 CommandsCount; 
    padding[4];
    u32 Commands[(CommandsLength >> 2)];
};

struct GFSubMesh{
   
    GFSubMesh1 gfsubmesh1[SubMeshesCount1];
    GFSubMesh2<GFSubMesh1, gfsubmesh1> gfsubmesh2[SubMeshesCount1];

};



struct GFMesh {
    GFSection meshgfsection;
    u32 NameHash;
    char NameStr[64];
    u32 skipped;
    Vector4 boundingboxminvector;
    Vector4 boundingboxmaxvector;  
    u32 SubMeshesCount;  
    SubMeshesCount1 = SubMeshesCount;
    u32 BoneIndicesPerVertex; 
    padding[16];
    GFMeshCommands1 commands;
    GFMeshCommands commands2[CommandsCount - 1];
    GFSubMesh gfsubmesh;
    skippadding;
    i1 = 0;
};

struct GFMesh1 {
    GFSection meshgfsection;
    u32 NameHash;
    char NameStr[64];
    u32 skipped;
    Vector4 boundingboxminvector;
    Vector4 boundingboxmaxvector;  
    u32 SubMeshesCount;  
    SubMeshesCount1 = SubMeshesCount;
    u32 BoneIndicesPerVertex; 
    padding[16];
    GFMeshCommands1 commands;
    GFMeshCommands commands2[CommandsCount - 1];
    GFSubMesh gfsubmesh;
    skippadding3;
    i1 = 0;
};

struct GFBone {
    u8 StringLength;
    char BoneName[StringLength];
    padding[1];
    u8 boneFlag;
    float ScaleX;
    float ScaleY;
    float ScaleZ;
    float RotationX;
    float RotationY;
    float RotationZ;
    float TranslationX;
    float TranslationY;
    float TranslationZ;

};

struct GFBone2 {
    u8 StringLength;
    char BoneName[StringLength];
    u8 StringLength2;
    char BoneParentName[StringLength2];
    u8 boneFlag;
    float ScaleX;
    float ScaleY;
    float ScaleZ;
    float RotationX;
    float RotationY;
    float RotationZ;
    float TranslationX;
    float TranslationY;
    float TranslationZ;

};

struct GFLUT {
    u32 HashId;
    padding[12];
    u32 picaCommand[lutsLength >> 2];
};


struct GFModel {
    TypeIdentifier typeindentifier;
    GFSection gfsection;
    //padding[8];
    GFHashName shadernames;
    GFHashName texturenames;
    GFHashName materialnames;
    GFHashName meshnames;
    Vector4 boundingboxminvector;
    Vector4 boundingboxmaxvector;
    Matrix transform;
    UnknownData unknowndata;
    padding[unknowndata.unknownDataOffset+unknowndata.unknownDataLength];
    padding[4];
    s32 bonescount;
    padding[12];
    
    if(bonescount > 0){
    GFBone originalgfbone;
    if(bonescount > 1){
    GFBone2 gfbone2[bonescount - 1];
    }
    }
    
    skippadding3;
    s32 lutsCount;
    s32 lutsLength1;
    lutsLength = lutsLength1;
    skippadding;
    
    if(lutsCount > 0){
    GFLUT gflut[lutsCount];
    }
    
    if(materialnames.numberofhashes > 0){
    GFMaterial gfmaterial[materialnames.numberofhashes];
    }
    
    if(meshnames.numberofhashes > 1){
    GFMesh gfmesh[meshnames.numberofhashes - 1];
    }
    if(meshnames.numberofhashes > 0){
    GFMesh1 gfmesh1[1];
    }

};


GFModel gfmodel @ 0x00000000;
