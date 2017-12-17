from distutils.core import setup
import inspect
import os

from lazylyst.__init__ import __version__

SETUP_DIRECTORY = os.path.dirname(os.path.abspath(inspect.getfile(
    inspect.currentframe())))
walkPath=os.path.join(SETUP_DIRECTORY, 'lazylyst')

def getPackages():
    modules = []
    for dirPath, _, fileNames in os.walk(walkPath):
        if '__init__.py' in fileNames:
            modules.append(os.path.relpath(dirPath, SETUP_DIRECTORY))
    return [_i.replace(os.sep, ".") for _i in modules]

def getResources():
    resources=[]
    for dirPath, _, fileNames in os.walk(walkPath):
        for aFile in fileNames:
            if (aFile.split('.')[-1] in ['txt','mseed','png','xml','picks','npy'] or 
                aFile=='setGen.ini'):
                resources.append(os.path.join(os.path.relpath(dirPath, walkPath),aFile))
    return resources

setupInputs={
  'name' : 'lazylyst',
  'version' : __version__,
  'description' : 'GUI for timeseries review with a focus on seismology',
  'author' : 'Andrew Reynen',
  'author_email' : 'andrew.m.g.reynen@gmail.com',
  'license':'MIT License',
  'url' : 'https://github.com/AndrewReynen/Lazylyst', 
  'keywords' : ['seismology', 'timeseries', 'picking', 'pyqtgraph'], 
  'classifiers' : [],
  'packages':getPackages(),
  'package_data':{'lazylyst': getResources()},
  'include_package_data':True,
  'install_requires':[
        'obspy>=1.0.2',
        'pyqtgraph==0.10.0',
        'scandir>=1.4',
        'pyproj>=1.9.5.1',
        'future',
        'sip'
    ],
}

try:
    setup(**setupInputs)
except:
    from setuptools import setup
    setup(**setupInputs)