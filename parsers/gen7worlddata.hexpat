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



struct header{
    filepositions positions;
    

};



struct first{
  u32 const1;
  u32 offset1;
  u32 offset2;
  u32 offset3;
  u32 value1;
  u32 value2;
  u32 padding1;
  $ = offset1+0x10;
  u8 data1[offset2 - offset1];
  $ = offset2+0x10;
  u8 data2[offset3 - offset2];
};

struct Vector3{
    float X;
    float Y;
    float Z;
};

struct second{
  u32 num1;
  u32 numofpositions;
  ogpos2 = $ - 0x8;
  header offsets[2+num1];

};

u32 off1 @ 0x4;
u32 off2 @ 0x8;

first f @ off1;
second s @ off2;