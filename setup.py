from distutils.core import setup
import inspect
import os

from lazylyst.Lazylyst import __version__

SETUP_DIRECTORY = os.path.dirname(os.path.abspath(inspect.getfile(
    inspect.currentframe())))

def find_packages():
    modules = []
    for dirpath, _, filenames in os.walk(
            os.path.join(SETUP_DIRECTORY, 'lazylyst')):
        if '__init__.py' in filenames:
            modules.append(os.path.relpath(dirpath, SETUP_DIRECTORY))
    return [_i.replace(os.sep, ".") for _i in modules]

setup(
  name = 'lazylyst',
  version = __version__,
  description = 'GUI for timeseries review with a focus on seismology',
  author = 'Andrew Reynen',
  author_email = 'andrew.m.g.reynen@gmail.com',
  url = 'https://github.com/AndrewReynen/Lazylyst', 
  download_url = 'https://github.com/AndrewReynen/Lazylyst/archive/'+__version__+'.tar.gz', 
  keywords = ['seismology', 'timeseries', 'picking', 'pyqtgraph'], 
  classifiers = [],
  packages=find_packages(),
  install_requires=[
        'obspy>=1.0.2',
        'pyqtgraph==0.10.0',
        'scandir>=1.4',
        'pyproj>=1.9.5.1',
        'scipy',
        'numpy',
        'sip'
    ],
)
