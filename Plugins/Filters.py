
def streamFilter(*args,**kwargs):
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
        stream.filter(**kwargs)
    return stream