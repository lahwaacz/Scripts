#! /bin/bash

for itm in *
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
