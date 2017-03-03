import numpy as np

def streamFilter(*args,**kwargs):
    # If the returned trace is to have all channels seperated on the y-axis...
    # ...note for later
    if 'sepChas' in kwargs.keys():
        doSepChas=kwargs['sepChas']
        kwargs.pop('sepChas')
    else:
        doSepChas=False
    # If want to return the raw, or derivative...
    stream=args[0]
    if kwargs['type']=='raw':
        return stream
    try:
        stream.detrend()
    except:
        stream=stream.split()
        stream.detrend()
    if kwargs['type']=='derivative':
        stream.differentiate()
    else:
        # Process the remaining arguments as obspy filter would
        stream.filter(**kwargs)
    # If the channels were to be seperated, do after filtered
    if doSepChas:
        stream=sepChas(stream)
    return stream
    
# Shift traces up/down on a per-station basis so that they do not overlap
def sepChas(stream):
    # First sort the stream by channel name
    stream.sort(keys=['channel'])
    stas=np.array([tr.stats.station for tr in stream])
    for sta in np.unique(stas):
        args=np.where(stas==sta)[0]
        offset=0
        for arg in args:
            aMin,aMax=np.min(stream[arg].data),np.max(stream[arg].data)
            stream[arg].data-=(aMin-offset)
            offset+=aMax-aMin
    return stream
        
    