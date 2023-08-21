import os
import re
import tempfile
from copy import deepcopy
from .mat44 import Mat44
from ..geom.group import GeomWrapper
from ..geom.geometry import GeometryTemplate
from ..geom.datacube import VolumeSlice, VolumeCube
from ..geom.blank import BlankPlaceholder
from ..geom.surface import CorticalSurface
from ..templates import init_skeleton, template_path
from ..utils import CONSTANTS, VolumeWrapper, read_xfm
from ..utils.serializer import GeomEncoder

MNI305_TO_MNI152 = Mat44(CONSTANTS.MNI305_TO_MNI152, space_from="mni305", space_to="mni152")

class Brain(object):
    def _update_matrices(self, volume_files = [], update = 1):
        '''
        Update voxel-to-ras and voxel-to-tkrRAS matrices.
        @param volume_files: A list of volume files to be used to update the matrices.
        @param update: 
            0: do not update, but will initialize if not exists; 
            1: update if there is a better one;
            2: force update.
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

    def __init__(self, subject_code, path, work_dir = None):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Brain path {path} not found.")
        if re.match(r"^[a-zA-Z][a-zA-Z0-9_-]{0,}$", subject_code) is None:
            raise ValueError(f"Invalid subject code: {subject_code}")
        self._path = os.path.abspath(path)
        self._subject_code = subject_code
        self._template_subject = "N27"
        self._storage = tempfile.TemporaryDirectory(prefix = subject_code, dir = work_dir)
        # set up geoms
        self._groups = {}
        self._geoms = {}
        self._slices = {}
        self._surfaces = {}
        self._volumes = {}
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
        return self._subject_code
    # region <paths>
    @property
    def path(self):
        return self._path
    @property
    def path_mri(self):
        return os.path.join(self._path, "mri")
    @property
    def path_surf(self):
        return os.path.join(self._path, "surf")
    @property
    def storage(self):
        return self._storage
    # endregion
    
    # region <transforms>
    @property
    def vox2ras(self) -> Mat44:
        if isinstance(self._vox2ras, Mat44):
            return self._vox2ras
        m = Mat44(space_from="voxel", space_to="ras")
        m.extra["missing"] = True
        return m
    @property
    def vox2ras_tkr(self) -> Mat44:
        if isinstance(self._vox2ras_tkr, Mat44):
            return self._vox2ras_tkr
        m = Mat44(space_from="voxel", space_to="ras_tkr")
        m.extra["missing"] = True
        return m
    @property
    def ras2ras_tkr(self) -> Mat44:
        return self.vox2ras_tkr * (~self.vox2ras)
    @property
    def ras2mni_305(self) -> Mat44:
        if isinstance(self._ras2mni_305, Mat44):
            return self._ras2mni_305
        m = Mat44(space_from="ras", space_to="mni305")
        m.extra["missing"] = True
        return m
    @property
    def ras2mni_152(self) -> Mat44:
        return MNI305_TO_MNI152 * self.ras2mni_305
    @property
    def ras_tkr2mni_305(self) -> Mat44:
        return self.ras2mni_305 * self.vox2ras * (~self.vox2ras_tkr)
    @property
    def ras_tkr2mni_152(self) -> Mat44:
        return MNI305_TO_MNI152 * self.ras_tkr2mni_305
    def get_transform(self, space_from : str, space_to : str) -> Mat44:
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
        Get a transform matrix from `space_from` to `space_to`.
        @param space_from: The space from which the transform matrix is defined.
        @param space_to: The space to which the transform matrix is defined.
        @param transform: The transform matrix. If `transform` is not specified, then the transform matrix will be identity matrix
        @return: The transform matrix.
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
    def add_global_data(self, name, value, is_cache = False, absolute_path = None):
        self._globals.set_group_data(name = name, value = value, is_cache = is_cache, absolute_path = absolute_path)
    def get_global_data(self, name):
        return self._globals.get_group_data(name = name)
    def add_group(self, name, position = [0,0,0], layers = [CONSTANTS.LAYER_USER_MAIN_CAMERA_0], exists_ok = True) -> GeomWrapper:
        group = self._groups.get(name, None)
        if group is None:
            group = GeomWrapper(self, name = name, position = position, layers = layers)
            self._groups[name] = group
        elif not exists_ok:
            raise ValueError(f"Group {name} already exists.")
        else:
            group.set_position(position)
            group.set_layers(layers)
        return group
    def get_group(self, name):
        return self._groups.get(name, None)
    def has_group(self, name):
        return name in self._groups
    def ensure_group(self, name, **kwargs):
        if self.has_group(name):
            return self.get_group(name)
        return self.add_group(name = name, exists_ok = True, **kwargs)
    def set_group_data(self, name, value, is_cache = False, absolute_path = None, auto_create = True) -> None:
        if auto_create:
            self.ensure_group(name = name)
        group = self.get_group(name)
        if group is None:
            raise ValueError(f"Group {name} not found.")
        group.set_group_data(name = name, value = value, is_cache = is_cache, absolute_path = absolute_path)
        return None
    def get_global_data(self, name, force_reload = False, ifnotfound = None):
        group = self.get_group(name)
        if group is None:
            return ifnotfound
        return group.get_group_data(name = name, force_reload = force_reload, ifnotfound = ifnotfound)
    # endregion
    
    # region <Geometries>
    def get_geometry(self, name):
        return self._geoms.get(name, None)
    def has_geometry(self, name):
        return name in self._geoms
    # endregion
    
    # region <MRI slices>
    def add_slice(self, slice_prefix : str = "brain.finalsurfs", name : str = "T1"):
        '''
        Add a (MRI) volume slice to the brain. The slices will be rendered in side canvas using datacube (JS).
        @param slice_prefix: The prefix of the slice file. 
        @param name: The name of the slice, currently only "T1" is supported.
        @example:
            # Adds brain.finalsurfs.mgz or brain.finalsurfs.nii[.gz] to the brain slices
            brain.add_slice(slice_prefix = "brain.finalsurfs", name = "T1")
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
    def get_slice(self, name):
        return self._slices.get(name, None)
    def get_slices(self):
        return self._slices
    def has_slice(self, name):
        return name in self._slices
    # endregion
    
    # region <Atlases/CT/3D voxels>
    def add_volume(self, volume_prefix : str, is_continuous : bool, name : str = None) -> dict | None:
        '''
        Add a (Atlas/CT/3D voxel) volume cube to the brain. The VolumeCube will be rendered in main canvas using datacube2 (JS).
        @param volume_prefix: The prefix of the volume file. 
        @param is_continuous: Whether the volume is continuous or discrete. 
            The color map for continuous and discrete values are set separately.
            For continuous values, the volume will be rendered using RedFormat (single-channel shader). 
                The color will be assgined according to the volume value (density).
            For discrete values, the volume will be rendered using RGBAFormat (four-channel shader). 
                The volume data will be used as the color index, and the color map will be set separately.
                The color index must be integer, and the color map must be a list of RGBA colors.
        @param name: The name of the volume, default is to automatically derived from the volume_prefix. 
            Please set name to "CT" is the volume file is CT for localization
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
        return self._surfaces.get(surface_type, None)
    def has_surface_type(self, surface_type : str) -> bool:
        return surface_type in self._surfaces
    # endregion
    
    
    def to_dict(self):
        '''
        Convert the brain to a dict.
        @return: A dict containing the brain data.
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
    def build(self, path = None, dry_run = False):
        '''
        Build the brain cache. If `path` is not specified, the cache will be built under the temporary directory.
        @param path: The path to build the cache.
        @param dry_run: If True, the cache will not be built, instead, the build process will be printed to the console.
        '''
        config = self.to_dict()
        # Needs to generate a global data dict to include all global data for compatibility
        build_global = BlankPlaceholder(brain = self, is_global = True)
        build_group = GeomWrapper(brain = self, name = build_global.group_name)
        config['geoms'].insert(0, build_global)
        config['groups'].insert(0, build_group)
        build_group.set_group_data(name = '__global_data__.subject_codes', value = [self.subject_code], is_cache = False)

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
        settings['color_maps'] = []
        settings['default_colormap'] = None
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
            index_content = index_content.replace("WIDGET_ID", "threeBrainPy-viewer")
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
        


    
    
    
    
    
    

