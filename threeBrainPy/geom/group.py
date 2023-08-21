import os
import re
import numpy as np
import shutil
from ..core.mat44 import Mat44

class GeomWrapper:
    def __init__(self, brain, name : str, layers = [0], position = [0, 0, 0]):
        # check inputs
        if len(position) != 3:
            raise ValueError(f"Invalid position: {position}, length must be 3.")
        if brain is None:
            raise ValueError(f"Brain must be <threeBrainPy.core.Brain> instance.")
        self._brain = brain
        self._subject_code = brain.subject_code
        self._name = name
        self.layers = set()
        if len(layers) > 0:
            for x in layers:
                self.layers.add(int(x))
        if len(self.layers) == 0:
            self.layers.add(0)
        self.position = np.array(position, dtype = float)
        self._group_data = {}
        self.trans_mat = Mat44()
        self.trans_mat_disabled = False
        self._cached_items = []
        self.parent_group = None
        self._cache_name = None
    

    @property
    def cache_root(self):
        return self._brain.storage.name
    @property
    def brain(self):
        return self._brain
    @property
    def name(self):
        return self._name
    @property
    def subject_code(self):
        return self._subject_code
    @property
    def cache_name(self):
        if self._cache_name is None:
            return re.sub(r'[^a-zA-Z0-9]', '_', self._name)
        return self._cache_name
    
    def set_cache_name(self, name):
        self._cache_name = name
    
    def set_group_data(self, name, value, is_cache = False, absolute_path = None):
        if is_cache:
            # value is a file path
            if absolute_path is None:
                absolute_path = os.path.abspath(value)
            if not os.path.exists(absolute_path):
                raise FileNotFoundError(f"File {absolute_path} not found.")
            value = {
                'path': value,
                'is_cache': True,
                'is_cached': True,
                'absolute_path': absolute_path,
                'file_name': os.path.basename(absolute_path),
                'is_new_cache': False,
            }
        # check if this is a manual cache
        if isinstance(value, dict):
            if value.get('is_cache', False) or value.get('is_cached', False):
                self._cached_items.append(name)
        self._group_data[name] = value

    def get_group_data(self, name, force_reload = False, ifnotfound = None):
        if force_reload or name not in self._group_data:
            if ifnotfound is None:
                raise ValueError(f"Group data {name} not found.")
            else:
                return ifnotfound
        else:
            return self._group_data[name]

    def set_subject_code(self, subject_code):
        self._subject_code = subject_code

    def get_cache_path(self, name = None, cache_root = None, normalize = True):
        if cache_root is None:
            cache_root = self.cache_root
        if name is None:
            re = os.path.join(cache_root, "lib", 'threebrain_data-0', self.cache_name)
        else:
            re = os.path.join(cache_root, "lib", 'threebrain_data-0', self.cache_name, name)
        if normalize:
            re = os.path.abspath(re)
        return re
    
    def to_dict(self):
        return {
            'name': self.name,
            'layer': tuple(self.layers),
            'position': self.position.tolist(),
            'group_data': self._group_data,
            'trans_mat': Mat44() if self.trans_mat_disabled else self.trans_mat,
            'cached_items': [x for x in self._cached_items],
            'cache_name': self.cache_name,
            'disable_trans_mat': self.trans_mat_disabled,
            'parent_group': self.parent_group,
            'subject_code': self.subject_code,
        }

    def build(self, path : str | None = None, dry_run : bool = False):
        if path is None:
            path = self.cache_root
        for name, data in self._group_data.items():
            # name = '__global_data__.SurfaceColorLUT'
            # data = self._group_data[name]
            if isinstance(data, dict) and data.get('is_cache', False):
                s_path = data.get("absolute_path", None)
                if isinstance(s_path, str) and os.path.exists(s_path):
                    # get file name
                    f_name = os.path.basename(s_path)
                    d_dirpath = self.get_cache_path(name = None, cache_root = path)
                    if not os.path.exists(d_dirpath) or not os.path.isdir(d_dirpath):
                        if os.path.exists(d_dirpath):
                            if dry_run:
                                print(f"Remove file: {d_dirpath}")
                            else:
                                os.remove(d_dirpath)
                        if dry_run:
                            print(f"Create directory: {d_dirpath}")
                        else:
                            os.makedirs(d_dirpath, exist_ok = True)
                    d_path = os.path.join(d_dirpath, f_name)
                    if os.path.isdir(s_path):
                        if dry_run:
                            print(f"Copy directory: {d_path} -> {s_path}")
                        else:
                            shutil.copytree(s_path, d_path, symlinks=False, ignore=None, dirs_exist_ok=True, copy_function=shutil.copyfile)
                    else:
                        if dry_run:
                            print(f"Copy file: {d_path} -> {s_path}")
                        else:
                            shutil.copyfile(s_path, d_path)
    def __repr__(self) -> str:
        return "\n".join([
            f"<threeBrainPy.geom.GeomWrapper ({ self.name })>",
            f"  subject_code: { self.subject_code }",
            f"  path: { self.cache_name }",
            f"  data: { list(self._group_data.keys()) }",
            f"  cached: { list(self._cached_items) }",
            ""
        ])

    

    



