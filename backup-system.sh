#!/bin/bash

# exit on first error
set -e

backupdir="/media/WD-black/backups"

# check if destination dir exists
if [[ ! -d "$backupdir" ]]; then
    echo "Backup directory $backupdir does not exist. Is the drive mounted?"
    exit 1
fi

#homedir="$backupdir/home_rsync_copy"
#rootdir="$backupdir/root_rsync_copy"

#echo "Syncing / to $rootdir (root permissions required)"
#sudo rsync / "$rootdir" -aPhAHX --info=progress2,name0,stats2 --delete --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/lost+found","/home","/swapfile","/.snapshots"}

#echo "Syncing ~/ to $homedir"
#rsync ~/ $homedir -aPhAHX --one-file-system --info=progress2,name0,stats2 --delete


# TODO:
# - make snapshot with snapper just before btrfs-sync
# - run `sync` before btrfs-sync to make sure that the snapshot is fully written to the disk
# - copy the snapper metadata files (info.xml)
# - make snapshots of the remaining subvolumes: @postgres @nspawn_containers @var_log

echo "Syncing /.snapshots to $backupdir/root (root permissions required)"
sudo btrfs-sync --verbose --delete /.snapshots "$backupdir/root"

echo "Syncing /home/.snapshots to $backupdir/home (root permissions required)"
sudo btrfs-sync --verbose --delete /home/.snapshots "$backupdir/home"
