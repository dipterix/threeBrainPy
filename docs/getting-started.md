## Installation

### Install from `pypi`:

```sh
# Bare minimal
pip install threebrainpy

# If you want JupyterLab support
pip install threebrainpy threebrainpywidget
```

## Simple example

Launch Python with your favorite editor, run the following Python commands. If you don't have `FreeSurfer` installed, replace `path` with any fs subject. If you don't have any, go to [sample templates](https://github.com/dipterix/threeBrain-sample/releases){:target="_blank"} and download one.

```py
import os
from threebrainpy.core import Brain

# You can replace `path` with any FreeSurfer-generated subject folder
path = os.path.join(os.environ["FREESURFER_HOME"], "subjects", "fsaverage")

brain = Brain(os.path.basename(path), path)
brain.add_slice("brain")
brain.add_surfaces("pial")
brain.render()
```

## Example: add electrodes

Easiest way to add electrodes is via a `csv` table. Please see [documentation](/api-core-brain/#threebrainpy.core.brain.Brain.add_electrodes){:target="_blank"}. Here is [a toy-example table](/showcase-viewer/electrodes.csv){:target="_blank"}. A bare-minimal table should contain at lease 5 columns:

|     Electrode       |       T1R       |       T1A       |       T1S       |       Label       |
|---------------------|-----------------|-----------------|-----------------|-------------------|
| int (start from 1)  | float (T1 MRI R)| float (T1 MRI A)| float (T1 MRI S)| str               |


```py
# Read electrodes.csv from github
brain.add_electrodes(table="electrodes.csv")
```
