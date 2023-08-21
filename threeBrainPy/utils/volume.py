import os
import nibabel
from ..core.mat44 import Mat44
from .temps import temporary_directory, temporary_file

ants_ok = False

def has_ants():
    if ants_ok:
        try:
            import ants
            return True
        except Exception as e:
            return False
    return False


def read_volume(volume_path, format = None):
    '''
    Read a volume from a file. The volume can be in 
    1. NIFTI format (suffix: .nii, .nii.gz)
    2. FreeSurfer format (suffix: .mgz/.mgh)

    @param volume_path: The path to the volume file.
    @param format: The format of the volume. 
        Choices are 'nii' or 'mgz'.
        If None, the format will be inferred from the suffix of the file name.
    '''
    # determine the format
    if format is None:
        fname = os.path.basename(volume_path).lower()
        if fname.endswith(".nii.gz") or fname.endswith(".nii"):
            format = "nii"
        elif fname.endswith(".mgz") or fname.endswith(".mgh"):
            format = "mgz"
        else:
            raise ValueError(f"Cannot infer the format of the volume from the file name {fname}.")
    # read the volume
    if has_ants():
        raise NotImplementedError("ANTS is not supported yet.")
    if format == "nii":
        # DEBUG:
        # volume_path = '/Users/dipterix/Dropbox (PennNeurosurgery)/RAVE/Samples/raw/N27/rave-imaging/fs/mri/aparc+aseg.nii'
        volume = nibabel.load(volume_path)
    else:
        # DEBUG:
        # volume_path = '/Users/dipterix/Dropbox (PennNeurosurgery)/RAVE/Samples/raw/N27/rave-imaging/fs/mri/aparc+aseg.mgz'
        volume = nibabel.freesurfer.load(volume_path)
    volume.extra['file_path_original'] = volume_path
    return volume

class VolumeWrapper():
    def __init__(self, volume, **kwargs) -> None:
        '''
        Create a volume wrapper. The volume must be either NIFTI or FreeSurfer (mgh/mgz) format.
        @param volume: The volume to be wrapped. It can be either a file path or one of the followings:
            1. nibabel.Nifti1Image
            2. nibabel.Nifti2Image
            3. nibabel.MGHImage
        '''
        if isinstance(volume, str):
            volume = read_volume(volume, **kwargs)
        self._volume = volume
        # make sure the volume is in the correct format
        if isinstance(volume, (nibabel.Nifti1Image, nibabel.Nifti2Image)):
            self._format = "nii"
        elif isinstance(volume, (nibabel.MGHImage)):
            self._format = "mgz"
        else:
            raise ValueError(f"Unsupported volume type: {type(volume)}. Please make sure this is a valid NIFTI or FreeSurfer volume.")
        pass
    @property
    def volume(self):
        return self._volume
    @property
    def format(self):
        return self._format
    @property
    def header(self):
        return self._volume.header
    @property
    def shape(self):
        return self._volume.shape
    @property
    def ndim(self):
        return self._volume.ndim
    @property
    def vox2ras(self) -> Mat44:
        return self.get_vox2ras()
    @property
    def vox2ras_tkr(self) -> Mat44:
        return self.get_vox2ras_tkr()
    def get_vox2ras(self):
        m = Mat44(self._volume.affine, space_from="voxel", space_to="ras")
        return m
    def get_vox2ras_tkr(self):
        if self._format == "nii":
            mat = self._volume.header.get_base_affine()
        else:
            mat = self._volume.header.get_vox2ras_tkr()
        m = Mat44(mat, space_from="voxel", space_to="ras_tkr")
        m.extra['source_format'] = self._format
        return m
    def get_fdata(self):
        return self._volume.get_fdata()
    def _get_filepath(self, alternative_path : str = None, normalize : bool = True) -> str:
        path = self._volume.extra.get('file_path_original', None)
        if path is None and alternative_path is not None:
            path = os.path.abspath(alternative_path)
            self._volume.to_filename(path)
            self._volume.extra['file_path_original'] = path
        if normalize:
            path = os.path.abspath(path)
        return path
    def as_cache(self):
        path = self._volume.extra.get('file_path_original', None)
        if path is None:
            if self._format == "nii":
                suffix = ".nii.gz"
            else:
                suffix = ".mgz"
            tfile = temporary_file(suffix = suffix, prefix = "volume_", delete = False)
            tfile.close()
            path = tfile.name
        path = self._get_filepath(alternative_path = path, normalize = False)
        return {
            'path': path,
            'absolute_path': os.path.abspath(path),
            'file_name': os.path.basename(path),
            'is_new_cache': False,
            'is_cache': True,
            'is_nifti': self._format == "nii",
        }
