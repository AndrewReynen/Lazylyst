# Author: Andrew.M.G.Reynen
from future.utils import iteritems

import numpy as np
from obspy import UTCDateTime

# Convert a string into easy to read text, assumes no lists
def dict2Text(aDict):  
    # Get all values first as strings
    keys=np.array([key for key,val in iteritems(aDict)])
    vals=np.array([str(val) for key,val in iteritems(aDict)])
    # Sort them alphabetically (better than random atleast)
    argSort=np.argsort(keys)
    vals=vals[argSort]
    keys=keys[argSort]
    # Put them all into one larger string   
    string=''
    for i in range(len(vals)):
        string+=keys[i]+'='+vals[i]+',' 
    if len(string)>0: 
        string=string[:-1]
    return string
    
# Convert text into a dictionary,assumes no lists
def text2Dict(text):
    if '=' not in text:
        return {}
    aDict=dict(x.split('=') for x in text.split(','))
    # Check if any of the values represent type other than string
    for key,val in iteritems(aDict):
        # Do not convert numbers to bool
        if val=='True':
            aDict[key]=True
        elif val=='False':
            aDict[key]=False
        # Otherwise see if it is a number
        else:
            try:
                if '.' in val:
                    aDict[key]=float(val)
                else:
                    aDict[key]=int(val)
            # If none of the above, leave as a string
            except:
                aDict[key]=str(val)
    return aDict
    
# Return the UTCDateTime from the forced file naming convention
def getTimeFromFileName(fileName):
    timeStr=fileName.split('_')[1].replace('.'+fileName.split('.')[-1],'')
    return UTCDateTime().strptime(timeStr,'%Y%m%d.%H%M%S.%f')


# Get the string representing the given station via the trace object
def getStaStr(tr):
    return str('.'.join([tr.stats.network,tr.stats.station,tr.stats.location]))