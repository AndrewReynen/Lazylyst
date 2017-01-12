# Testing

dicti={'color':'g'}
def func(color='b'):
    print color
func(**dicti)
func()

string = "abc=123,xyz=456"

print dict(x.split('=') for x in string.split(','))


import os
print os.path.realpath(__file__)
print os.path.dirname(__file__)
print os.getcwd()