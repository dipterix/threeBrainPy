## Prerequisites

* Minimum: `python>=3.8`, `setuptools>=43.0.0`, `wheel`

## Set up development environment

Please fork this repository first. Then you can either pull from `git`, or download, and un-zip the repository.

Once downloaded, open terminal, and navigate to the repository folder, run the following commands:

```sh
python -m venv .venv
source ./.venv/bin/activate
```

This will create a virtual environment to install all packages needed for development.

Next, choose from the following cases, depending on which component you want to contribute.

* Standard dependence

```sh
python -m pip install -r requirements.txt
```

* Full dependence

```sh
python -m pip install -r requirements-dev.txt
```

## Test configuration

#### Install local package as "dev" package

```sh
python -m pip install -e . --no-deps
```

Next, use the following Python script to test installations. If you don't have `FreeSurfer` installed, replace `path` with any fs subject. If you don't have any, go to [sample templates](https://github.com/dipterix/threeBrain-sample/releases) and download one.

```python
import os
from threebrainpy.core import Brain

# You can replace `path` with any FreeSurfer-generated subject folder
path = os.path.join(os.environ["FREESURFER_HOME"], "subjects", "fsaverage")
brain = Brain(os.path.basename(path), path)
brain.add_slice("brain")
brain.add_surfaces("pial")
brain.render()

```

You will know the module has been installed correctly. You will know if you fail as well.

#### Documentation

Run the following `mkdocs` command.

```sh
mkdocs gh-deploy
```

## Why not `conda`

I don't know how to set up `.vscode` preferences for conda. If you know how to, please help :)

<!--

Note for myself:

To update the package on `testpypi`, run the following commands:

```sh
python3 -m pip install --upgrade build twine
python3 -m build
python3 -m twine upload --repository testpypi dist/*
```

-->