import os
import shutil
import re

template_root = os.path.dirname(__file__)
sub_files = [x for x in os.listdir(template_root) if re.match(r"^[\._]", x) is None]

def init_skeleton(path : str = None, dry_run = False):
    # file the sub-directories in templates create them under `path`
    if path is None:
        path = os.getcwd()
    if not os.path.exists(path):
        if dry_run:
            print(f"Create directory: {path}")
        else:
          os.makedirs(path)
    if not dry_run :
        if not os.path.isdir(path):
            raise ValueError(f"Path {path} is not a directory.")
        if not os.access(path, os.W_OK):
            raise PermissionError(f"Path {path} is not writable.")
    # create sub-directories
    for d in sub_files:
        d_path = os.path.join(path, d)
        s_path = os.path.join(template_root, d)
        if os.path.isdir(s_path):
          if not os.path.exists(d_path):
              if dry_run:
                  print(f"Create directory: {d_path}")
              else:
                  os.makedirs(d_path)
          if dry_run:
              print(f"Copy {s_path} to {d_path}")
          else:
              shutil.copytree(s_path, d_path, symlinks=False, ignore=None, dirs_exist_ok=True, copy_function=shutil.copyfile)
        else:
          if dry_run:
              print(f"Copy {s_path} to {d_path}")
          else:
              shutil.copyfile(s_path, d_path)
    for f in ["linux.sh" , "mac.command", "simple_server.py"]:
        f_path = os.path.join(path, f)
        if os.path.exists(f_path):
            if not dry_run:
                try:
                    os.chmod(f_path, 0o777)
                except Exception as e:
                    pass
            else:
                print(f"Change permission of {f_path} to 777")



def template_path(name : str):
    path = tuple(name.split("/"))
    return os.path.join(template_root, *path)