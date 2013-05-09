#!/bin/bash

outfile=$1
ext=tif

echo "Converting images to pdf..."
declare -a pages
for file in ./*.$ext; do
    echo "  $file"
    pdf=$(basename "$file" .$ext).pdf
#    convert "$file" "$pdf"
    tiff2pdf -z -F -x 300 -y 300 -o "$pdf"  "$file"
    pages+=("$pdf")
done
echo "Merging into one pdf..."
stapler sel "${pages[@]}" "$outfile"
