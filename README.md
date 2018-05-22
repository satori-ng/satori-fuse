# satori-fuse
Utility to mount *Satori Images* in the Filesystem

![logo6](https://github.com/satori-ng/Logos/blob/master/logos/light/logo6.png)

[![PyPI version](https://badge.fury.io/py/satori-fuse.svg)](https://pypi.org/project/satori-fuse) - `pip install satori-fuse`

*Satori Image Files* contain a structured copy of a Filesystem (created with [satori-imager](https://github.com/satori-ng/satori-imager)). This Filesystem image can be mounted using *FUSE* under a directory just like a *USB drive device*.

### The `satori-mount` entrypoint

```bash
$ satori-mount -h
usage: satori-mount [-h] [--mountpoint MOUNTPOINT] SatoriFile

positional arguments:
  SatoriFile            The SatoriImage file to mount

optional arguments:
  -h, --help            show this help message and exit
  --mountpoint MOUNTPOINT
                        The directory to use as mount target
```

Given a *SatoriImage File* named `image.json.gz` containing an image of an `/etc` directory, it can be mounted under the `/mnt/satori_target` directory with:
```bash
$ satori-mount --mountpoint /mnt/satori_target image.json.gz
```

If `--mountpoint` is not specified, a mount directory will be created under `/tmp`

```bash
$ satori-mount image.json.gz
[+] Mounting Image at: '/tmp/satori_mnt_xwabe7ar'
[...]
```



#### The internal file structure can then be explored with `ls`:

```bash
$ ls /tmp/satori_mnt_xwabe7ar
etc
```
```bash
$ ls /tmp/satori_mnt_xwabe7ar/etc
abrt                        foomatic        magic                     rpc
adjtime                     fprintd.conf    mailcap                   rpm
aliases                     fstab           makedumpfile.conf.sample  rwtab
alsa                        fuse.conf       man_db.conf               rwtab.d
alternatives                fwupd           mcelog                    rygel.conf
[...]
```
```bash
$ ls -l /tmp/satori_mnt_xwabe7ar/etc
total 1968
drwxr-xr-x.  3 root root     4096 Feb 17 20:50 abrt
-rw-r--r--.  1 root root       16 Feb 17 20:53 adjtime
-rw-r--r--.  1 root root     1518 Sep  4  2017 aliases
drwxr-xr-x.  2 root root     4096 Feb 17 20:50 alsa
drwxr-xr-x.  2 root root     4096 Apr 12 12:44 alternatives
-rw-r--r--.  1 root root      541 Aug  2  2017 anacrontab
[...]
```

#### Or with `find`:

```bash
$ find /tmp/satori_mnt_xwabe7ar/etc -name passwd
/tmp/satori_mnt_xwabe7ar/etc/pam.d/passwd
/tmp/satori_mnt_xwabe7ar/etc/passwd
```
or any binary, as they are a part of the real filesystem!

#### Also `stat` for mounted files returns real results:

```bash
$ stat /tmp/satori_mnt_xwabe7ar/etc/pam.d/passwd
  File: /tmp/satori_mnt_xwabe7ar/etc/pam.d/passwd
  Size: 188       	Blocks: 8          IO Block: 4096   regular file
Device: 34h/52d	Inode: 739         Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Context: system_u:object_r:fusefs_t:s0
Access: 2018-05-03 22:15:55.563727140 +0300
Modify: 2017-08-04 10:44:55.000000000 +0300
Change: 2018-02-17 20:50:16.641976833 +0200
 Birth: -
```

#### Yet, *File Contents are not available* - unless they are also gathered by a *satori-extension*:

```bash
$ cat /tmp/satori_mnt_xwabe7ar/etc/pam.d/passwd
cat: /tmp/satori_mnt_xwabe7ar/etc/pam.d/passwd: Function not implemented
```


#### Basic diagnosis scripts:

```bash
SAT_MOUNT="$1"
$ stat -c '%a' $SAT_MOUNT/etc/pam.d/passwd
777
$ if [ "$(stat -c '%a' $SAT_MOUNT/etc/pam.d/passwd)" != "644" ]; then
  echo "Edited /etc/passwd file";
fi
Edited /etc/passwd file
```
