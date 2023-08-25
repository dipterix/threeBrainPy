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
      name='threeBrainPy',
      version=get_version("threeBrainPy/__init__.py"),
      author='Zhengjia Wang',
      author_email='dipterix.wang@gmail.com',
      description='WebGL-base Brain Viewer for Python',
      long_description=long_description,
      long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
      url='https://github.com/dipterix/threeBrainPy',
      packages=find_packages(),  # Automatically find all packages in the project
      package_data={
            'threeBrainPy': ['templates/*'],
      },
      classifiers=[
            'Development Status :: 0 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MPL 2.0 License',
            'Programming Language :: Python :: 3',
            'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='your, keywords, here',
      python_requires='>=3.8',
      install_requires=[
            'numpy',
            'nibabel',
      ],
)
