

def streamFilter(*args,**kwargs):
    stream=args[0]
    stream.filter(**kwargs)
    return stream