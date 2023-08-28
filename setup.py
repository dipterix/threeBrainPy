from setuptools import setup, find_packages

import os

long_description = open("README.md").read()

def read(rel_path: str) -> str:
      here = os.path.abspath(os.path.dirname(__file__))
      with open(os.path.join(here, rel_path)) as fp:
            return fp.read()


def get_version(rel_path: str) -> str:
      for line in read(rel_path).splitlines():
            if line.startswith("__version__"):
                  delim = '"' if '"' in line else "'"
                  return line.split(delim)[1]
      raise RuntimeError("Unable to find version string.")

setup(
      name='threebrainpy',
      version=get_version("threebrainpy/_version.py"),
      description='Your Advanced Electrode Localizer Viewer for Python',
      long_description=long_description,
      long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
      url='https://github.com/dipterix/threeBrainPy',
      author='Zhengjia Wang',
      author_email='dipterix.wang@gmail.com',
      license='Mozilla Public License 2.0 (MPL 2.0)',
      classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 3 - Alpha',

            # Indicate who your project is intended for
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Topic :: Multimedia :: Graphics :: 3D Rendering',
            'Topic :: Scientific/Engineering :: Human Machine Interfaces',
            'Topic :: Scientific/Engineering :: Visualization',
            "Operating System :: OS Independent",

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 3',
      ],
      keywords='iEEG, DBS, Visualization, Neuroscience, Electrophysiology, Electrode, Localizer',
      project_urls={
            'Project Website': 'https://yael.wiki/',
            'Source': 'https://github.com/dipterix/threeBrainPy/',
            'Bug Reports': 'https://github.com/dipterix/threeBrainPy/issues',
      },
      packages=find_packages(),  # Automatically find all packages in the project
      package_data={
            'threebrainpy': [
                  'templates/*', 'templates/lib/*/*', 'templates/lib/threebrain_data-0/__global_data/*',
                  'extensions/labextension/*', 'extensions/nbextension/*',
            ],
      },
      python_requires='>=3',
      install_requires=[
            'numpy',
            'nibabel',
            'pandas',
            'matplotlib',
      ],
)
