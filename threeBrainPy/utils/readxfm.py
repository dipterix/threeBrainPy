import os
import re

xfm_regexp = r'^[ ]{0,}([-]{0,1}[0-9.]+)[ ]{1,}([-]{0,1}[0-9.]+)[ ]{1,}([-]{0,1}[0-9.]+)[ ]{1,}([-]{0,1}[0-9.]+)[ ;]{0,}$'

def read_xfm(path):
    '''
    Read a FreeSurfer talairach.xfm file and return a dict with keys:
    @param path: The path to the talairach.xfm file.
    @return: A dict with keys:
        'path': The absolute path to the talairach.xfm file.
        'transform': The transform matrix.
        'transform_type': The type of the transform. Always 'Linear' (Non-linear transforms are not supported yet).
    '''
    # path = '/Users/dipterix/rave_data/raw_dir/PCC/rave-imaging/fs/mri/transforms/talairach.xfm'
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} not found.")
    with open(path, "r") as f:
        s = f.readlines()
    m = [re.match(xfm_regexp, x).groups() for x in s if re.match(xfm_regexp, x) is not None]
    return {
        'path': os.path.abspath(path),
        'transform': m,
        'transform_type': 'Linear',
        'space_from': 'ras',
        'space_to': 'mni305',
    }
