#! /usr/bin/bash

shopt -s globstar

for i in "$1"/**; do
    echo "$i"
    [[ -d "$i" ]] && continue
    dir=$(dirname "$i")
    mkdir -p "/home/lahwaacz/stuff/$dir"
    ddrescue "$i" "/home/lahwaacz/stuff/$i"
done
