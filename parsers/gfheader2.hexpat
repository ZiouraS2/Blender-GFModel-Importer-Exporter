import std.mem;
import std.core;

u32 ogpos;
u32 ogpos2;
u8 i3 = 0;

struct filepositions{
    u32 startaddress;
    u32 endaddress;
    
    ogpos = $ - 0x4;
    
    $ = startaddress + ogpos2;
    
    u32 start;
    $ = endaddress + ogpos2 - 0x4;
    u32 end;
    
    $ = ogpos;
};



fn checkfordups(filepositions pos){
        u8 magic1 @ pos[i3].startaddress;
        u8 magic2 @ pos[i3].startaddress + 0x1;
        if(magic1 < 0x5A && magic1 > 0x40){
            if(magic2 < 0x5A && magic2 > 0x40){
                std::print("true");
                return true;
            }else{
                return false;
            }
  
        }else{
            return false;
        }
  
};

struct header{
    ogpos2 = $;
    u16 magic;
    u16 entries;

    filepositions positions[entries];
    

};



struct extrapositions<T, auto pos>{
     if(checkfordups(pos)){
        $ = pos[i3].startaddress;
        //$ = $ - 0x2;
        header headeer2;
     }
      i3 = i3+1;

};

struct files{
    u8 magic1;
    u8 magic2;
    if(magic1 < 0x5A && magic2 > 0x40){    
        $ = $ - 0x2;
        header headeer;
    }
     //check for subfolders, meaning most will be empty
     extrapositions<filepositions, headeer.positions> positions2[headeer.entries];
};

files files1 @ 0x0;
