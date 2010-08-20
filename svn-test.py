#! /usr/bin/env python2.6

import pysvn
import sys
import os
import re
from os.path import realpath, basename, normpath

client = pysvn.Client()

#props = client.propget(sys.argv[1], sys.argv[2], recurse=False)
#print props
#for prop in props:
#    sys.stdout.write(props[prop])

#entries = client.proplist(sys.argv[1], depth=pysvn.depth.files)
#for entry in entries:
#    print '%s:' % entry[0],
#    for prop in entry[1].keys():
#        print ' %s' % prop,
#    print

#ls = os.listdir(sys.argv[1])
#for p in ls:
#    print p

#p = sys.argv[1]
#pl = p + '/'
#print pl[len(p):]

#root = realpath(sys.argv[1])
#path = sys.argv[2]
#norm = normpath(root + path)
#plpaths = client.proplist(norm, depth=pysvn.depth.files)
#print plpaths
#for name, prop_dict in plpaths:
#    if  name == norm:
#        name = ''
#    else:
#        name = basename(name) + '#'
#    for prop in prop_dict.keys():
#        print '.#' + name + prop
#

rx = re.compile(r"^\.(?:#(?P<name>.+))?#(?P<prop>[a-zA-Z_:][a-zA-Z0-9_:.-]*)$")
m = rx.match(sys.argv[1])
if m != None:
    print m.group('name')
    print m.group('prop')
