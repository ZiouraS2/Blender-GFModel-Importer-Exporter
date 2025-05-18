u32 ogpos;
struct GFPackName {
    ogpos = $;
    u32 fileoffset;
    
    $ = fileoffset+4;
    
    u32 start;
    $ = ogpos+4;
};  

struct filepack{
    u32 magic;
    GFPackName offsets[272];

};

filepack file @ 0x0;