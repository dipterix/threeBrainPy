from typing import Union
import numpy as np
from .geom_template import GeometryTemplate
from .constants import CONSTANTS
from .vec3 import Vec3
from .keyframe import SimpleKeyframe


class ElectrodeSphere(GeometryTemplate):
    '''
    Sphere geometry, to be displayed as electrode contacts in the 3D viewers.
    '''
    def __init__(self, brain, number : int, label : str, position : Union[list, None] = None, **kwargs) -> None:
        number = int(number)
        if number <= 0:
            raise ValueError("Invalid electrode number, must start from 1.")
        subject_code = brain.subject_code
        name = kwargs.get('name', None)
        if name is None or name == "":
            name = f"{subject_code}, {number} - {label}"
        
        group_name = kwargs.get('group_name', None)
        if group_name is None or group_name == "":
            group_name = f"Electrodes ({subject_code})"
        super().__init__(brain = brain, name = name, group_name = group_name)
        self.set_layers( CONSTANTS.LAYER_USER_ALL_CAMERA_1 )
        self._keyframes = {}
        self._number = number
        self._position = Vec3(position) # default spacing is scannerRAS
        self.radius = kwargs.get('radius', 2.0)
        self.width_segments = int(kwargs.get('width_segments', 10))
        self.height_segments = int(kwargs.get('height_segments', 6))
        self.is_surface = kwargs.get('is_surface', False)
        self.use_template = kwargs.get('use_template', False)
        self.custom_info = kwargs.get('custom_info', "")
        self.clickable = True
        self.hemisphere = kwargs.get('hemisphere', None)
        # For surface electrodes only, this is the surface to snap to
        self.surface_type = kwargs.get('surface_type', "pial")
        # set only when manual MNI305 position is set
        self._mni305_position = None
        # set for surface electrodes (positions on the sphere, for template mapping)
        self._sphere_position = Vec3([0, 0, 0], space = "sphere")
    @property
    def number(self):
        return self._number
    def get_position(self, space : str = "ras", world : bool = False):
        if space in ("mni305", "mni152") and self._mni305_position is not None:
            re = self._mni305_position.copy()
            re.space = "mni305"
            if space == "mni152":
                transform = self._brain.get_transform(space_from = "mni305", space_to = "mni152")
                re.applyMat44( transform )
        else:
            re = self._position.copy()
            if space != self._position.space:
                transform = self._brain.get_transform(space_from = self._position.space, space_to = space)
                re.applyMat44( transform )
        if world:
            if self._group is not None:
                transform = self._brain.set_transform_space(
                    transform = self._group.trans_mat,
                    space_from = space,
                    space_to = space
                )
                re.applyMat44( transform )
        return re
    
    def set_mni_position(self, position : Vec3):
        if isinstance(position, Vec3):
            if position.space not in ("mni305", "mni152"):
                raise ValueError("set_mni_position: Invalid position.space, must be mni305 or mni152.")
        position = Vec3(position, space="mni152") # will copy
        if position.space == "mni152":
            transform = self._brain.get_transform(space_from = "mni152", space_to = "mni305")
            position.applyMat44( transform )
        if not isinstance( self._mni305_position, Vec3 ):
            self._mni305_position = position
        else:
            self._mni305_position.copyFrom(position)

    def set_sphere_position(self, position ):
        position = Vec3(position)
        self._sphere_position.copyFrom( position._xyz )
        self._sphere_position.space = "sphere"
        if self._sphere_position.length() > 0.001:
            self._sphere_position.normalize().multiplyScalar( 100.0 )
        else:
            self._sphere_position.set(0, 0, 0)
    def get_sphere_position(self):
        return self._sphere_position.copy()
    @property
    def type(self):
        return "sphere"
    @property
    def is_electrode(self):
        '''
        Whether this geometry is a electrode. Always True for this class.
        '''
        return True
    def set_keyframe(self, value, time = None, name : str = "value", dtype : Union[str, None] = None) -> SimpleKeyframe:
        '''
        Set the value of the keyframe.
        @param value: The value of the keyframe.
        @param time: The time stamp of the value
        @param name: The name of the keyframe, default is "value".
        @param dtype: The data type of the keyframe, either "continuous" or "discrete"; default is derived from the type of the value.
        '''
        if isinstance(value, (list, tuple, set, )):
            value = np.array(list(value)).reshape(-1)
        elif isinstance(value, dict):
            if time is not None:
                raise ValueError("set_keyframe: time must be None when value is a dict (the keys will be used as time).")
            time = [float(k) for k in value.keys()]
            value = np.array(list(value.values())).reshape(-1)
        if dtype is None:
            if isinstance(value, np.ndarray):
                if value.size == 0 or isinstance(value.item(0), str):
                    dtype = "discrete"
                elif np.isreal(value.item(0)):
                    dtype = "continuous"
                else:
                    raise TypeError(f"Invalid value type: {type(value.item(0))}")
            elif np.all(np.isreal(value)):
                dtype = "continuous"
            else:
                dtype = "discrete"
        keyframe = SimpleKeyframe(name=name, value=value, time=time, dtype=dtype)
        self._keyframes[ keyframe.name ] = keyframe
        return keyframe
    def get_keyframe(self, name) -> Union[SimpleKeyframe, None]:
        '''
        Get the value of the keyframe.
        @param name: The name of the keyframe.
        '''
        return self._keyframes.get(name, None)
    def del_keyframe(self, name) -> Union[SimpleKeyframe, None]:
        '''
        Delete the keyframe.
        @param name: The name of the keyframe.
        '''
        return self._keyframes.pop(name, None)
    @property
    def keyframe_names(self):
        '''
        The keyframes of the geometry.
        '''
        return tuple(self._keyframes.keys())
    def to_dict(self):
        data = super().to_dict()
        # override position to tkrRAS
        data['position'] = self.get_position(space = "ras_tkr")

        data['radius'] = self.radius
        data['width_segments'] = self.width_segments
        data['height_segments'] = self.height_segments
        data['is_electrode'] = True
        data['is_surface_electrode'] = self.is_surface
        data['use_template'] = self.use_template
        data['surface_type'] = self.surface_type
        data['hemisphere'] = self.hemisphere
        data['vertex_number'] = -1
        data['MNI305_position'] = self.get_position(space = "mni305")
        data['sphere_position'] = self._sphere_position.copy()
        data['keyframes'] = dict(**self._keyframes)

        # legacy compatibility
        data['sub_cortical'] = not self.is_surface
        data['search_geoms'] = self.hemisphere
        data['number'] = self.number
        return data
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"