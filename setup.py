from setuptools import setup, find_packages

with open('README.txt') as file:
    long_description = file.read()

with open('releases/latest.txt') as file:
    version = file.read()

setup(name='neuro3d',
      version=version,
      description='Interface for Blender <-> NEURON',
      long_description=long_description,
      author='Robin De Schepper',
      author_email='robingilbert.deschepper@unipv.it',
      url='https://github.com/Helveg/neuro3d',
      packages=find_packages(),
      keywords=["Blender", "neuron", "neuroscience", "visualization", "neural networks", "neurons", "3D"],
      license="GPLv3",
      install_requires=[],
      classifiers=[
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Natural Language :: English",
          "Operating System :: MacOS",
          "Operating System :: Microsoft :: Windows",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Topic :: Scientific/Engineering :: Visualization",
      ]
)
