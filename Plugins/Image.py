import numpy as np
from scipy import signal

# Return a spectrogram image for the current stations vertical trace
# Optionals: [winLen (float),interLen (float),normType (one of sqrt,log,none)]
def spectrogramVert(stream,curTraceSta,**kwargs):
    # Ensure that the vertical trace exists...
    if curTraceSta+'Z' not in [tr.stats.station+tr.stats.channel[-1] for tr in stream]:
        return '$pass'
    # If winLen (window over which a single FFT computed) or interLen (sampling interval in time of spectrogram)...
    # ...does not exist, add in some defaults
    if 'winLen' not in kwargs.keys():
        kwargs['winLen']=1.0
    if 'interLen' not in kwargs.keys():
        kwargs['interLen']=0.5
    if kwargs['interLen']>kwargs['winLen']:
        kwargs['interLen']=0.5*kwargs['winLen']
    # Give default sqrt normalization if none are given, or
    if 'normType' not in kwargs.keys():
        kwargs['normType']='sqrt'
    elif kwargs['normType'] not in ['sqrt','log','none']:
        print('Accepted normalization "normType" args are [sqrt, log, none], assigning sqrt')
        kwargs['normType']='sqrt'
    # Grab the trace and calculate the spectrogram
    trace=stream.select(component='Z',station=curTraceSta).merge()[0]
    trace.detrend('linear')
    trace.taper(0.1,type='hann',max_length=2.0)
    sps=trace.stats.sampling_rate
    f, t, psd=signal.spectrogram(trace.data, sps,
                                 nperseg=int(sps*kwargs['winLen']),
                                 noverlap=int(sps*(kwargs['winLen']-kwargs['interLen'])))
    # Ensure the spectrogram is large enough to mean something
    if len(t)<2 or len(f)<2:
        return '$pass'
    # Normalize the psd
    if kwargs['normType']=='sqrt':
        psd=np.sqrt(psd)
    elif kwargs['normType']=='log':
        psd=np.log10(psd)
    # Scale between 0 and 1
    psd=(psd-np.min(psd))/(np.max(psd)-np.min(psd))
    return {'data':psd,'t0':trace.stats.starttime.timestamp,'tDelta':t[1]-t[0],
            'y0':f[0],'yDelta':f[1]-f[0],'label':trace.stats.station,
            'cmapRGBA':np.array([[0,0,0,255],[255,0,0,255]])}