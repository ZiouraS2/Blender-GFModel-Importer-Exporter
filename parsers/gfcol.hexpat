struct values{
float PosX1[[color("FF0000")]];
float PosY1[[color("00FF00")]];
float PosZ1[[color("0000FF")]];
float PosW1;
float PosX2[[color("FF0000")]];
float PosY2[[color("00FF00")]];
float PosZ2[[color("0000FF")]];
float PosW2;
float PosX3[[color("FF0000")]];
float PosY3[[color("00FF00")]];
float PosZ3[[color("0000FF")]];
float PosW3;
float NormalX;
float NormalY;
float NormalZ;
float NormalW;
u32 collisionvalue;
float unknown;
};

struct among{
u32 header;
u32 numof;
values cool[numof];
};
among amo @ 0x0;