from setuptools import setup, find_packages

with open('README.md') as file:
    long_description = file.read()

with open("neuro3d/__init__.py") as f:
    for line in f.readlines():
        if "__version__" in line:
            exec(line.strip())
            break
    else:
        raise IOError("Version not specified in __init__")

setup(name='neuro3d',
      version=__version__,
      description='Blender toolkit for visualizing neurons and simulation data',
      long_description=long_description,
      long_description_content_type="text/markdown",
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
