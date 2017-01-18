

def streamFilter(*args,**kwargs):
    stream=args[0]
    stream.detrend()
    stream.filter(**kwargs)
    return stream