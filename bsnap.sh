#! /usr/bin/bash

# exit on first error
set -e

backupdir="$HOME/_backup_snapshots"

usage() {
    echo $@ >&2
    echo "Usage: $0 {snapshot|transfer} ...

    snapshot        Create snapshots for every subvolume configured in '\$backupdir/*'.
                    The subvolume is specified by a symlink '\$backupdir/*/cur'
                    pointing to a Btrfs subvolume.

    transfer <dst>  Transfer all snapshots from '\$backupdir/*/' to '<dst>/', which
                    should be other Btrfs partition. The tree structure is kept
                    intact.

    \$backupdir is set to '$backupdir'
" >&2
}

transfer() {
    src="$1"    # e.g. ~/_backup_snapshots/Bbox/
    dst="$2"    # e.g. /media/WD1T/backup-lahwaacz/Bbox/

    [[ ! -d "$dst" ]] && mkdir "$dst"

    # get list of snapshots to transfer
    src_snapshots=($(find "$src" -mindepth 1 -maxdepth 1 -type d | sort))

    _len=${#src_snapshots[@]}
    for ((i=0; i<$_len; i++)); do
        if [[ -e "$dst/$(basename ${src_snapshots[$i]})" ]]; then
            # nothing to transfer
            echo "Snapshot '$dst/$(basename ${src_snapshots[$i]})' already exists"
            continue
        fi

        # There is currently an issue that the snapshots to be used with "btrfs send"
        # must be physically on the disk, or you may receive a "stale NFS file handle"
        # error. This is accomplished by "sync" after the snapshot
        #
        # ref: http://marc.merlins.org/perso/btrfs/post_2014-03-22_Btrfs-Tips_-Doing-Fast-Incremental-Backups-With-Btrfs-Send-and-Receive.html
        sync

        dst_snapshots=($(find "$dst" -mindepth 1 -maxdepth 1 -type d | sort))

        if [[ $i -eq 0 ]]; then
            # no parent, make initial transfer
            sudo sh -c "btrfs send ${src_snapshots[$i]} | btrfs receive $dst"
        else
            sudo sh -c "btrfs send -p ${src_snapshots[(($i-1))]} ${src_snapshots[$i]} | btrfs receive $dst"
        fi

    done


    
}

case $1 in
    snapshot)
        for dir in "$backupdir"/*; do
            if [[ -L "$dir/cur" ]]; then
                btrfs subvolume snapshot -r $(realpath "$dir/cur") "$dir/$(date +%F-%T)"
            else
                echo "$dir/cur does not exist or is not a symlink"
            fi
        done
        ;;
    transfer)
        [ -n "$2" -a -d "$2" ] || usage "Invalid destination path"

        for dir in "$backupdir"/*; do
            transfer "$dir" "$2"/$(basename "$dir")
        done
        ;;
    *)
        usage "Incorrect invocation"
esac
