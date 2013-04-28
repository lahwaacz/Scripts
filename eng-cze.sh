#!/bin/bash

echo "Welcome to the English-Czech FreeDict Dictionary!"

while echo -en "\x1b[1;32m" && read -e input
do
    echo -en "\x1b[0m"
    curl -s dict://dict.org/d:$input:eng-cze
    echo -en "\x1b[1;34m"
    echo "------------------------------------------------------"
done
