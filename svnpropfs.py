#!/usr/bin/env python2.6

from __future__ import with_statement

import os
from errno import *
from stat import *
from sys import argv, exit
import time
import re

from fuse import FUSE, Operations, LoggingMixIn, fuse_get_context

import pysvn

class SvnPropFS(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = os.path.realpath(root)
        self.client = pysvn.Client()
        try:
            info = self.client.info(self.root)
        except:
            print 'source is not an subversion working directory'
            exit(1)
        self.propregex = re.compile(r"^\.(?P<name>[^#]*)#(?P<prop>[a-zA-Z_:][a-zA-Z0-9_:.-]*)$")

    def __call__(self, op, path, *args):
        return super(SvnPropFS, self).__call__(op, os.path.normpath(self.root + path), *args)
    
    def access(self, path, mode):
        if not os.access(path, mode):
            raise OSError(EACCES, '')
    
    def chmod(self, path, mode):
        return os.chmod(path, mode)

    def chown(self, path, uid, gid):
        return os.chown(path, uid, gid)

    def create(self, path, mode):
        return os.open(path, os.O_WRONLY | os.O_CREAT, mode)

    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        return os.fsync(fh)

    def getattr(self, path, fh=None):
        dirpath = os.path.dirname(path)
        name = os.path.basename(path)
        m = self.propregex.match(name)
        if m == None:
            st = os.lstat(path)
            return dict((key, getattr(st, key)) for key in ('st_atime',
                'st_ctime',
                'st_gid',
                'st_mode',
                'st_mtime',
                'st_nlink',
                'st_size',
                'st_uid'))
        else:
            if len(m.group('name')) == 0:
                srcname = dirpath
            else:
                srcname = os.path.join(dirpath, m.group('name'))
            prop = dict()
            try:
                prop = self.client.propget(m.group('prop'), srcname, recurse=False)
            except:
                raise OSError(ENOENT, '')
            print prop
            if len(prop) == 0:
                raise OSError(ENOENT, '')
            return dict(
                st_mode=(S_IFREG | 0644),
                st_nlink=1,
                st_size=len(prop[srcname]),
                st_ctime=time.time(),
                st_mtime=time.time(),
                st_atime=time.time())

    getxattr = None

    def link(self, target, source):
        return os.link(source, target)
    
    listxattr = None
    mkdir = os.mkdir
    mknod = os.mknod
    open = os.open
        
    def read(self, path, size, offset, fh):
        os.lseek(fh, offset, 0)
        return os.read(fh, size)

    def readdir(self, path, fh):
        origpath = path[len(self.root):]
        ls = os.listdir(path)
        if '.svn' in ls:
            ls.remove('.svn')

        out = ['.', '..'] + ls

        try:
            uid, gid, pid = fuse_get_context()
            comm = os.path.basename(os.readlink('/proc/%d/exe' % pid))
        except:
            comm = ''

        # for anything that starts with svn we pretend that there are no
        # property files
        if comm in ['svn', 'svnversion', 'svnadmin', 'svnlook', 'kdesvn']:
            return out

        for name, prop_dict in self.client.proplist(path, depth=pysvn.depth.files):
            if  name == path:
                name = ''
            else:
                name = os.path.basename(name)
            for prop in prop_dict.keys():
                out += ['.' + name + '#' + prop]
        return out

    readlink = os.readlink
    
    def release(self, path, fh):
        return os.close(fh)
        
    def rename(self, old, new):
        return os.rename(old, self.root + new)
    
    rmdir = os.rmdir
    
    def statfs(self, path):
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
    
    def symlink(self, target, source):
        return os.symlink(source, target)
    
    def truncate(self, path, length, fh=None):
        with open(path, 'r+') as f:
            f.truncate(length)
    
    unlink = os.unlink
    utimens = os.utime
    
    def write(self, path, data, offset, fh):
        os.lseek(fh, offset, 0)
        return os.write(fh, data)
    

if __name__ == "__main__":
    if len(argv) != 2:
        print 'usage: %s <svn-work-tree>' % argv[0]
        exit(1)

    mountpoint = os.path.realpath(argv[1])
    shadowmountpoint = os.path.join(os.path.dirname(mountpoint), '.' + os.path.basename(mountpoint)) + '.svnpropfs'
    try:
        os.rename(mountpoint, shadowmountpoint)
        os.mkdir(mountpoint, os.stat(shadowmountpoint).st_mode)
        fuse = FUSE(SvnPropFS(shadowmountpoint), mountpoint, foreground=True, nothreads=True, fsname=argv[1])
    except BaseException, e:
        print repr(e)
    finally:
        os.rmdir(mountpoint)
        os.rename(shadowmountpoint, mountpoint)
