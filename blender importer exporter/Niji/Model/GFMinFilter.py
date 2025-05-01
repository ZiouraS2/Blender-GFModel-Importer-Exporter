from enum import Enum

#copied directly from SPICA

class GFMinFilter(Enum):         
        Nearest = 0
        NearestMipmapNearest = 1
        NearestMipmapLinear = 2
        Linear = 3
        LinearMipmapNearest = 4
        LinearMipmapLinear = 5