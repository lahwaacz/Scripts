#!/bin/bash

any2img() {
    convert -density 150 "$1" -quality 100 "$2" &>/dev/null
}

pdf2jpg() {
    echo "Splitting single pdf file by pages and converting to png"
    stapler burst "$1"
    rm -f "$1"
    for i in *.pdf
    do
        out=$(basename "$i" .pdf).png
        echo "$out"
        any2img "$i" "$out"
        rm -f "$i"
    done
}

djvu2jpg() {
    echo "Splitting single djvu file by pages and converting to jpg"
    pages=`djvused -e "n" "$1"`
    for (( i=1; i<=$pages; i++ ))
    do
        num=$(printf "%03d" "$i")
        pnm="pg_$num.pnm"
        out=$(basename pnm .pnm).jpg
        echo "  $out"
        ddjvu -page=$i -format=pnm "$1" "$pnm"
        any2img "$pnm" "$out"
        rm -f "$pnm"
    done
}

if [[ $1 == *.pdf ]]; then
    dir=$(basename "$1" .pdf)
    mkdir "$dir"
    cp "$1" "$dir"
    cd "$dir"
    pdf2jpg "$1"
elif [[ $1 == *.djvu ]]; then
    djvu2jpg "$1"
else
    echo "Supported file types: pdf, djvu"
    exit 1
fi
