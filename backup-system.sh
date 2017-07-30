#!/bin/bash

# exit on first error
set -e

backupdir="/media/black/backups"
music="/media/black/Music"

# check if destination dir exists
if [[ ! -d "$backupdir" ]]; then
    echo "Backup directory $backupdir does not exist. Is the drive mounted?"
    exit 1
fi

homedir="$backupdir/home_lahwaacz"
rootdir="$backupdir/root"

START=$(date +%s)

echo "Syncing / to $rootdir (root permissions required)"
sudo rsync / "$rootdir" -aPhAHX --info=progress2,name0,stats2 --delete --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/lost+found","/home","/swapfile"}

echo "Syncing ~/Music/ to $music"
rsync ~/Music/ $music -aPhAHX --info=progress2,name0,stats2

echo "Syncing ~/ to $homedir"
rsync ~/ $homedir -aPhAHX --one-file-system --info=progress2,name0,stats2 --delete --exclude={"/build/builddir/","/build/pkgs/","/build/src/","/mnt/","/stuff/","/Music/"}

FINISH=$(date +%s)
echo "total time: $(( ($FINISH-$START) / 60 )) minutes, $(( ($FINISH-$START) % 60 )) seconds"
