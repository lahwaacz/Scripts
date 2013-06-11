#!/bin/bash

# exit on error
set -e

any2img() {
    convert -density 150 "$1" -quality 100 "$2" &>/dev/null
}

pdf2img() {
    echo "Splitting single pdf file by pages (tiff)"
    stapler burst "$1"
    base=${1%.*}
    for i in "${base}_"*.pdf
    do
        out=pg${i#"$base"}  # will result in 'pg_123.pdf'
        out=${out%.*}.tiff  # replace extension
        echo "$out"
#        any2img "$i" "$out"
        convert -density 300 "$i" -compress lzw "$out"
        rm -f "$i"
    done
}

djvu2img() {
    echo "Splitting single djvu file by pages (tiff)"
    pages=`djvused -e "n" "$1"`
    for (( i=1; i<=$pages; i++ ))
    do
        num=$(printf "%03d" "$i")
        out="pg_$num.tiff"
        echo "  $out"
        ddjvu -page=$i -format=tiff "$1" "$out"
    done
}

path=$(realpath "$1")
filename=$(basename "$path")
extension=${filename##*.}
basename=${filename%.*} # filename without extension

# create directory for extracted images
mkdir -p "$basename"
cp "$path" "$basename"
cd "$basename"

if [[ "$extension" == "pdf" ]]; then
    pdf2img "$filename"
    rm -f "$filename"
elif [[ "$extension" == "djvu" ]]; then
    djvu2img "$filename"
    rm -f "$filename"
else
    echo "Supported file types: pdf, djvu"
    exit 1
fi
