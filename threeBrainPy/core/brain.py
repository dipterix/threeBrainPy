import os
import re
import numpy as np
from copy import deepcopy
from .mat44 import Mat44
from .vec3 import Vec3
from .keyframe import SimpleKeyframe
from .colormap import ElectrodeColormap
from .constants import CONSTANTS
from ..geom.group import GeomWrapper
from ..geom.geometry import GeometryTemplate
from ..geom.datacube import VolumeSlice, VolumeCube
from ..geom.blank import BlankPlaceholder
from ..geom.surface import CorticalSurface
from ..geom.sphere import ElectrodeSphere
from ..templates import init_skeleton, template_path
from ..utils import VolumeWrapper, read_xfm
from ..utils.serializer import GeomEncoder
from ..utils.temps import temporary_directory
try:
    from pandas import DataFrame
except:
    DataFrame = None

MNI305_TO_MNI152 = Mat44(CONSTANTS.MNI305_TO_MNI152, space_from="mni305", space_to="mni152")


class Brain(object):
    '''
    Class definition for storing brain data and rendering information.
    Examples:
        This example loads `fsaverage` brain from FreeSurfer (if you have installed) and renders it.
        >>> import os
        >>> from threebrainpy.core import Brain
        >>> fs_home = os.environ.get("FREESURFER_HOME", None)
        >>> if fs_home is not None:
        >>>     brain = Brain("fsaverage", os.path.join(fs_home, "subjects", "fsaverage"))
        >>>     print(brain)
        >>>     brain.build()
    '''
    def _update_matrices(self, volume_files = [], update = 1):
        '''
        Internal method to update voxel-to-ras and voxel-to-tkrRAS matrices.
        Args:
            volume_files: A list of volume files to be used to update the matrices.
                Each volume file must be a path to a volume file (nii, nii.gz, mgz).
            update: update policy, see below.
                - 0: do not update, but will initialize if not exists;
                - 1: update if there is a better one;
                - 2: force update.
        '''
        if len(volume_files) == 0:
            return None
        for volume_file in volume_files:
            if os.path.exists(volume_file):
                vox2ras_needs_update = update >= 2
                vox2ras_tkr_needs_update = update >= 2
                # check if _vox2ras needs update
                if not isinstance(self._vox2ras, Mat44):
                    vox2ras_needs_update = True
                if not isinstance(self._vox2ras_tkr, Mat44):
                    vox2ras_tkr_needs_update = True
                elif update == 1 and self._vox2ras_tkr.extra.get('source_format', None) is not "mgz" and volume_file.lower().endswith(".mgz"):
                    vox2ras_tkr_needs_update = True
                if vox2ras_needs_update or vox2ras_tkr_needs_update:
                    volume = VolumeWrapper(volume_file)
                    if vox2ras_needs_update:
                        self._vox2ras = volume.vox2ras
                    if vox2ras_tkr_needs_update:
                        self._vox2ras_tkr = volume.vox2ras_tkr
                # early stop
                if not vox2ras_needs_update and not vox2ras_tkr_needs_update and update < 2:
                    # this means the matrices are all up-to-date and need no further update
                    return None

    def __init__(self, subject_code : str, path : str, work_dir : str | None = None):
        '''Constructor for Brain.
        Args:
            subject_code: The subject code of the brain.
            path: The path to the FreeSurfer or FreeSurfer-like folder (with MRI stored at `mri` and surfaces at `surf`).
            work_dir: The path to the working directory. If not specified, a temporary directory will be created.
        '''
        if not os.path.exists(path):
            raise FileNotFoundError(f"Brain path {path} not found.")
        if re.match(r"^[a-zA-Z][a-zA-Z0-9_-]{0,}$", subject_code) is None:
            raise ValueError(f"Invalid subject code: {subject_code}")
        self._path = os.path.abspath(path)
        self._subject_code = subject_code
        self._template_subject = "N27"
        self._storage = temporary_directory(prefix = subject_code, dir = work_dir)
        # set up geoms
        self._groups = {}
        self._geoms = {}
        self._slices = {}
        self._surfaces = {}
        self._volumes = {}
        self._electrode_contacts = {}
        self._electrode_cmaps = {}
        # set up global data, this must run prior to _update_matrices
        self._initialize_global_data()
        # Basic information 
        self._vox2ras = None
        self._vox2ras_tkr = None
        self._ras2mni_305 = None
        # using CONSTANT.DEFAULT_SLICE_PREFIXIES and CONSTANT.DEFAULT_ATLAS_PREFIXIES to find the matrices
        volume_prefixies = [*CONSTANTS.DEFAULT_SLICE_PREFIXIES, *CONSTANTS.DEFAULT_ATLAS_PREFIXIES]
        mgz_files = [f"{x}.mgz" for x in volume_prefixies]
        nii_gz_files = [f"{x}.nii.gz" for x in volume_prefixies]
        nii_files = [f"{x}.nii" for x in volume_prefixies]
        self._update_matrices(volume_files = [os.path.join(self.path_mri, x) for x in [*mgz_files, *nii_gz_files, *nii_files]])
        # get ras to mni-305 matrix
        xfm_file = os.path.join(self.path_mri, "transforms", "talairach.xfm")
        try:
            xfm = read_xfm(xfm_file)
            self._ras2mni_305 = xfm['transform']
        except:
            self._ras2mni_305 = Mat44(space_from="ras", space_to="mni305")
        
    def __del__(self):
        self._storage.cleanup()
    def __repr__(self):
        return f"Brain({self._subject_code} @ {self._path})"
    def __str__(self):
        return f"Brain({self._subject_code} @ {self._path})"
    @property
    def subject_code(self):
        '''
        Subject code string.
        '''
        return self._subject_code
    # region <paths>
    @property
    def path(self):
        '''
        The root path to the imaging files.
        '''
        return self._path
    @property
    def path_mri(self):
        '''
        The path to the MRI and atlas files.
        '''
        return os.path.join(self._path, "mri")
    @property
    def path_surf(self):
        '''
        The path to the surface mesh files.
        '''
        return os.path.join(self._path, "surf")
    @property
    def storage(self):
        '''
        The path to a temporary directory for storing intermediate files and viewers.
        '''
        return self._storage
    # endregion
    
    # region <transforms>
    @property
    def vox2ras(self) -> Mat44:
        '''
        A `4x4` voxel (indexing) to T1 scanner RAS (right-anterior-superior coordinate) transform matrix.
        '''
        if isinstance(self._vox2ras, Mat44):
            return self._vox2ras
        m = Mat44(space_from="voxel", space_to="ras")
        m.extra["missing"] = True
        return m
    @property
    def vox2ras_tkr(self) -> Mat44:
        '''
        A `4x4` voxel (indexing) to viewer (or FreeSurfer) tkrRAS (tk-registered right-anterior-superior coordinate) transform matrix.
        '''
        if isinstance(self._vox2ras_tkr, Mat44):
            return self._vox2ras_tkr
        m = Mat44(space_from="voxel", space_to="ras_tkr")
        m.extra["missing"] = True
        return m
    @property
    def ras2ras_tkr(self) -> Mat44:
        '''
        A `4x4` T1 scanner RAS (right-anterior-superior coordinate) to viewer (or FreeSurfer tk-registered) tkrRAS transform matrix.
        '''
        return self.vox2ras_tkr * (~self.vox2ras)
    @property
    def ras2mni_305(self) -> Mat44:
        '''
        A `4x4` transform matrix from T1 scanner RAS (right-anterior-superior coordinate) to MNI305 template space using FreeSurfer affine transform (generated during `recon-all`).
        '''
        if isinstance(self._ras2mni_305, Mat44):
            return self._ras2mni_305
        m = Mat44(space_from="ras", space_to="mni305")
        m.extra["missing"] = True
        return m
    @property
    def ras2mni_152(self) -> Mat44:
        '''
        A `4x4` transform matrix from T1 scanner RAS (right-anterior-superior coordinate) to MNI152 template space using FreeSurfer affine transform (generated during `recon-all`).
        '''
        return MNI305_TO_MNI152 * self.ras2mni_305
    @property
    def ras_tkr2mni_305(self) -> Mat44:
        '''
        A `4x4` transform matrix from tkrRAS to MNI305 template space using FreeSurfer affine transform (generated during `recon-all`).
        '''
        return self.ras2mni_305 * self.vox2ras * (~self.vox2ras_tkr)
    @property
    def ras_tkr2mni_152(self) -> Mat44:
        '''
        A `4x4` transform matrix from tkrRAS to MNI152 template space using FreeSurfer affine transform (generated during `recon-all`).
        '''
        return MNI305_TO_MNI152 * self.ras_tkr2mni_305
    def get_transform(self, space_from : str, space_to : str) -> Mat44:
        '''
        Get transform matrix from `space_from` to `space_to`. 
        Args:
            space_from: The space from which the transform matrix is defined.
                choices are `voxel`, `ras`, `ras_tkr`, `mni305`, `mni152`.
            space_to: The space to which the transform matrix is defined.
                see `space_from` for choices.
        Examples:
            >>> brain.get_transform(space_from = "voxel", space_to = "ras_tkr")
            Mat44 (T1.voxel -> T1.ras_tkr): 
            array([[  -1.,    0.,    0.,  128.],
                [   0.,    0.,    1., -128.],
                [   0.,   -1.,    0.,  128.],
                [   0.,    0.,    0.,    1.]])
        '''
        if space_from not in CONSTANTS.SUPPORTED_SPACES:
            raise ValueError(f"Invalid space_from: {space_from}, supported spaces are: {CONSTANTS.SUPPORTED_SPACES}")
        if space_to not in CONSTANTS.SUPPORTED_SPACES:
            raise ValueError(f"Invalid space_to: {space_to}, supported spaces are: {CONSTANTS.SUPPORTED_SPACES}")
        if space_from == space_to:
            return Mat44(space_from=space_from, space_to=space_to, modality_from="T1", modality_to="T1")
        if space_from == "ras":
            transform = Mat44(space_from="ras", space_to="ras", modality_from="T1", modality_to="T1")
        elif space_from == "ras_tkr":
            transform = deepcopy(~self.ras2ras_tkr)
        elif space_from == "mni305":
            transform = deepcopy(~self.ras2mni_305)
        elif space_from == "mni152":
            transform = deepcopy(~self.ras2mni_152)
        else:
            transform = deepcopy(self.vox2ras)
        if space_to == "ras":
            return transform
        elif space_to == "ras_tkr":
            return self.ras2ras_tkr * transform
        elif space_to == "mni305":
            return self.ras2mni_305 * transform
        elif space_to == "mni152":
            return self.ras2mni_152 * transform
        else:
            return (~self.vox2ras) * transform

    def set_transform_space(self, transform : Mat44, space_from : str, space_to : str) -> Mat44:
        '''
        Returns a copy of `transform`, but with space transformed. 
        Args:
            transform: The transform matrix of class `Mat44`. If `transform` is not specified, then the transform will be identity matrix.
            space_from: The space from which the transform matrix will be defined.
                choices are `voxel`, `ras`, `ras_tkr`, `mni305`, `mni152`.
            space_to: The space to which the transform matrix will be defined.
        Returns:
            The new transform matrix with given spaces and inherited modalities.
        Examples:
            If you have a matrix that switch the column and row indexes in the voxel space,
                what's the matrix in the ras space?
            >>> from threebrainpy.core import Mat44
            >>> idx_transform = Mat44([0,1,0,0,1,0,0,0,0,0,1,0], space_from = "voxel", space_to = "voxel")
            >>> idx_transform
            Mat44 (T1.voxel -> T1.voxel): 
            array([[0., 1., 0., 0.],
                [1., 0., 0., 0.],
                [0., 0., 1., 0.],
                [0., 0., 0., 1.]])
            >>> # Applies idx_transform first then vox-to-ras
            >>> brain.set_transform_space(transform = idx_transform, space_from = "voxel", space_to = "ras")
            Mat44 (T1.voxel -> T1.ras): 
            array([[   0.        ,   -1.        ,    0.        ,  131.61447144],
                [   0.        ,    0.        ,    1.        , -127.5       ],
                [  -1.        ,    0.        ,    0.        ,  127.5       ],
                [   0.        ,    0.        ,    0.        ,    1.        ]])
            >>> # To validate the transform
            >>> brain.vox2ras * idx_transform
            Mat44 (T1.voxel -> T1.ras): 
            array([[   0.        ,   -1.        ,    0.        ,  131.61447144],
                [   0.        ,    0.        ,    1.        , -127.5       ],
                [  -1.        ,    0.        ,    0.        ,  127.5       ],
                [   0.        ,    0.        ,    0.        ,    1.        ]])
        '''
        if not isinstance(transform, Mat44):
            raise TypeError(f"Invalid transform matrix: {transform}")
        if space_from not in CONSTANTS.SUPPORTED_SPACES:
            raise ValueError(f"Invalid space_from: {space_from}, supported spaces are: {CONSTANTS.SUPPORTED_SPACES}")
        if space_to not in CONSTANTS.SUPPORTED_SPACES:
            raise ValueError(f"Invalid space_to: {space_to}, supported spaces are: {CONSTANTS.SUPPORTED_SPACES}")
        # check modalities
        if transform.modality_from != "T1" and transform.space_from != space_from:
            raise ValueError(f"Invalid transform matrix: {transform}, modality_from must be 'T1' or space_from must be {space_from}.")
        if transform.modality_to != "T1" and transform.space_to != space_to:
            raise ValueError(f"Invalid transform matrix: {transform}, modality_to must be 'T1' or space_to must be {space_to}.")
        re = deepcopy(transform)
        if transform.modality_from == "T1":
            re = re * self.get_transform(space_to = transform.space_from, space_from = space_from)
        if transform.modality_to == "T1":
            re = self.get_transform(space_from = transform.space_to, space_to = space_to) * re
        return re
    # endregion
    
    # region <Group operations>
    def _initialize_global_data(self):
        global_placeholder = BlankPlaceholder(brain = self)
        self._globals = global_placeholder.group
    def add_global_data(self, name : str, value : any | str, is_cache : bool = False, absolute_path : str = None):
        '''
        Internal method to add global data to the brain.
        Args:
            name: The name of the global data.
            value: If `is_cache=False`, the value of the global data, can be any JSON-serializable object.
                If `is_cache=True`, the path to, or the file name of the cached JSON file.
            is_cache: Whether the `value` is a cached JSON file.
            absolute_path: The absolute path to the cached JSON file.
        '''
        self._globals.set_group_data(name = name, value = value, is_cache = is_cache, absolute_path = absolute_path)
    def get_global_data(self, name):
        '''
        Get global data from the brain instance.
        Args:
            name: The name of the global data.
        Returns:
            The value of the global data.
        '''
        return self._globals.get_group_data(name = name)
    def add_group(self, name : str, exists_ok : bool = True) -> GeomWrapper:
        '''
        Internal method to add a geometry groups to the brain.
        Args:
            name: The name of the group.
            exists_ok: Whether to overwrite the existing group if the group already exists.
        Returns:
            The group instance.
        '''
        group = self._groups.get(name, None)
        if group is None:
            group = GeomWrapper(self, name = name, position = [0,0,0], layers = [CONSTANTS.LAYER_USER_MAIN_CAMERA_0])
            self._groups[name] = group
        elif not exists_ok:
            raise ValueError(f"Group {name} already exists.")
        return group
    def get_group(self, name : str) -> GeomWrapper | None:
        '''
        Get a geometry group from the brain.
        Args:
            name: The name of the group.
        Returns:
            The group instance or `None` if the group does not exist.
        '''
        return self._groups.get(name, None)
    def has_group(self, name : str) -> bool:
        '''
        Check if the brain has a geometry group.
        Args:
            name: The name of the group.
        Returns:
            `True` if the group exists, `False` otherwise.
        '''
        return name in self._groups
    def ensure_group(self, name : str, **kwargs : dict) -> GeomWrapper:
        '''
        Ensure that a geometry group exists, if not, create one.
        Args:
            name: The name of the group.
            kwargs: Other arguments to be passed to `add_group`.
        Returns:
            The group instance.
        '''
        if self.has_group(name):
            return self.get_group(name)
        return self.add_group(name = name, exists_ok = True, **kwargs)
    def set_group_data(self, name : str, value : any | str, is_cache : bool = False, absolute_path : str | None = None, auto_create : bool = True) -> None:
        '''
        Set group data to the brain so the JavaScript engine will have access to the data. 
            This method is a low-level function
        Args:
            name: The name of the group data.
            value: If `is_cache=False`, the value of the group data, can be any JSON-serializable object.
                If `is_cache=True`, the path to, or the file name of the cached JSON file.
            is_cache: Whether the `value` is a cached JSON file.
            absolute_path: The absolute path to the cached JSON file.
            auto_create: Whether to create a group if the group does not exist.
        '''
        if auto_create:
            self.ensure_group(name = name)
        group = self.get_group(name)
        if group is None:
            raise ValueError(f"Group {name} not found.")
        group.set_group_data(name = name, value = value, is_cache = is_cache, absolute_path = absolute_path)
        return None
    def get_global_data(self, name : str, force_reload : bool = False, ifnotfound : any | None = None) -> any:
        '''
        Get group data from the brain instance.
        Args:
            name: The name of the group data.
            force_reload: Whether to force reload the group data.
            ifnotfound: If the group data is not found, return this value.
        Returns:
            The value of the group data, or `ifnotfound`.
        '''
        group = self.get_group(name)
        if group is None:
            return ifnotfound
        return group.get_group_data(name = name, force_reload = force_reload, ifnotfound = ifnotfound)
    # endregion
    
    # region <Geometries>
    def get_geometry(self, name : str) -> GeometryTemplate | None:
        '''
        Get a geometry instance from the brain.
        Args:
            name: The name of the geometry template.
        Returns:
            The geometry instance or `None` if the geometry instance does not exist.
        '''
        return self._geoms.get(name, None)
    def has_geometry(self, name : str) -> bool:
        '''
        Check if the brain has a geometry instance.
        Args:
            name: The name of the geometry template.
        Returns:
            `True` if the geometry instance exists, `False` otherwise.
        '''
        return name in self._geoms
    # endregion
    
    # region <MRI slices>
    def add_slice(self, slice_prefix : str = "brain.finalsurfs", name : str = "T1"):
        '''
        Add a (MRI) volume slice to the brain. The slices will be rendered in side canvas using datacube (JavaScript class).
        Args:
            slice_prefix: The prefix of the slice file in the `mri` folder. (default: "brain.finalsurfs")
            name: The name of the slice, currently only "T1" is supported. (default: "T1")
        Examples:
            Adds `brain.finalsurfs.mgz` or `brain.finalsurfs.nii[.gz]` to the brain slices
            >>> brain.add_slice(slice_prefix = "brain.finalsurfs", name = "T1")
        '''
        # In geoms, the name needs to be appended with the subject code
        # possible file names
        slice_prefix = slice_prefix.lower()
        candidates = [
            f"{slice_prefix}.mgz",
            f"{slice_prefix}.nii.gz",
            f"{slice_prefix}.nii",
        ]
        slice_files = [x for x in os.listdir(self.path_mri) if x.lower() in candidates]
        if len(slice_files) == 0:
            return None
        slice_file = slice_files[0]
        slice_path = os.path.abspath(os.path.join(self.path_mri, slice_file))
        slice = VolumeSlice(brain = self, name = f"{name} ({self.subject_code})", volume = slice_path)
        self._slices[name] = slice
        self._update_matrices(volume_files = [slice_path])
        return slice
    def get_slice(self, name : str) -> VolumeSlice | None:
        '''
        Get MRI slices from the brain.
        Args:
            name: The name of the slice.
        Returns:
            The slice instance or `None` if the slice does not exist.
        '''
        return self._slices.get(name, None)
    def get_slices(self) -> list[VolumeSlice]:
        '''
        Get all MRI slices from the brain.
        '''
        return self._slices
    def has_slice(self, name : str) -> bool:
        '''
        Check if the brain has MRI slices with given name.
        '''
        return name in self._slices
    # endregion
    
    # region <Atlases/CT/3D voxels>
    def add_volume(self, volume_prefix : str, is_continuous : bool, name : str = None) -> dict | None:
        '''
        Add a (Atlas/CT/3D voxel) volume cube to the brain. The VolumeCube will be rendered in main canvas using datacube2 (JavaScript class).
        Args:
            volume_prefix: The prefix of the volume file in the `mri` folder. (e.g. "aparc+aseg", "CT_raw")
            is_continuous: Whether the volume is continuous or discrete. 
                The color map for continuous and discrete values are set separately.
                For continuous values, the volume will be rendered using RedFormat (single-channel shader). 
                    The color will be assgined according to the volume value (density).
                For discrete values, the volume will be rendered using RGBAFormat (four-channel shader). 
                    The volume data will be used as the color index, and the color map will be set separately.
                    The color index must be integer, and the color map must be a list of RGBA colors.
            name: The name of the volume, default is to automatically derived from the volume_prefix. 
                Please set name to "CT" is the volume file is CT for localization
        Examples:
            Adds `aparc+aseg.mgz` or `aparc+aseg.nii[.gz]` to the brain volumes
            >>> brain.add_volume(volume_prefix = "aparc+aseg", is_continuous = False)
        '''
        # In geoms, the name needs to be appended with the subject code
        # possible file names
        volume_prefix = volume_prefix.lower()
        if name is None:
            name = re.sub(r"[^a-zA-Z0-9_]", "_", volume_prefix)
        candidates = [
            f"{volume_prefix}.mgz",
            f"{volume_prefix}.nii.gz",
            f"{volume_prefix}.nii",
        ]
        volume_files = [x for x in os.listdir(self.path_mri) if x.lower() in candidates]
        if len(volume_files) == 0:
            return None
        volume_file = volume_files[0]
        volume_path = os.path.abspath(os.path.join(self.path_mri, volume_file))
        volume = VolumeWrapper(volume_path)
        volume_cube = VolumeCube(brain = self, name = f"Atlas - {name} ({self.subject_code})", volume = volume,
                                 color_format = "RedFormat" if is_continuous else "RGBAFormat")
        self._update_matrices(volume_files = [volume_path])
        self._volumes[name] = volume_cube
        return volume_cube
    # endregion
    
    # region <Surfaces>
    def _surface_morph_paths(self, hemesphere : str = "both", morph_types : tuple[str] | list[str] | str | None = None) -> dict | None:
        if hemesphere.lower()[0] not in ['l', 'r', 'b']:
            raise ValueError(f"Invalid hemesphere: {hemesphere}")
        hemesphere = hemesphere.lower()[0]
        if hemesphere == "b":
            hemesphere = ["lh", "rh"]
        else:
            hemesphere = [f"{ hemesphere }h"]
        if morph_types is None:
            morph_types = CONSTANTS.SURFACE_BASE_TEXTURE_TYPES
        elif isinstance(morph_types, str):
            morph_types = [morph_types]
        for morph_type in morph_types:
            not_found = False
            re = dict([(h, os.path.join(self.path_surf, f"{h}.{morph_type}")) for h in hemesphere])
            for h, morph_path in re.items():
                if not os.path.exists(morph_path):
                    not_found = True
                    break
            if not not_found:
                return re
        return None

    def add_surfaces(self, surface_type : str, hemesphere : str = "both") -> dict | None:
        '''
        Add a surface to the brain. The surface will be rendered in main canvas using surface (JavaScript class).
        Args:
            surface_type: The type of the surface, e.g. "pial", "white", "inflated", "sphere" (see `surf/` folder, usually `[lr]h.<surface_type>`).
            hemesphere: The hemesphere of the surface, can be "l", "r", "b" (both). (default: "both")
        Returns:
            A dictionary of surface instances if exist, with keys being the hemesphere.
        Examples:
            Adds `lh.pial` and `rh.pial` to the brain surfaces
            >>> brain.add_surfaces(surface_type = "pial", hemesphere = "both")
        '''
        hemesphere_prefix = hemesphere.lower()[0]
        if hemesphere_prefix == "b":
            hemesphere_prefix = ["lh", "rh"]
        elif hemesphere_prefix == "l":
            hemesphere_prefix = ["lh"]
        elif hemesphere_prefix == "r":
            hemesphere_prefix = ["rh"]
        else:
            raise ValueError(f"Invalid hemesphere: {hemesphere}")
        surface_type0 = surface_type
        surface_type = surface_type.lower()
        if surface_type in ("pial", "pial.t1",):
            # Newer freesurfer versions use "pial.T1" as the surface type, while older versions use "pial"
            surface_type = ["pial", "pial.t1"]
            surface_type0 = "pial"
        # construct possible file names
        file_names_lower = []
        for h in hemesphere_prefix:
            for s in surface_type:
                file_names_lower.append(f"{h}.{s}")
        # search for the file
        if not os.path.exists(self.path_surf):
            return None
        if not os.path.isdir(self.path_surf):
            return None
        surface_files = [x for x in os.listdir(self.path_surf) if x.lower() in file_names_lower]
        if len(surface_files) == 0:
            return None
        surface_dict = self._surfaces.get(surface_type0, None)
        if not isinstance(surface_dict, dict):
            surface_dict = {}
            self._surfaces[surface_type0] = surface_dict
        # check base vertex colors
        base_vertex_colors = self._surface_morph_paths()
        for surface_filename in surface_files:
            surface_file = os.path.join(self.path_surf, surface_filename)
            surface = CorticalSurface(brain = self, surface_type = surface_type0, surface_file = surface_file, hemesphere = surface_filename[0])
            surface_dict[ surface.hemesphere ] = surface
            if isinstance(base_vertex_colors, dict):
                surface.group.set_group_data(
                    name = f"{surface.hemesphere}_primary_vertex_color", 
                    value = base_vertex_colors[surface.hemesphere], is_cache = True)
        return surface_dict
    def get_surfaces(self, surface_type : str) -> dict | None:
        '''
        Get surfaces from the brain.
        Args:
            surface_type: The type of the surface, e.g. "pial", "white", "inflated", "sphere" (see `surf/` folder, usually `[lr]h.<surface_type>`).
        Returns:
            A dictionary of surface instances if exist, with keys being the hemesphere.
        '''
        return self._surfaces.get(surface_type, None)
    def has_surface_type(self, surface_type : str) -> bool:
        '''
        Check if the brain has surfaces with given type.
        Args:
            surface_type: The type of the surface, e.g. "pial", "white", "inflated", "sphere" (see `surf/` folder, usually `[lr]h.<surface_type>`).
        '''
        return surface_type in self._surfaces
    # endregion
    
    # region <Electrode contacts>
    def add_electrode_contact(
            self, number : int, label : str, 
            position : Vec3 | list | None = None, 
            is_surface : bool = False, 
            radius : float | None = None,
            mni_position : Vec3 | list | None = None, 
            sphere_position : Vec3 | list | None = None,
            **kwargs : dict) -> ElectrodeSphere:
        '''
        Add an electrode contact to the brain. The electrode contact will be rendered in main canvas using sphere (JavaScript class).
        Args:
            number: The integer number of the electrode contact, starting from 1.
            label: The label of the electrode contact.
            position: The position of the electrode contact in the native space of the brain, or a `Vec3` instance with given spaces.
            is_surface: Whether the electrode contact is a surface electrode.
            radius: The radius of the electrode contact, default is 2.0 for surface electrodes and 1.0 for depth electrodes.
            mni_position: The position of the electrode contact in MNI space, overrides the default affine MNI calculation; 
                often used if you have advanced/more accurate MNI estimation
            sphere_position: The position of the electrode contact in the sphere space; surface electrodes only.
            kwargs: Other arguments to be passed to `ElectrodeSphere`.
        Returns:
            The electrode contact instance.
        Examples:
            Adds an electrode contact to the brain
            >>> e1 = brain.add_electrode_contact(number = 1, label = "LA1", position = [35,10,10], is_surface = False)
            >>> e1.get_position("ras")
            Vec3(35.0, 10.0, 10.0) [ras]
            >>> e2 = brain.add_electrode_contact(number = 2, label = "LA2", position = Vec3([5,10,10], space = "voxel"), is_surface = False)
            >>> # Automatically transform position to RAS space
            >>> e2.get_position("ras")
            Vec3(126.61447143554688, -117.5, 117.5) [ras]
        '''
        is_surface = True if is_surface else False
        if radius is None:
            radius = 2.0 if is_surface else 1.0
        contact = ElectrodeSphere(
            brain = self,
            number = number, 
            label = label, 
            position = position, 
            radius = radius,
            is_surface = is_surface,
            **kwargs)
        if mni_position is not None:
            contact.set_mni_position(mni_position)
        if sphere_position is not None:
            contact.set_sphere_position(sphere_position)
        self._electrode_contacts[ contact.number ] = contact
        return contact
    def set_electrode_keyframe(self, number : int, value : np.ndarray | list[float] | list[int] | list[str] | float | int | str, 
                               time : float | list[float] | tuple(float) | np.ndarray | None = None, 
                               name : str = "value") -> SimpleKeyframe | None:
        '''
        Low-level method to set electrode contacts keyframe (values).
        Args:
            number: The integer number of the electrode contact, starting from 1.
            value: The value of the keyframe, can be numerical or characters.
            time: The time (second) of the keyframe, default is `None` which means 0.
            name: The name of the keyframe, default is "value".
        Returns:
            The keyframe created
        '''
        contact = self._electrode_contacts.get(int(number), None)
        if contact is None:
            return None
        return contact.set_keyframe(value = value, time = time, name = name)
    def get_electrode_contact(self, number : int) -> ElectrodeSphere | None:
        '''
        Get an electrode contact from the brain.
        Args:
            number: The integer number of the electrode contact, starting from 1.
        Returns:
            The electrode contact instance or `None` if the electrode contact does not exist.
        '''
        return self._electrode_contacts.get(int(number), None)
    @property
    def electrode_contacts(self) -> dict[int, ElectrodeSphere]:
        '''
        Get all electrode contacts from the brain.
        '''
        return self._electrode_contacts
    def clean_electrodes(self):
        '''
        Remove all electrode contacts from the brain.
        '''
        contact_names = [contact.name for _, contact in self._electrode_contacts.items()]
        for contact_name in contact_names:
            self._geoms.pop(contact_name, None)
            self._electrode_contacts.pop(contact_name, None)
    def add_electrodes(self, table : str | DataFrame, space : str | None = 'ras') -> int:
        '''
        Add electrodes to the brain.
        Args:
            table: A pandas table containing the electrode information, or the path to the table. (See 'Details:')
            space: The space of the electrode coordinates, default is "ras".
        Returns:
            The number of electrodes added.
                    
        Details:
            The table (or table file) must contains at least the following columns (**case-sensitive**):
                
            * `Electrode` (int, mandatory): electrode contact number, starting from 1
                
            * `Label` (str, mandatory): electrode label string, must not be empty string
                
            * `x`, `y`, `z` (float): the coordinates of the electrode contact in the space specified by `space`.
                    
                If `space` is not specified, then the coordinates are assumed to be in the T1 space ("ras").
                    
                > If x=y=z=0, then the electrode will be hidden. (This is the default behavior of R package threeBrain)

                If `x`, `y`, `z` is not specified, then the following columns will be used in order:
                    
                * `Coord_x`, `Coord_y`, `Coord_z`: electrode coordinates in tkrRAS space (FreeSurfer space)
                * `T1R`, `T1A`, `T1S`: electrode coordinates in T1 RAS space (scanner space)
                * `MNI305_x`, `MNI305_y`, `MNI305_z`: electrode coordinates in MNI305 space
                * `MNI152_x`, `MNI152_y`, `MNI152_z`: electrode coordinates in MNI152 space
                    
                The order will be Coord_* > T1* > MNI305_* > MNI152_* to be consistent with R package threeBrain.
                
                > xyz in native (subject brain) space and MNI space can co-exist in the same table. In this case,
                > the native space coordinates will be used to show the electrodes in the native brain,
                > and the MNI space coordinates will be used to show the electrodes on the template brain.

            The following columns are optional:

            * `Radius` (float): the radius of the electrode contact, default is 1.0 for sEEG and 2.0 for ECoG
            * `Hemisphere` (str, ["auto", "left", "right"]): the hemisphere of the electrode contact, default is "auto"
                If "auto", then the hemisphere will be determined by the `FSLabel` column.
            * `Sphere_x`, `Sphere_y`, `Sphere_z` (float): the coordinates of the electrode contact in the sphere space (surface electrodes only)
            * `SurfaceElectrode` (bool): whether the electrode is a surface electrode, default is False
            * `FSLabel` (str): the FreeSurfer label of the electrode contact.
        '''
        if space is None:
            space = "ras"
        elif not space in CONSTANTS.SUPPORTED_SPACES:
            raise ValueError(f"Invalid space: {space}, supported spaces are: {CONSTANTS.SUPPORTED_SPACES}")
        # table = "/Users/dipterix/Dropbox (PennNeurosurgery)/RAVE/Samples/data/demo/PAV006/rave/meta/electrodes.csv"
        if isinstance(table, str):
            import pandas as pd
            table = pd.read_csv(table, sep = ",")
        # assume table is pandas since we don't want to import pandas here
        nrows = table.shape[0]
        valid_length = lambda l: np.isfinite(l) and l > 0 and l < 500
        for ii in range(nrows):
            row = table.iloc[ii].to_dict()
            electrode = row["Electrode"]
            label = row.get("Label", "").strip()
            if label == "":
                label = f"NoLabel{ electrode }"
            x = row.get("x", None)
            y = row.get("y", None)
            z = row.get("z", None)
            xyz = Vec3(x, y, z, space=space)
            tkr_x = row.get("Coord_x", None)
            tkr_y = row.get("Coord_y", None)
            tkr_z = row.get("Coord_z", None)
            tkr_ras = Vec3(tkr_x, tkr_y, tkr_z, space="ras_tkr")
            t1_x = row.get("T1R", None)
            t1_y = row.get("T1A", None)
            t1_z = row.get("T1S", None)
            ras = Vec3(t1_x, t1_y, t1_z, space="ras")
            mni305_x = row.get("MNI305_x", None)
            mni305_y = row.get("MNI305_y", None)
            mni305_z = row.get("MNI305_z", None)
            mni305 = Vec3(mni305_x, mni305_y, mni305_z, space="mni305")
            mni152_x = row.get("MNI152_x", None)
            mni152_y = row.get("MNI152_y", None)
            mni152_z = row.get("MNI152_z", None)
            mni152 = Vec3(mni152_x, mni152_y, mni152_z, space="mni152")
            mni_position = mni305
            if valid_length( xyz.length() ):
                position = xyz
            elif valid_length( tkr_ras.length() ):
                position = tkr_ras
            elif valid_length( ras.length() ):
                position = ras
            elif valid_length( mni305.length() ):
                position = mni305
            elif valid_length( mni152.length() ):
                position = mni152
            else:
                position = None
            if not valid_length( mni_position.length() ):
                mni_position = mni152
            if not valid_length( mni_position.length() ):
                mni_position = None
            sphere_x = row.get("Sphere_x", None)
            sphere_y = row.get("Sphere_y", None)
            sphere_z = row.get("Sphere_z", None)
            sphere_position = Vec3(sphere_x, sphere_y, sphere_z, space="sphere")
            if not valid_length( sphere_position.length() ):
                sphere_position = None
            radius = row.get("Radius", None)
            is_surface = row.get("SurfaceElectrode", False)
            fs_label = row.get("FSLabel", "Unknown")
            hemisphere = row.get("Hemisphere", "auto").lower()
            if len(hemisphere) == 0 or hemisphere[0] not in ["l", "r"]:
                hemisphere = "auto"
                # also guess the hemisphere from the FSLabel
                if re.match(r"^(left|(ctx|wm)[_-]lh)", fs_label, re.IGNORECASE):
                    hemisphere = "left"
                elif re.match(r"^(right|(ctx|wm)[_-]rh)", fs_label, re.IGNORECASE):
                    hemisphere = "right"
            else:
                if hemisphere[0] == "l":
                    hemisphere = "left"
                elif hemisphere[0] == "r":
                    hemisphere = "right"
            self.add_electrode_contact(
                number = electrode, label = label, position = position,
                is_surface = is_surface, radius = radius,
                mni_position = mni_position, sphere_position = sphere_position,
                hemisphere = hemisphere)
        return len(self._electrode_contacts)
    def set_electrode_value(self, number : int, name : str, value : list[float] | list[str] | dict | float | str, 
                            time : list[float] | float | None = None) -> SimpleKeyframe | None:
        '''
        Set value to a electrode contact.
        Args:
            number: The electrode contact number.
            name: The data name of the value.
            value: The value to set, can be a list of values or a single value.
            time: The time of the value, can be a list of times (in seconds) or a single time.
        Returns: 
            The keyframe object or None if the electrode contact is not found.
        '''
        contact = self._electrode_contacts.get(int(number), None)
        if contact is None:
            return None
        return contact.set_keyframe(value = value, time = time, name = name)
    def set_electrode_values(self, table : str | DataFrame):
        '''
        Set single or multiple values to multiple electrode contacts.
        Args: 
            table: A pandas or a path to a csv file. The see 'Details' for table contents
        Details:
            The table (or table file) contains the following columns (**case-sensitive**):

            * `Electrode` (mandatory): The electrode contact number, starting from 1
            * `Subject` (optional): The subject code of the value, default is the current subject code
            * `Time` (optional): The numeric time of the value, in seconds
            * All other columns: The the column names are the data names of the values, can 
                be combinations of letters `[a-zA-Z]`, numbers `[0-9]`, dots `.`, and underscores `_`
        Examples:
            The minimal table contains only the electrode contact number and the value:

            | Electrode | brain.response |
            |-----------|----------------|
            | 1         | 0.1            |
            | 2         | 0.2            |
            | 3         | 0.3            |


            Here's an example of the table with two variables `brain.response` and `classifier`, 
            and two electrodes `1` and `2`. The time range is `0~1` seconds.

            | Electrode | Time | brain.response | classifier |
            |-----------|------|----------------|------------|
            | 1         | 0    | 0.1            | A          |
            | 1         | 1    | 0.2            | A          |
            | 2         | 0    | 0.3            | A          |
            | 2         | 1    | 0.4            | B          |
        '''
        if isinstance(table, str):
            # table = "/Users/dipterix/rave_data/data_dir/demo/DemoSubject/rave/meta/electrodes.csv"
            import pandas as pd
            table = pd.read_csv(table, sep = ",")
        # assume table is pandas since we don't want to import pandas here
        if "Electrode" not in table.columns:
            raise LookupError(f"Invalid table, must contain column 'Electrode'.")
        time = table.get("Time", None)
        subjects = table.get("Subject", None)
        electrodes = table["Electrode"]
        electrode_numbers = electrodes.unique()
        var_names = [x for x in table.columns if x not in ["Electrode", "Time"]]
        if subjects is not None:
            subjects = subjects == self.subject_code
        else:
            subjects = True
        for electrode in electrode_numbers:
            sel = (electrodes == electrode) & subjects
            if sel.size > 0 and sel.sum() > 0:
                for name in var_names:
                    keyframe = self.set_electrode_value(
                        number = electrode, name = name, value = table[name][sel].tolist(), 
                        time = None if time is None else time[sel])
                    if isinstance(keyframe, SimpleKeyframe):
                        # get colormap
                        colormap = self._electrode_cmaps.get(name, None)
                        if colormap is None:
                            colormap = ElectrodeColormap(keyframe_name = keyframe, value_type = "continuous" if keyframe.is_continuous else "discrete")
                            self._electrode_cmaps[name] = colormap
                        colormap.update_from_keyframe( keyframe = keyframe )
        return 
    def get_electrode_colormap(self, name : str) -> ElectrodeColormap | None:
        '''
        Get the colormap of an electrode contact.
        Args:
            name: The name of the electrode keyframe (which is also the color-map name).
        Returns:
            The colormap instance or `None` if the colormap does not exist.
        '''
        return self._electrode_cmaps.get(name, None)
    # endregion
    
    def to_dict(self) -> dict:
        '''
        Convert the brain to a dict.
        Returns: 
            A dict containing the brain data.
        '''
        # global_data needs to be rebuilt
        self._globals.set_group_data(
            name = "subject_data", 
            is_cache = False,
            value = {
                'subject_code' : self.subject_code,
                'Norig': self.vox2ras.mat.tolist(),
                'Torig': self.vox2ras_tkr.mat.tolist(),
                'xfm': self.ras2mni_305.mat.tolist(),
                # FreeSurfer RAS to MNI305, should be ras_tkr2mni_305, but for compatibility, vox2vox_MNI305
                'vox2vox_MNI305': self.ras_tkr2mni_305.mat.tolist(),
                # -(self$Norig %*% solve( self$Torig ) %*% c(0,0,0,1))[1:3]
                'volume_types' : list(self._slices.keys()),
                'atlas_types' : [], # self._atlases.keys()
            })
        geom_list = []
        group_list = []
        for _, geom in self._geoms.items():
            geom_list.append(geom)
        for _, group in self._groups.items():
            group_list.append(group)
        # The config file should contain groups and geoms
        return {
            'subject_code': self.subject_code,
            'storage': self.storage.name,
            'path': self.path,
            "settings": {},
            "groups": group_list,
            "geoms": geom_list,
        }
    def build(self, path : str | None = None, dry_run : bool = False):
        '''
        Build the brain cache. If `path` is not specified, the cache will be built under the temporary directory.
        Args:
            path: The path to build the cache; default is using the `self._storage` path.
            dry_run: If True, the cache will not be built, instead, the build process will be printed to the console.
        '''
        config = self.to_dict()
        # Needs to generate a global data dict to include all global data for compatibility
        build_global = BlankPlaceholder(brain = self, is_global = True)
        build_group = GeomWrapper(brain = self, name = build_global.group_name)
        config['geoms'].insert(0, build_global)
        config['groups'].insert(0, build_group)
        build_group.set_group_data(name = '__global_data__.subject_codes', value = [self.subject_code], is_cache = False)

        # Construct colormaps
        cmaps = {}
        for _, colormap in self._electrode_cmaps.items():
            cmap_data = colormap.to_dict()
            if isinstance(cmap_data, dict):
                cmaps[ colormap.name ] = cmap_data
        default_cmap = list(cmaps.keys())[0] if len(cmaps) > 0 else None

        # Hard-code for now
        build_group.set_group_data(
            name = '__global_data__.SurfaceColorLUT', 
            value = template_path(f"lib/threeBrain_data-0/{ build_group.cache_name }/ContinuousSample.json"),
            is_cache = True
        )
        build_group.set_group_data(
            name = '__global_data__.VolumeColorLUT', 
            value = template_path(f"lib/threeBrain_data-0/{ build_group.cache_name }/FreeSurferColorLUT.json"),
            is_cache = True
        )
        build_group.set_group_data(
            name = '__global_data__.FSColorLUT', 
            value = template_path(f"lib/threeBrain_data-0/{ build_group.cache_name }/FSColorLUT.json"),
            is_cache = True
        )
        
        settings = config['settings']
        settings['title'] = ""
        settings['side_camera'] = True
        settings['side_canvas_zoom'] = 1
        settings['side_canvas_width'] = 250
        settings['side_canvas_shift'] = [0, 0]
        settings['color_maps'] = cmaps
        settings['default_colormap'] = default_cmap
        settings['hide_controls'] = False
        settings['control_center'] = [0, 0, 0]
        settings['camera_pos'] = [500, 0, 0]
        settings['font_magnification'] = 1
        settings['start_zoom'] = 1
        settings['show_legend'] = True
        settings['render_timestamp'] = True
        settings['control_presets'] = [
            "subject2", "surface_type2", "hemisphere_material", "surface_color", "map_template",
            "electrodes", "voxel", "animation", "display_highlights"
        ]
        settings['cache_folder'] = "lib/threebrain_data-0/"
        settings['lib_path'] = "lib/"
        settings['default_controllers'] = []
        settings['debug'] = True
        settings['background'] = "#FFFFFF"
        settings['token'] = None
        settings['show_inactive_electrodes'] = True
        settings['side_display'] = True
        settings['control_display'] = True
        settings['custom_javascript'] = None

        # write files
        # dry_run = False
        # path=os.path.join(ensure_default_temporary_directory(), "test")
        if path is None:
            path = self._storage.name
        init_skeleton(path, dry_run = dry_run)
        # for each group data, check if is_cache, if so, copy the file to the cache folder
        for group in config['groups']:
            group.build(path = path, dry_run = dry_run)
        # construct config.json
        if dry_run:
            print("Writing config.json...")
        else:
            import json
            s = json.dumps({
                "groups": config['groups'],
                "geoms": config['geoms'],
            }, cls = GeomEncoder)
            with open(os.path.join(path, "lib", "threebrain_data-0", "config.json"), "w") as f:
                f.write(s)
        
        # construct index.html
        if dry_run:
            print("Writing index.html...")
        else:
            with open(template_path("index.html"), "r") as f:
                index_content = "\n".join(f.readlines())
            index_content = index_content.replace("WIDGET_ID", "threebrainpy-viewer")
            widget_data = json.dumps({
                'x' : {
                    'data_filename' : 'config.json',
                    "force_render":True,
                    'settings' : settings,
                },
                "evals":[],"jsHooks":[]
            }, cls = GeomEncoder)
            index_content = index_content.replace("WIDGET_DATA", widget_data)
            index_path = os.path.join(path, "index.html")
            with open(index_path, "w") as f:
                f.write(index_content)

        # set global data
        # dict_keys(['__global_data__DemoSubject', '__global_data__.VolumeColorLUT', '__global_data__.FSColorLUT'])
        # config['groups'][0]['group_data']['__global_data__DemoSubject']
        


    
    
    
    
    
    

