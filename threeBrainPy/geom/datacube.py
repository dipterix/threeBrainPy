from .geometry import GeometryTemplate
from ..utils import VolumeWrapper
from ..core.mat44 import Mat44
from ..core.constants import CONSTANTS


class VolumeSlice( GeometryTemplate ):
    '''
    Volume slice geometry, to be displayed as a slice in the 3D (side) viewers.
    '''
    def __init__(self, brain, volume, name : str | None = None, group_name : str | None = None) -> None:
        '''
        Creates a volume (MRI) slice geometry.
        @param brain: The brain instance.
        @param volume: The volume data. Can be a numpy array or a <threebrainpy.utils.VolumeWrapper> instance,
            or a path to a nifti/mgz file.
        @param name: The name of the geometry.
        @param group_name: The name of the group to which this geometry belongs;
            default is "Volume - {name}", which rarely needs to be manually set.
        '''
        subject_code = brain.subject_code
        if name is None:
            name = f"T1 ({subject_code})"
        if group_name is None:
            group_name = f"Volume - {name}"
        super().__init__(brain = brain, name = name, group_name = group_name)
        if not isinstance(volume, VolumeWrapper):
            volume = VolumeWrapper(volume)
        self._color_format = "RedFormat"
        self.volume : VolumeWrapper = volume
        self.threshold : float = 10
        self.clickable = False
        self.set_layers( CONSTANTS.LAYER_SYS_ALL_SIDE_CAMERAS_13 )
        # For T1 slices, don't worry about the transform for T1, the JS code will take care of it
        group = self._group
        if group is None:
            raise ValueError("Geometry [VolumeSlice] must have a group.")
        # Add the volume data to the group so the data can be loaded by the js engine
        group.set_group_data(name = "volume_data", value = self.volume.as_cache(), is_cache = False)
        # Make sure the cache name is updated, self.subject_code is self.group.subject_code, which comes from brain.subject_code
        group.set_cache_name(name = f"{self.subject_code}/mri")
    @property
    def type(self):
        return "datacube"
    @property
    def shape(self):
        return self.volume.shape
    def set_color_format(self, color_format : str) -> None:
        if color_format not in ("RedFormat", "RGBAFormat"):
            raise ValueError(f"Invalid color format: {color_format}. Please specify either 'RedFormat' or 'RGBAFormat'.")
        self._color_format = color_format
    @property
    def is_datacube(self):
        '''
        Whether this geometry is a DataCube. To be compatible with R package <threeBrain>.
        '''
        return True
    @property
    def is_VolumeSlice(self):
        return True
    def to_dict(self):
        if self._group is None:
            raise ValueError("Geometry [VolumeSlice] must be added to a group before it can be converted to a dictionary.")
        data = super().to_dict()
        data['isDataCube'] = True
        data['isVolumeCube'] = True
        data['threshold'] = self.threshold
        # data['color_format'] = self._color_format
        return data

class VolumeCube( GeometryTemplate ):
    def __init__(self, brain, volume, name : str, 
                 color_format : str = "RedFormat", group_name : str | None = None) -> None:
        '''
        Creates a volume (atlas, CT) cube geometry.
        @param brain: The brain instance.
        @param volume: The volume data. Can be a numpy array or a <threebrainpy.utils.VolumeWrapper> instance,
            or a path to a nifti/mgz file.
        @param name: The name of the geometry.
        @param color_format: The color format of the volume data. Can be either "RedFormat" for continuous values
            such as CT density or fMRI analysis results, or "RGBAFormat" for discontinuous data such as anatomical
            segmentations or parcelations.
        @param group_name: The name of the group to which this geometry belongs;
            default is name (or "Atlas - {name}" if name does not start with "Atlas - "), 
            which rarely needs to be manually set.
        add_nifti(self, "CT", path = ct_path,
                color_format = "RedFormat", trans_mat = trans_mat,
                trans_space_from = "scannerRAS")
        '''
        if name is None:
            raise ValueError("Geometry [VolumeCube] must have a name.")
        if group_name is None:
            # Should be VolumeCube, but it was original created to show atlas, so keep it as Atlas for compatibility
            if name.startswith("Atlas - "):
                group_name = name
            else:
                group_name = name
        if color_format not in ("RedFormat", "RGBAFormat"):
            raise ValueError(f"Invalid color format: {color_format}. Please specify either 'RedFormat' or 'RGBAFormat'.")
        if not isinstance(volume, VolumeWrapper):
            volume = VolumeWrapper(volume)
        super().__init__(brain = brain, name = name, group_name = group_name)
        self._color_format = color_format
        self.volume : VolumeWrapper = volume
        self.threshold : float = 0.6
        self.clickable = False
        self.set_layers( CONSTANTS.LAYER_SYS_MAIN_CAMERA_8 )
        # In JS code, this._transform.multiply( niftiData.model2RAS );
        # If not transform is given, the volume will be in RAS space, but 
        # we need to display it in tkrRAS space (since the world space is tkrRAS), 
        # the trans_mat needs to be RAS to tkrRAS in tkrRAS space for T1
        # For other modalities, this matrix is going to be set manually via set_affine anyway
        self._trans_mat = Mat44(
            volume.vox2ras_tkr * (~volume.vox2ras),
            space_from="ras_tkr", space_to="ras_tkr",
            modality_from="T1", modality_to="T1"
        )
        group = self._group
        if group is None:
            raise ValueError("Geometry [VolumeCube] must have a group.")
        # Add the volume data to the group so the data can be loaded by the js engine
        group.set_group_data(name = "volume_data", value = self.volume.as_cache(), is_cache = False)
        # Make sure the cache name is updated, self.subject_code is self.group.subject_code, which comes from brain.subject_code
        group.set_cache_name(name = f"{self.subject_code}/mri")
    def set_affine(self, m : Mat44) -> Mat44:
        '''
        @param m: The transform matrix of the volume data. it is needed when the volume imaging modality is not T1 (e.g. CT). 
            The transform matrix converts the volume data to T1 space, so that the volume cube can overlay with T1.
            If `m` is specified, then 
                1. `m.space_from` must be "ras" (when the image is CT, then this means the RAS space in CT scanner)
                2. `m.space_to` must be one of "ras", "voxel", "ras_tkr", "mni305", "mni152"
                3. `m.modality_to` must be "T1"
        '''
        if not isinstance(m, Mat44):
            raise ValueError(f"[VolumeCube.set_affine] must be a Mat44 instance. Current type: {type(m)}")
        if m.modality_to != "T1":
            raise ValueError(f"[VolumeCube.set_affine] `transform.modality_to` must be T1 when transform is not None. Current `modality_to`: {m.modality_to}")
        if m.space_from != "ras":
            raise ValueError(f"[VolumeCube.set_affine] `transform.space_from` must be ras when transform is not None. Current `space_from`: {m.space_from}")
        if m.space_to not in CONSTANTS.SUPPORTED_SPACES:
            raise ValueError(f"[VolumeCube.set_affine] `transform.space_to` must be one of {CONSTANTS.SUPPORTED_SPACES}. Current `space_to`: {m.space_to}")
        self._trans_mat = self._brain.set_transform_space(transform = m, space_from = m.space_from, space_to = "ras")
    @property
    def type(self):
        return "datacube2"
    @property
    def shape(self):
        return self.volume.shape
    def set_color_format(self, color_format : str) -> None:
        if color_format not in ("RedFormat", "RGBAFormat"):
            raise ValueError(f"Invalid color format: {color_format}. Please specify either 'RedFormat' or 'RGBAFormat'.")
        self._color_format = color_format
    @property
    def is_datacube2(self):
        '''
        Whether this geometry is a DataCube. To be compatible with R package <threeBrain>.
        '''
        return True
    @property
    def is_VolumeCube(self):
        return True
    def to_dict(self):
        if self._group is None:
            raise ValueError("Geometry [VolumeCube] must be added to a group before it can be converted to a dictionary.")
        data = super().to_dict()
        data['isDataCube2'] = True
        data['isVolumeCube2'] = True
        data['threshold'] = self.threshold
        data['color_format'] = self._color_format
        data['trans_space_from'] = "scannerRAS"
        return data
