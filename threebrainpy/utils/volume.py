import os
import nibabel

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

