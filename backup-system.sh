#!/bin/bash

# exit on first error
set -e

# check if destination dir exists
[[ ! -d $1 ]] && echo -e "Set valid destination folder as \$1.\nExiting..." && exit 1

homedir=$1/Záloha-home
rootdir=$1/Záloha-root

START=$(date +%s)


#echo "Syncing ~/Virtual.Machines to $homedir/Virtual.Machines"
#rsync -aPhAHX --delete-before ~/Virtual.Machines "$homedir/"
echo "Syncing ~/ to $homedir"
rsync -aPhAHX --stats --delete-before --exclude={"/Filmy-NEW","/Filmy-OLD","/.ccache/","/.thumbnails/","/Virtual.Machines/"} ~/ $homedir
echo "Syncing / to $rootdir (root permissions required)"
sudo rsync -aPhAHX --stats --delete-after --exclude={/dev/*,/proc/*,/sys/*,/tmp/*,/run/*,/mnt/*,/media/*,/lost+found,/home,/swapfile} /* $rootdir

FINISH=$(date +%s)
echo "total time: $(( ($FINISH-$START) / 60 )) minutes, $(( ($FINISH-$START) % 60 )) seconds"
