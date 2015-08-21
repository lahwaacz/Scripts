#!/bin/bash

# exit on first error
set -e

# check if destination dir exists
[[ ! -d $1 ]] && echo -e "Set valid destination folder as \$1.\nExiting..." && exit 1

snapdir="$1/backup-lahwaacz"
homedir="$snapdir/home"
rootdir="$1/backup-root"

START=$(date +%s)

echo "Syncing / to $rootdir (root permissions required)"
sudo rsyncbtrfs backup / "$rootdir" -aPhAHX --info=progress2 --stats --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/lost+found","/home","/swapfile"}

echo "Syncing ~/ to $homedir"
# --one-file-system skips subvolumes
sudo rsyncbtrfs backup ~/ $homedir -aPhAHX --one-file-system --info=progress2 --stats --exclude={"/Filmy-NEW","/Filmy-OLD","/.cache/ccache/","/.thumbnails/","/_backup_snapshots/","/rsnapshots/","/aur/"}

#echo "Creating snapshots of some subvolumes ('bsnap.sh snapshot')"
#bsnap.sh snapshot

echo "Transferring snapshots ('bsnap.sh transfer $snapdir')"
bsnap.sh transfer "$snapdir"

FINISH=$(date +%s)
echo "total time: $(( ($FINISH-$START) / 60 )) minutes, $(( ($FINISH-$START) % 60 )) seconds"
