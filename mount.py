#!/usr/bin/env python
# Taken from:
#   https://github.com/skorokithakis/python-fuse-sample

from __future__ import with_statement

import argparse
import os
import sys
import tempfile
import errno
import logging
from stat import S_IFDIR, S_IFREG
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from satoricore.image import SatoriImage
from satoricore.file import load_image
from satoricore.common import load_extension_list
from satoricore.logger import logger

import hooker
hooker.EVENTS.append(["fuse.on_stat", "fuse.on_open","fuse.on_read"])

ENCODING = sys.getdefaultencoding()


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
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)

    def chmod(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def chown(self, path, uid, gid):
        raise FuseOSError(errno.EROFS)

    def getattr(self, path, fh=None):
        st = self.satori_image.lstat(path)
        if st.get("st_mode", None) is None:
            return {"st_mode": (S_IFDIR | 0o777), "st_nlink": 2}
        return st

    def readdir(self, path, fh):
        try:
            return self.satori_image.get_dir_contents(path)
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)
        except NotADirectoryError:
            raise FuseOSError(errno.ENOTDIR)

    def readlink(self, path):
        return self.satori_image.get_attribute(path, 'link')

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
        hooker.EVENTS['fuse.on_open'](
                satori_image=self.satori_image,
                file_path=path, flags=flags
            )
        return 1
        # raise FuseOSError(errno.ENOSYS)

    def create(self, path, mode, fi=None):
        raise FuseOSError(errno.EROFS)

    def read(self, path, length, offset, fh):
        # Use immutable object to return a value from hook
        value = {'return':None}
        hooker.EVENTS['fuse.on_read'](
                satori_image=self.satori_image, 
                file_path=path, length=length, offset=offset, fh=fh,
                value=value,
            )
        if value['return'] is None:
            raise FuseOSError(errno.ENOSYS)
        ret = bytes(value['return'], ENCODING)
        return ret

    def write(self, path, buf, offset, fh):
        raise FuseOSError(errno.EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EROFS)

    def flush(self, path, fh):
        raise FuseOSError(errno.ENOSYS)

    def release(self, path, fh):
        raise FuseOSError(errno.ENOSYS)

    def fsync(self, path, fdatasync, fh):
        raise FuseOSError(errno.ENOSYS)


def main_fuse(mountpoint, root):
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


def main():
    global ENCODING
    parser = argparse.ArgumentParser()
    parser.add_argument("SatoriFile", help="The SatoriImage file to mount")
    parser.add_argument("--mountpoint", help="The directory to use as mount target")
    parser.add_argument("--encoding",
        help="""The Text Encoding to use for 'open("..","r")' System calls """,
        default=ENCODING,
        )
    parser.add_argument(
        '-l', '--load-extensions',
        help='Load the following extensions',
        action='append',
        default=[],
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)

    ENCODING = args.encoding

    load_extension_list(args.load_extensions)

    mountpoint = args.mountpoint
    use_temp_dir = False
    if mountpoint is None:
        mountpoint = tempfile.mkdtemp(prefix='satori_mnt_')
        use_temp_dir = True

    filename = args.SatoriFile
    image = load_image(filename)
    # print (type(image))
    logger.warn("Mounting Image at: '{}'".format(mountpoint))

    try:
        main_fuse(mountpoint, image)
    finally:
        if use_temp_dir :
            logger.warn("[!] Cleaning up '{}'".format(mountpoint))
            os.rmdir(mountpoint)


if __name__ == '__main__':
    main()
