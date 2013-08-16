#!/bin/bash

# Original author: xyne
# url: http://xyne.archlinux.ca/projects/quickserve/

set -e

# help message function
function display_help()
{
    cat <<HELP
usage: $0 [CURL OPTIONS] <URI> [FILES]

    The order of the arguments is not important. The arguments are simply filtered
    and passed to curl, wrapping detected files so that curl can upload them.

    See "curl --help" for information about curl options.
HELP
    exit
}

if [ -z "$1" ]; then
    display_help
fi


# argument filter
args=()
_i=1
for arg in "$@"; do
    case "$arg" in
        -h)
            display_help
        ;;
        --help)
            display_help
        ;;
    esac

    if [[ -f $arg ]]
    then
        args+=("-F")
        args+=("file=@$arg")
    else
        args+=("$arg")
    fi
done

curl "${args[@]}"
