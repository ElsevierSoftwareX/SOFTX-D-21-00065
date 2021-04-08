from setuptools import setup
 
setup(name='mics_library',
      version='1.0',
      description='A Python package to work with MICS data',
      license='GPLv3',
      packages=['mics_library'],
      install_requires=[
          'numpy',
          'pandas',
          'pyreadstat'],
      zip_safe=False)