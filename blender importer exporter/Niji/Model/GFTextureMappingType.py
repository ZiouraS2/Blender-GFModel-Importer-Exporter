from enum import Enum

#copied directly from SPICA

class GFTextureMappingType(Enum):         
        UvCoordinateMap = 0
        CameraCubeEnvMap = 1
        CameraSphereEnvMap = 2
        ProjectionMap = 3
        Shadow = 4
        ShadowBox = 5