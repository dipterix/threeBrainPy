# WebGL-based 3D Brain for Python

The project is part of [YAEL](https://yael.wiki/). 

[![Check out live demo](docs/assets/images/showcase-01.png)](https://dipterix.org/threeBrainPy/showcase-viewer/)

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

## Documentation

Please check the documentation [here](https://dipterix.org/threeBrainPy/).


## Other implementations

This Python implementation implements the core functionalities. More advanced features will come soon. 

The core implementation is in [JavaScript](https://github.com/dipterix/three-brain-js). The R implementation [threeBrain](https://github.com/dipterix/threeBrain) is also available on [CRAN](https://cran.r-project.org/package=threeBrain).

Here is a comparison of the Python vs R implementations:

| Feature | Python | R |
|---------|--------|---|
| 3D Brain | :white_check_mark: | :white_check_mark: |
| 3D Electrodes | :white_check_mark: | :white_check_mark: |
| Electrode Localization | :white_check_mark: | :heart: |
| Dashboard Integration  | :white_check_mark: | :heart: |

* :white_check_mark: = implemented
* :heart: = will implement if I get enough requests or I get grants to do so

# Sponsor

There has been no sponsor in this Python project yet. It is super hard and discouraging for software projects to apply for fundings. Your support will be greatly appreciated. Please email `help` at `rave.wiki` to join our slack channel if you want to:

* Request a demos
* Ask questions
* Use our software
* Collaborate with us


