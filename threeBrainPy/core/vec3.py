import numpy as np
import json
from .mat44 import Mat44

class Vec3:
    '''
    Creates a 3D vector with given coordinate space.
    Args:
        x: x coordinate or a Vec3, or a list/tuple/array of 3 numbers.
        y: y coordinate or None if x is a Vec3 or a list/tuple/array of 3 numbers.
        z: z coordinate or None if x is a Vec3 or a list/tuple/array of 3 numbers.
        space: The space of the vector, either "ras", "ras_tkr", "mni305", "mni152" or "voxel". 
        
            > This is ignored if x is a Vec3 since the space will be the same as x.
            > In other situations, if space is None, the space will be "ras".

    '''
    def __init__(self, x : list | tuple | np.ndarray | float | None = None, 
                 y : float | None = None, z : float | None = None, space : str | None = None):
        self.space = "ras" if space is None else space
        if y is None or z is None or isinstance(x, Vec3):
            if x is None:
                self._xyz = np.array([ np.nan, np.nan, np.nan, 1.0 ], dtype=float)
            elif isinstance(x, Vec3):
                self._xyz = np.array([ x.x, x.y, x.z, 1.0 ], dtype=float)
                self.space = x.space
            elif isinstance(x, (list, tuple, np.ndarray)):
                x = np.array(x, dtype=float).reshape(-1)
                if x.size in (3, 4, ):
                    self._xyz = np.array([ x[0], x[1], x[2], 1.0 ], dtype=float)
                else:
                    raise ValueError(f"Vec3 init: x must be a Vec3 or can be converted into Vec3, but got {x}")
            elif isinstance(x, (int, float, str)):
                x = float(x)
                self._xyz = np.array([ x, x, x, 1.0 ], dtype=float)
            else:
                raise ValueError(f"Vec3 init: x must be a Vec3 or can be converted into float/Vec3, but got {x}")
        else:
            self._xyz = np.array([x, y, z, 1.0], dtype=float)
    
    @property
    def x(self):
        '''
        Get x coordinate.
        '''
        return self._xyz[0]
    @x.setter
    def x(self, value):
        self._xyz[0] = value

    @property
    def y(self):
        '''
        Get y coordinate.
        '''
        return self._xyz[1]
    @y.setter
    def y(self, value):
        self._xyz[1] = value

    @property
    def z(self):
        '''
        Get z coordinate.
        '''
        return self._xyz[2]
    @z.setter
    def z(self, value):
        self._xyz[2] = value
    
    def __str__(self):
        return f"Vec3({self.x}, {self.y}, {self.z}) [{ self.space }]"
    
    def __repr__(self):
        return str(self)
    
    def __add__(self, other):
        if isinstance(other, Vec3):
            if self.space != other.space:
                raise ValueError(f"Vec3 add: spaces must match, but got {self.space} and {other.space}")
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z, space = self.space)
        else:
            v = np.array(other, dtype=float)
            if v.size in (3, 4, ):
                return Vec3(self.x + v[0], self.y + v[1], self.z + v[2], space = self.space)
            else:
                raise ValueError(f"Vec3 add: other must be a Vec3 or can be converted into Vec3, but got {other}")
    
    def __sub__(self, other):
        if isinstance(other, Vec3):
            if self.space != other.space:
                raise ValueError(f"Vec3 sub: spaces must match, but got {self.space} and {other.space}")
            return Vec3(self.x - other.x, self.y - other.y, self.z - other.z, space = self.space)
        else:
            v = np.array(other, dtype=float)
            if v.size in (3, 4, ):
                return Vec3(self.x - v[0], self.y - v[1], self.z - v[2], space = self.space)
            else:
                raise ValueError(f"Vec3 sub: other must be a Vec3 or can be converted into Vec3, but got {other}")
    
    def __mul__(self, other):
        if isinstance(other, Vec3):
            if self.space != other.space:
                raise ValueError(f"Vec3 mul: spaces must match, but got {self.space} and {other.space}")
            return Vec3(self.x * other.x, self.y * other.y, self.z * other.z, space = self.space)
        else:
            v = np.array(other, dtype=float)
            if v.size in (3, 4, ):
                return Vec3(self.x * v[0], self.y * v[1], self.z * v[2], space = self.space)
            else:
                raise ValueError(f"Vec3 mul: other must be a Vec3 or can be converted into Vec3, but got {other}")
    
    def __truediv__(self, other):
        if isinstance(other, Vec3):
            if self.space != other.space:
                raise ValueError(f"Vec3 truediv: spaces must match, but got {self.space} and {other.space}")
            return Vec3(self.x / other.x, self.y / other.y, self.z / other.z, space = self.space)
        else:
            v = np.array(other, dtype=float)
            if v.size == 3 in (3, 4, ):
                return Vec3(self.x / v[0], self.y / v[1], self.z / v[2], space = self.space)
            else:
                raise ValueError(f"Vec3 truediv: other must be a Vec3 or can be converted into Vec3, but got {other}")
    
    def __floordiv__(self, other):
        if isinstance(other, Vec3):
            if self.space != other.space:
                raise ValueError(f"Vec3 floordiv: spaces must match, but got {self.space} and {other.space}")
            return Vec3(self.x // other.x, self.y // other.y, self.z // other.z, space = self.space)
        else:
            v = np.array(other, dtype=float)
            if v.size in (3, 4, ):
                return Vec3(self.x // v[0], self.y // v[1], self.z // v[2], space = self.space)
            else:
                raise ValueError(f"Vec3 floordiv: other must be a Vec3 or can be converted into Vec3, but got {other}")
    
    def to_list(self):
        '''
        Convert this vector into a list of 3 numbers.
        When the point is invalid, a list of 3 `9999.0` will be returned. 
        Points that far will be be rendered in the viewer
        '''
        if not np.isfinite(self.length()):
            return [9999.0, 9999.0, 9999.0]
        return [self.x, self.y, self.z]
    
    def to_tuple(self):
        '''
        Convert this vector into a tuple of 3 numbers.
        '''
        return tuple(self._xyz[:3])
    
    def copyFrom(self, other):
        '''
        Copy (in-place) the value of this vector from another vector or a list/tuple/array of 3 numbers.
        Args:
            other Vec3 | list | tuple | np.ndarray : The other vector or a list/tuple/array of 3 numbers.
        '''
        if isinstance(other, Vec3):
            self.space = other.space
            other = other._xyz
        else:
            other = np.array(other, dtype=float)
            if other.size not in (3, 4, ):
                raise ValueError(f"Vec3 copyFrom: other must be a Vec3 or can be converted into Vec3, but got {other}")
        self._xyz[0] = other[0]
        self._xyz[1] = other[1]
        self._xyz[2] = other[2]
        return self

    def applyMat44(self, mat44 : Mat44):
        '''
        Apply a 4x4 matrix to this vector in-place.
        Args:
            mat44: A 4x4 matrix 
        '''
        if isinstance(mat44, Mat44):
            if self.space != mat44.space_from:
                raise ValueError(f"Vec3 applyMatrix44: spaces must match, but got {self.space} and {mat44.space_from}")
            self.copyFrom(np.dot(mat44.mat, self._xyz))
            self.space = mat44.space_to
        else:
            raise ValueError(f"Vec3 applyMatrix44: mat44 must be a Mat44, but got {mat44}")
        return self
    
    def add(self, vec3):
        '''
        Add another vector to this vector in-place.
        Args:
            vec3 Vec3: Another vector.
        '''
        if isinstance(vec3, Vec3):
            if self.space != vec3.space:
                raise ValueError(f"Vec3 add: spaces must match, but got {self.space} and {vec3.space}")
            self._xyz[0] += vec3._xyz[0]
            self._xyz[1] += vec3._xyz[1]
            self._xyz[2] += vec3._xyz[2]
        else:
            raise ValueError(f"Vec3 add: vec3 must be a Vec3, but got {vec3}")
        return self
    
    def sub(self, vec3):
        '''
        Subtract another vector to this vector in-place.
        Args:
            vec3 Vec3: Another vector.
        '''
        if isinstance(vec3, Vec3):
            if self.space != vec3.space:
                raise ValueError(f"Vec3 sub: spaces must match, but got {self.space} and {vec3.space}")
            self._xyz[0] -= vec3._xyz[0]
            self._xyz[1] -= vec3._xyz[1]
            self._xyz[2] -= vec3._xyz[2]
        else:
            raise ValueError(f"Vec3 sub: vec3 must be a Vec3, but got {vec3}")
        return self
    
    def dot(self, vec3) -> float:
        '''
        Dot-product another vector to this vector.
        Args:
            vec3 Vec3: Another vector.
        Returns:
            float: The dot product of this vector and the other vector.
        '''
        if isinstance(vec3, Vec3):
            if self.space != vec3.space:
                raise ValueError(f"Vec3 dot: spaces must match, but got {self.space} and {vec3.space}")
            return self._xyz[0] * vec3._xyz[0] + self._xyz[1] * vec3._xyz[1] + self._xyz[2] * vec3._xyz[2]
        else:
            raise ValueError(f"Vec3 dot: vec3 must be a Vec3, but got {vec3}")
    
    def multiplyScalar(self, scalar):
        '''
        Multiply this vector by a scalar in-place.
        Args:
            scalar float: A scalar.
        '''
        self._xyz[0] *= scalar
        self._xyz[1] *= scalar
        self._xyz[2] *= scalar
        return self
    
    # def cross(self, vec3):
    #     if isinstance(vec3, Vec3):
    #         if self.space != vec3.space:
    #             raise ValueError(f"Vec3 cross: spaces must match, but got {self.space} and {vec3.space}")
    #         return Vec3(
    #             self._xyz[1] * vec3._xyz[2] - self._xyz[2] * vec3._xyz[1],
    #             self._xyz[2] * vec3._xyz[0] - self._xyz[0] * vec3._xyz[2],
    #             self._xyz[0] * vec3._xyz[1] - self._xyz[1] * vec3._xyz[0],
    #             space = self.space
    #         )
    #     else:
    #         raise ValueError(f"Vec3 cross: vec3 must be a Vec3, but got {vec3}")
    #     return self
    
    def length(self) -> float:
        '''
        Get the length of this vector.
        Returns:
            float: The length of this vector.
        '''
        return np.sqrt(self._xyz[0] * self._xyz[0] + self._xyz[1] * self._xyz[1] + self._xyz[2] * self._xyz[2])
    
    def normalize(self):
        '''
        Normalize this vector in-place.
        '''
        l = self.length()
        if l == 0.0:
            return self
        self._xyz[0] /= l
        self._xyz[1] /= l
        self._xyz[2] /= l
        return self

    def distanceTo(self, vec3) -> float:
        '''
        Calculate the distance to another vector.
        Args:
            vec3 Vec3: Another vector.
        Returns:
            float: The L2 distance to the other vector.
        '''
        if isinstance(vec3, Vec3):
            if self.space != vec3.space:
                raise ValueError(f"Vec3 distanceTo: spaces must match, but got {self.space} and {vec3.space}")
            return np.sqrt(
                (self._xyz[0] - vec3._xyz[0]) * (self._xyz[0] - vec3._xyz[0]) +
                (self._xyz[1] - vec3._xyz[1]) * (self._xyz[1] - vec3._xyz[1]) +
                (self._xyz[2] - vec3._xyz[2]) * (self._xyz[2] - vec3._xyz[2])
            )
        else:
            raise ValueError(f"Vec3 distanceTo: vec3 must be a Vec3, but got {vec3}")
        
    def distanceToSquared(self, vec3) -> float:
        '''
        Calculate the squared distance to another vector.
        Args:
            vec3 Vec3: Another vector.
        Returns:
            float: The squared L2 distance to the other vector.
        '''
        if isinstance(vec3, Vec3):
            if self.space != vec3.space:
                raise ValueError(f"Vec3 distanceToSquared: spaces must match, but got {self.space} and {vec3.space}")
            return (
                (self._xyz[0] - vec3._xyz[0]) * (self._xyz[0] - vec3._xyz[0]) +
                (self._xyz[1] - vec3._xyz[1]) * (self._xyz[1] - vec3._xyz[1]) +
                (self._xyz[2] - vec3._xyz[2]) * (self._xyz[2] - vec3._xyz[2])
            )
        else:
            raise ValueError(f"Vec3 distanceToSquared: vec3 must be a Vec3, but got {vec3}")
    
    def set(self, x : float, y : float, z : float):
        '''
        Set the value of this vector in-place.
        Args:
            x: x coordinate.
            y: y coordinate.
            z: z coordinate.
        '''
        self._xyz[0] = x
        self._xyz[1] = y
        self._xyz[2] = z
        return self
    
    def __copy__(self):
        return Vec3(self._xyz[0], self._xyz[1], self._xyz[2], space = self.space)
    
    def copy(self):
        '''
        A deep copy this vector.
        '''
        return self.__copy__()
    

