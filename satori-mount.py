#!/usr/bin/env python
# Taken from:
#   https://github.com/skorokithakis/python-fuse-sample

from __future__ import with_statement

import os
import sys
import errno
import logging
from stat import S_IFDIR, S_IFREG

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from satoricore.image import SatoriImage
from satoricore.serialize import load_image


class Passthrough(LoggingMixIn, Operations):
    def __init__(self, root, satori_image, read_only=True):
        self.root = root
        self.read_only = read_only
        self.satori_image = satori_image

    # Helpers
    # =======

    def _full_path(self, partial):
        partial = partial.lstrip("/")
        path = os.path.join(self.root, partial)
        return partial

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)
        return True
        # if not os.access(full_path, mode):
        #     raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def chown(self, path, uid, gid):
        raise FuseOSError(errno.EROFS)

    def getattr(self, path, fh=None):
        # Merge stat and times dicts
        try:
            st = self.satori_image.get_attribute(path, 'stat')
            st.update(self.satori_image.get_attribute(path, 'times'))
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)

        if st.get("mode", None) is None:
            return {"st_mode": (S_IFDIR | 0o777), "st_nlink": 2}

        # Append "st_" to all keys
        return {"st_" + k: st[k] for k in st.keys()}

    def readdir(self, path, fh):
        # full_path = self._full_path(path)

        try:
            return self.satori_image.get_dir_contents(path)
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)
        except NotADirectoryError:
            raise FuseOSError(errno.ENOTDIR)

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        raise FuseOSError(errno.EROFS)

    def rmdir(self, path):
        raise FuseOSError(errno.EROFS)

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def statfs(self, path):
        try:
            st = self.satori_image.get_attribute(path, 'statfs')
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)

        # Append "f_" to all keys
        return {"f_" + k: st[k] for k in st.keys()}

    def unlink(self, path):
        raise FuseOSError(errno.EROFS)

    def symlink(self, name, target):
        raise FuseOSError(errno.EROFS)

    def rename(self, old, new):
        raise FuseOSError(errno.EROFS)

    def link(self, target, name):
        raise FuseOSError(errno.EROFS)

    def utimens(self, path, times=None):
        raise FuseOSError(errno.EROFS)

    # File methods
    # ============

    def open(self, path, flags):
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        raise FuseOSError(errno.EROFS)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        raise FuseOSError(errno.EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EROFS)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(mountpoint, root):
    FUSE(
        Passthrough(
            mountpoint,
            root,
            ),
        mountpoint,
        foreground=True,
        # nothreads=True,
        # nonempty=True,
        )

if __name__ == '__main__':
    mountpoint = sys.argv[1]
    filename = sys.argv[2]
    image = load_image(filename)

    logging.basicConfig(level=logging.DEBUG)
    main(mountpoint, image)
