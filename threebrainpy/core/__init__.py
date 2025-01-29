from .constants import CONSTANTS
from .vec3 import Vec3
from .mat44 import Mat44
from .brain import Brain
from .keyframe import SimpleKeyframe
from .colormap import ElectrodeColormap
__all__ = ['Brain', 'Vec3', 'Mat44', 'SimpleKeyframe', 'CONSTANTS', 'ElectrodeColormap']

# Path: threeBrainPy/core/brain.py

"""Provide core classes and functions for threebrainpy

The module contains the following objects:

- `Brain` (class) - The main `threebrainpy` brain class definition.
- `Vec3` (class) - 3D point vector (position) within specified space.
- `Mat44` (class) - Affine matrix (4x4) for transforming 3D points.
- `SimpleKeyframe` (class) - Class definition for storing electrode animation keyframes.
- `CONSTANTS` (class singleton) - Class singleton instance for storing constants used in `threebrainpy`.
"""


# import