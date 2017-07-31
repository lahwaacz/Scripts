#! /bin/bash

# recursively remove dead symlinks

shopt -s globstar

# non-recursive version: 'for itm in *'
for itm in **/*
do
    if [ -h "$itm" ]
    then
        target=$(readlink -fn "$itm")
        if [ ! -e "$target" ]
        then
            echo "$itm"
            rm "$itm"
        fi
    fi
done
