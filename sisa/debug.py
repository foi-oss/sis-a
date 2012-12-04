from __future__ import print_function

DEBUG = False

def log(*args, **kwargs):
  if DEBUG == True:
    print(*args, **kwargs)