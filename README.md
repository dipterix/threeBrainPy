# WebGL-based 3D Brain for Python

The project is part of [YAEL](https://yael.wiki/). 

The script is under construction. See the [R package threeBrain](https://github.com/dipterix/threeBrain) or [JavaScript library three-brain-js](https://github.com/dipterix/three-brain-js)

## Installation

### Install from `pypi`:

```sh
# Bare minimal
pip install threebrainpy

# to allow Jupyter support
pip install threebrainpy threebrainpywidget
```


### Install from `Github`:

```sh
pip install pandas matplotlib
pip install git+https://github.com/dipterix/threebrainpy
```

### Test the installation

Launch Python with your favorite editor, run the following Python commands. If you don't have `FreeSurfer` installed, replace `path` with any fs subject. If you don't have any, go to [sample templates](https://github.com/dipterix/threeBrain-sample/releases) and download one.

```python
import os
from threebrainpy.core import Brain

# You can replace `path` with any FreeSurfer-generated subject folder
path = os.path.join(os.environ["FREESURFER_HOME"], "subjects", "fsaverage")

brain = Brain(os.path.basename(path), path)
brain.add_slice("brain")
brain.add_slice("brain.finalsurf")
brain.add_surfaces("pial")
brain.render()
```

