import tempfile
import os
def ensure_directory(path, delete_file = False, check_writable = False):
    if os.path.exists(path):
        if os.path.isdir(path):
            if check_writable and not os.access(path, os.W_OK):
                if delete_file:
                    os.removedirs(path)
                else:
                    raise PermissionError(f"Path {path} is not writable.")
        else:
            if delete_file:
                os.remove(path)
            else:
                raise ValueError(f"Path {path} exists and is not a directory.")
    if not os.path.exists(path):
        os.makedirs(path, mode=0o777, exist_ok=True)
    return os.path.abspath(path)

def ensure_default_temporary_directory():
    return ensure_directory(os.path.join(tempfile.gettempdir(), "threeBrainPy"), delete_file = True, check_writable = True)

def ensure_temporary_directory(path = None):
    if path is None:
        path = ensure_default_temporary_directory()
    else:
        path = ensure_directory(path, delete_file = False, check_writable = True)
    return os.path.abspath(path)

def temporary_directory(prefix = None, suffix = None, dir = None, **kwargs):
    return tempfile.TemporaryDirectory(prefix = prefix, suffix = suffix, 
                                       dir = ensure_temporary_directory(dir), **kwargs)

def temporary_file(prefix = None, suffix = None, dir = None, delete = True, named = True, **kwargs):
    if named:
        return tempfile.NamedTemporaryFile(prefix = prefix, suffix = suffix, 
                                           dir = ensure_temporary_directory(dir), 
                                           delete = delete, **kwargs)
    else:
        return tempfile.TemporaryFile(prefix = prefix, suffix = suffix, 
                                      dir = ensure_temporary_directory(dir), 
                                      delete = delete, **kwargs)
