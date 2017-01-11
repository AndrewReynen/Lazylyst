from PyQt4 import QtGui

# Default Preferences
def defaultPreferences(main):
    pref={
    'staPerPage':Pref(tag='staPerPage',val=6,dataType=int,
                      func=main.updateStaPerPage),
    'evePreTime':Pref(tag='evePreTime',val=-60,dataType=int),
    'evePostTime':Pref(tag='evePostTime',val=120,dataType=int)
    }
    return pref

# Capabilities for preferences
class Pref(object):
    def __init__(self,tag=None,val=None,dataType=str,
                 dialog=QtGui.QInputDialog,
                 dialogSuggest='Enter text:',
                 func=None):
        self.tag=tag # The preference key, and user visible name
        self.dataType=dataType # What kind of data is expected upon update
        self.val=val # The preference value
        self.dialog=dialog() # The dialog which will pop up to return a value
        self.dialogSuggest=dialogSuggest # The text used to assist user in updating a value
        self.func=func # Function which is called on successful updates
    
    # If the key was asked to be updated
    def update(self,hostWidget,init=False):
        # If this is the original initalization, don't ask for new value
        if not init:
            # Show what the value was before
            self.dialog.setTextValue(str(self.val))
            # Get the new value
            val,ok=self.dialog.getText(hostWidget, 'Update '+self.tag, self.dialogSuggest)
            try:
                self.val=self.dataType(val)
            except:
                print 'Data type does not conform to '+self.tag+', skipped update'
                return
        # If the value was updated, queue off its function
        if self.func!=None: self.func()