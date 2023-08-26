# defines the abstract class Geometry

import numpy as np
from .group import GeomWrapper
from ..core.mat44 import Mat44
from ..core.vec3 import Vec3
from ..core.constants import CONSTANTS

class GeometryTemplate:
    def __init__(self, brain, name : str, group_name : str | None = None, auto_register : bool = True) -> None:
        if brain is None:
            raise ValueError(f"Brain must be <threebrainpy.core.Brain> instance.")
        # TODO: check name
        self._brain = brain
        self.name = name
        self.render_order : float = 1.0
        self._position = Vec3([0, 0, 0], space = "ras_tkr")
        self._trans_mat = Mat44()
        self._disable_trans_mat = False
        self._layers = set()
        self.clickable : bool = False
        self.use_cache : bool = False
        self.custom_info : str = ""
        if group_name is None or group_name == "":
            self._group = None
        else:
            group_existed = brain.has_group(group_name)
            self._group = brain.ensure_group(name = group_name)
            if not auto_register and not group_existed and brain.has_group(group_name):
                del brain._groups[group_name]
        if auto_register:
            self._brain._geoms[self.name] = self


    @property
    def type(self):
        return "abstract"
    def get_position(self, space = "ras", world = False):
        '''
        Get relative position of the geometry in the specified space
        @param space: the space to get the position in
        @param world: whether to get the position in world space
            if True, the position will be transformed by the affine matrix of the parent group
            if False, the position will be local (relative to the parent group)
        '''
        re = self._position.copy()
        if space != re.space:
            transform = self._brain.get_transform(space_from = re.space, space_to = space)
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
    def set_position(self, position : Vec3):
        if not isinstance(position, Vec3):
            raise ValueError("set_position: Invalid position type, must be Vec3.")
        self._position.copyFrom(position)
    @property
    def affine(self) -> Mat44:
        if self._disable_trans_mat:
            return Mat44()
        return self._trans_mat
    def set_affine(self, m, *args) -> Mat44:
        if not isinstance(m, (Mat44, np.ndarray)):
            if isinstance(m, (list, tuple)):
                m = np.array(m, dtype=float)
            else:
                m = np.array([m, *args], dtype=float)
        if m.size == 12:
            m = m.reshape((3, 4))
        elif m.size == 16:
            m = m.reshape((4, 4))
        else:
            raise ValueError(f"Invalid affine matrix (length must by either 12 or 16): {args}")
        self._trans_mat.mat[0:3,0:4] = m[0:3,0:4]
        return self._trans_mat
    def enable_affine(self, enabled : bool = True) -> None:
        self._disable_trans_mat = not enabled
    def disable_affine(self) -> None:
        self._disable_trans_mat = True
    @property
    def layers(self):
        if len(self._layers) == 0:
            return (CONSTANTS.LAYER_USER_ALL_CAMERA_1, )
        return tuple(self._layers)
    def enable_layers(self, *args) -> None:
        for layer in args:
            layer = int(layer)
            if layer < 0:
                raise ValueError(f"Invalid layer: {layer}")
            if layer >= 32:
                raise ValueError(f"Invalid layer: {layer}")
            self._layers.add(layer)
    def disable_layers(self, *args) -> None:
        for layer in args:
            layer = int(layer)
            if layer in self._layers:
                self._layers.remove(layer)
    def set_layers(self, *args) -> None:
        self._layers.clear()
        self.enable_layers(*args)
    @property
    def subject_code(self):
        if self.group is None:
            return None
        return self.group.subject_code
    @property
    def group(self):
        return self._group
    @property
    def group_name(self):
        if self._group is None:
            return self._group_name
        return self._group.name
    @property
    def group_position(self):
        if self.group is None:
            return np.array([0, 0, 0], dtype=float)
        return self.group.position
    @property
    def group_layers(self):
        if self.group is None:
            re = set()
            re.add(CONSTANTS.LAYER_USER_ALL_CAMERA_1)
            return re
        return self.group.layers
    
    def to_dict(self):
        group_info = None
        if self.group is not None:
            group_info = {
                'group_name': self.group.name,
                'group_layer': tuple(self.group.layers),
                'group_position': self.group.position.tolist()
            }
        affine = self.affine
        data = {
            'name': self.name,
            'type': self.type,
            'render_order': self.render_order,
            'subject_code': self.subject_code,
            'position': self.get_position(space = "ras_tkr", world = False),
            'trans_mat': self._brain.set_transform_space(transform = affine, space_from = "ras_tkr" if affine.modality_from == "T1" else affine.space_from, space_to = "ras_tkr"),
            'disable_trans_mat': self._disable_trans_mat,
            'layer': list(self.layers),
            'clickable': self.clickable,
            'use_cache': self.use_cache,
            'custom_info': self.custom_info,
            'value': None,
            'keyframes': [],
            'group': group_info,
        }
        return data
    def __repr__(self):
        if self.group is None:
            return f"<{self.__class__.__name__} ({self.type}): {self.name}>"
        return f"<{self.__class__.__name__} ({self.type}): {self.name} in group [{ self.group.name }]>"


# $time_stamp
# NULL

# $value
# NULL

# $keyframes
# list()


# $subject_code
# NULL
