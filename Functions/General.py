
# Go to the next pick type (in alphabetical order)
def togglePickMode(*args,**kwargs):
    curMode=args[0]
    availPickModes=sorted([str(key) for key in args[1].keys()])
    if curMode in availPickModes:
        idx=availPickModes.index(curMode)
    else:
        idx=0
    idx=(idx+1)%len(availPickModes)
    print 'Picking mode: '+availPickModes[idx]
    return availPickModes[idx]
    