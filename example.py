from threebrainpy.core import Brain, Vec3, Mat44, SimpleKeyframe, CONSTANTS, ElectrodeColormap
print(CONSTANTS)

import os
from threebrainpy.core import Brain

# You can replace `path` with any FreeSurfer-generated subject folder
path = os.path.join(os.environ["FREESURFER_HOME"], "subjects", "fsaverage")

brain = Brain(os.path.basename(path), path)
brain.add_slice("brain")
brain.add_surfaces("pial")
brain.render()
electrode_path = "https://raw.githubusercontent.com/dipterix/threeBrainPy/main/docs/showcase-viewer/electrodes.csv"
brain.add_electrodes(table=electrode_path)
value_path = "https://raw.githubusercontent.com/dipterix/threeBrainPy/main/docs/showcase-viewer/electrodes.csv"
brain.set_electrode_values(value_path)
brain.render()
