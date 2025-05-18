import os
import sys
import mathutils
from . import helperfunctions
from mathutils import Vector


class UniformManager(object):   
    def __init__(self):
        self.uniforms = []
        for x in range(96):
            initvec = mathutils.Vector((0.0, 0.0, 0.0, 0.0))
            self.uniforms.append(initvec)
