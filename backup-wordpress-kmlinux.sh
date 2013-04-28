#! /bin/bash

# rsync not useful - does not back up mysql database
#rsync -aPhAHX $* klinkjak@kmlinux.fjfi.cvut.cz:~/public_html /home/lahwaacz/stuff/Archiv/backup-wordpress-kmlinux

# exit on error
set -e

# default error message on error
trap "echo 'Errors occured during backup.' >&2; exit 1" ERR

if [[ "$1" == "-q" ]]; then
    QUIET="&> /dev/null"
else
    QUIET=""
fi

ssh $* klinkjak@kmlinux.fjfi.cvut.cz 'bash -s' < ~/bin/backup-wordpress-kmlinux-server-side.sh $QUIET
scp $* klinkjak@kmlinux.fjfi.cvut.cz:~/backups/*.tar.gz /home/lahwaacz/stuff/Archiv/backup-wordpress-kmlinux/
ssh $* klinkjak@kmlinux.fjfi.cvut.cz 'rm -f ~/backups/*.tar.gz' $QUIET

echo "Kmlinux backup successful."

# untrap ERR and exit 0
trap - ERR
exit 0
