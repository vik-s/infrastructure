This role automates the installation of mergerfs and snapraid. The vars associated with the role define what versions of these software will be installed. So, if newer versions are released, you can update the vars/main.yaml file to reflect the newest installable packages. Mount points are automatically created, if they are not already present.

Formatting of new drives should be done manually, as it is destructive if something goes wrong. So when adding a new drive, find the drive identifier ``/dev/sdX`` where X = a, b, c, ..., by doing ``sudo fdisk -l``. Then, create a single partition on the whole drive using ``gpart``.

## Creating a disk partition

Run the following as root:

``sudo gdisk /dev/sdc``

The following is copied from perfectmediaserver.com.

Use the following sequence to create one large partition spanning the entire drive. Note that the keys you need to press are at the start of each heading and the answers to the subsequent questions at the ends of the next few lines.

- o : creates a new EMPTY GPT partition table (GPT is good for large drives over 3TB)
     
Proceed? (Y/N) - Y

- n : creates a new partition

Partition number (1-128, default 1): 1

First sector (34-15628053134, default = 2048) or {+-}size{KMGTP}: leave blank

Last sector (2048-15628053134, default = 15628053134) or {+-}size{KMGTP}: leave blank

Hex code or GUID (L to show codes, Enter = 8300): 8300

- p : (optional) validate 1 large partition to be created

- w : writes the changes made thus far

Until this point, gdisk has been non-destructive

Confirm that making these changes is OK and the changes queued so far will be executed

## Filesystem creation

Next, create ``ext4`` filesystems on the new drives.

```
mkfs.ext4 /dev/sdX1
```

The following is then taken care of by the ansible role described in ``disks.yaml``

1. Mount disks and mergerfs mounts in /etc/fstab


