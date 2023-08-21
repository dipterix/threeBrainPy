from .geometry import GeometryTemplate
from ..utils import CONSTANTS
import os

class Surface(GeometryTemplate):
    '''
    Surface geometry, to be displayed as a surface in the 3D main viewer.
    '''
    def __init__(self, brain, name : str, group_name : str, surface_file : str) -> None:
        if not os.path.exists(surface_file) or not os.path.isfile(surface_file):
            raise ValueError(f"Invalid surface file: {surface_file}")
        if group_name is None or group_name == "":
            raise ValueError(f"Invalid group name: {group_name}")
        super().__init__(brain = brain, name = name, group_name = group_name)
        self._surface_file = os.path.abspath(surface_file)
        self.clickable = False
        self.set_layers( CONSTANTS.LAYER_SYS_MAIN_CAMERA_8 )

        group = self._group
        if group is None:
            raise ValueError("Geometry [Surface] must have a group.")
        # Add the surface data to the group so the data can be loaded by the js engine
        group.set_group_data(name = "template_subject", value = group._brain._template_subject, is_cache = False)
        group.set_group_data(name = "subject_code", value = self.subject_code, is_cache = False)
        # set cache file
        group.set_group_data(name = f"free_vertices_{ self.name }", value = self._surface_file, is_cache = True)
        group.set_group_data(name = f"free_faces_{ self.name }", value = self._surface_file, is_cache = True)
        # TODO: add surface type in sub-classes
        # group$set_group_data('surface_type', surface_name)
        # TODO: add surface format in sub-classes
        # group$set_group_data('surface_format', 'fs')

        # Make sure the cache name is updated (freesurfer_path/surf)
        group.set_cache_name(name = f"{self.subject_code}/surf")

    @property
    def type(self):
        return "free"
    def to_dict(self):
        if self._group is None:
            raise ValueError("Geometry [Surface] must be added to a group before it can be converted to a dictionary.")
        data = super().to_dict()
        data['isSurface'] = True
        # data['surface_type'] = self._surface_type
        # re$hemisphere <- self$hemisphere
        # re$subcortical_info <- self$subcortical_info
        return data
    @property
    def is_Surface(self):
        '''
        Whether this geometry is a Surface. Always True for this class.
        '''
        return True

class CorticalSurface( Surface ):

    def __init__(self, brain, surface_type : str, surface_file: str, hemesphere : str, 
                 file_format = "fs", name: str | None = None, group_name: str | None = None) -> None:
        '''
        Creates a cortical surface geometry.
        @param brain: The brain object.
        @param surface_type: The surface type, e.g. "pial", "white", "smoothwm", "sphere".
        @param surface_file: The path to surface file.
        @param hemesphere: The hemesphere, either "left" or "right" partial matching is supported.
        @param file_format: The file format, currently only support "fs".
        @param name: The name of the geometry, will be set to 
            "FreeSurfer {hemesphere} Hemisphere - {surface_type} ({subject_code})", which 
            rarely needs to be manually set
        @param group_name: The name of the group, will be set to
            "Surface - {surface_type} ({subject_code})", which rarely needs to be manually set
        '''
        subject_code = brain.subject_code
        hemesphere = hemesphere.lower()
        if hemesphere[0] not in ['l', 'r']:
            raise ValueError(f"Invalid hemesphere: {hemesphere}")
        hemesphere = hemesphere[0]
        if file_format not in ['fs']:
            raise NotImplementedError(f"File format {file_format} not supported. Currently only support 'fs'.")
        if name is None:
            # 'FreeSurfer Right Hemisphere - %s (%s)'
            name = f"FreeSurfer { 'Left' if hemesphere == 'l' else 'Right' } Hemisphere - {surface_type} ({subject_code})"
        if group_name is None:
            # 'Surface - %s (%s)'
            group_name = f"Surface - {surface_type} ({subject_code})"
        super().__init__(brain = brain, name = name, group_name = group_name, surface_file = surface_file)
        self._file_format = file_format
        self._surface_type = surface_type
        if hemesphere == 'l':
            self._hemesphere = 'lh'
        else:
            self._hemesphere = 'rh'
        self._group.set_group_data('surface_type', self.surface_type)
        self._group.set_group_data('surface_format', self._file_format)
    @property
    def surface_type(self):
        return self._surface_type
    @property
    def hemesphere(self):
        return self._hemesphere
    def to_dict(self):
        data = super().to_dict()
        data['surface_type'] = self.surface_type
        data['hemisphere'] = "left" if self.hemesphere == 'lh' else "right"
        # re$subcortical_info <- self$subcortical_info
        return data
    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.type}): {self.name} ({self.surface_type}, {self.hemesphere}) in group [{ self.group.name }]>"
