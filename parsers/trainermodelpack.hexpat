u32 ogpos;
struct GFPackName {
    u8 NameLength;
    char Name[NameLength];
    ogpos = $;
    u32 fileoffset;
    
    $ = fileoffset;
    
    u32 start;
    $ = ogpos+4;
};  

struct filepack{
    u32 magic;
    u32 filecount1;
    u32 filecount2;
    u32 filecount3;
    u32 filecount4;
    u32 filecount5;
    u32 resourceidmaybe[filecount1+filecount2+filecount3+filecount4+filecount5];
    GFPackName names[filecount1+filecount2+filecount3+filecount4+filecount5];
};

filepack file @ 0x0;