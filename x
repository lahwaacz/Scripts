#! /bin/bash

# Some references:
# https://wiki.archlinux.org/index.php/Bash#Functions
# https://github.com/robbyrussell/oh-my-zsh/blob/master/plugins/extract/extract.plugin.zsh

function extract() {
    local remove_archive
    local success
    local fname
    local basename
    local extension

    success=0
    fname=$(realpath "$1")
    extension=${fname##*.}

    # remove extension from basename
    basename=$(basename "${fname%.*}")

    # hack to recognize .tar.gz etc as extension
    if [[ "${basename##*.}" == "tar" ]]; then
        extension="${basename##*.}.$extension"
        basename=$(basename "${basename%.*}")
    fi

    # split \.part[0-9]* from $basename
    basename="${basename%\.part[0-9]*}"

    case "$extension" in
        tar.gz|tgz|tar.bz2|tbz|tbz2|tar.xz|txz|tar.lzma|tlz|tar|tar.zst)
            mkdir "$basename"
            tar xvf "$fname" -C "$basename"
            ;;
        gz|Z)
            gzip -dkv "$fname"
            ;;
        bz2)
            bzip2 -dkv "$fname"
            ;;
        xz|lzma)
            xz -dkv "$fname"
            ;;
        zst)
            zstd -dkv "$fname"
            ;;
        zip)
            unzip "$fname" -d "$basename"
            ;;
        rar)
            mkdir "$basename"
            pushd "$basename"
                unrar e "$fname"
            popd
            ;;
        7z)
            7za x "$fname" -o"$basename"
            ;;
        *)
            echo "extract: '$fname' cannot be extracted" 1>&2
            success=1
            ;;
    esac

    [[ $success == 0 ]] && success=$?

    # if destination directory contains only one file/dir, move it to cwd
    if [[ $success == 0 ]]; then
        count=$(find "$basename" -maxdepth 1 -mindepth 1 | wc -l)

        if [[ $count == 1 ]]; then
            name=$(basename $(find "$basename" -maxdepth 1 -mindepth 1))

            # can't move ./foo/foo into ./foo
            if [[ "$basename" == "$name" ]]; then
                tmp="$name.tmp"
            else
                tmp="$name"
            fi

            mv "$basename/$name" "$tmp"
            rmdir "$basename"
            mv "$tmp" "$name"
        fi
    fi
}

if [[ $# == 0 ]]; then
    echo "Usage: $0 file [file ...]"
    exit 1
fi

while [[ $# > 0 ]]; do
    if [[ -f "$1" ]]; then
        extract "$1"
    else
        echo "extract: '$1' is not a valid file"
    fi
    shift
done
