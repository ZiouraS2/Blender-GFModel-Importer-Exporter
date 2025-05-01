from enum import Enum

#copied directly from SPICA

class GFTextureWrap(Enum):         
        ClampToEdge = 0
        ClampToBorder = 1
        Repeat = 2
        Mirror = 3