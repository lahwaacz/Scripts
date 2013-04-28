#!/bin/bash
#
# thinkwatt:
# record power consumption, calculate average and create a gnuplot graph
#
# TO-DO:
# * add more options (e.g. for specifying a different gnuplot title or png output)
# * allow time input in minutes and hours

# utilities {{{
message() {
  cat << EOF
usage:	thinkwatt -r (seconds) (-q) (-o file)
	thinkwatt [ -p | -a ] (-q) file

options:	
	-r, --record	record power consumption and optionally create a graph from the gathered data
	-p, --plot	create a plot image from a specified data file
	-a, --average	calculate the average power consumption from a specified data file
	-q, --quiet	makes thinkwatt less chatty
	-o, --output	the output file. can be prepended by a path.
	-h, --help	show this help text
	
examples:
	thinkwatt -r (will record to a temp file until cancelled)
	thinkwatt -r 300 -o /foo/bar/consumption.dat (will record for 5 minutes to the specified file)
	thinkwatt -p /foo/bar/consumption.dat (will create a graph from the specified file)
EOF
  exit 1
}

errorout() { echo "error: $*" >&2; exit 1; }

check_ac() {
  local acfile=/sys/class/power_supply/AC0/online
  [[ $(cat "$acfile") = 0 ]] || errorout 'please unplug the ac adapater first'
}
check_datafile() {
  [[ -f "$@" ]] || errorout "$@ does not exist"
  local valid_file=$(file "$@" | grep -s "^$@: ASCII text$")
  [[ "$valid_file" ]] || errorout "$@ is not a valid data file"
  local valid_data=$(cat "$@" | grep -s '^[0-9]*[,.]\?.*[0-9]$')
  [[ "$valid_data" ]] || errorout "$@ does not contain valid data"
}
countdown() {
  if [[ "$seconds" =~ ^[0-9]+$ ]];then
    # count down
    secs="$seconds"
    while [ "$secs" -gt 0 ];do
      [[ "$die" == yes ]] && return 0
      sleep 1 &
      cat "$powerfile" >> "$tmpfile1"
      printf "\rrecording (%02d/$seconds)" $((secs))
      secs=$(( $secs - 1 ))
      wait
    done
  else
    # count up
    secs=1
    while true;do
      [[ "$die" == yes ]] && return 0
      sleep 1 &
      cat "$powerfile" >> "$tmpfile1"
      printf "\rrecording ($secs)"
      secs=$(( $secs + 1 ))
      wait
    done
  fi
  echo 
}
# if we abort the recording process with ctrl+c this will give the option to plot the already recorded data
trap ctrl_c INT
function ctrl_c() {
  echo
  read -p "plot already recorded data before exiting? y/n "
  [[ "$REPLY" = "y" ]] && die=yes || exit 0
}
# }}}

# default output dir and png file {{{
# use $TDIR to have thinkwatt save files in a different directory.
# thinkwatt will save two files:
# 1) a .plt file (containing plot instructions) in case you want to reuse/modify it
# 2) a .png file (the plot graphic)
TDIR="/tmp/thinkwatt"
PLOTFILE="$TDIR"/$$.plt
# }}}

# record {{{
record() {

  local seconds="$1"
  
  #[[ "$seconds" =~ ^[0-9]+$ ]] || errorout 'please specify the time in seconds"
  [[ -d "$output" ]] && errorout "$output is a directory"
  [[ -d "$TDIR" ]] || mkdir -p "$TDIR" 2>/dev/null || errorout "could not create $TDIR"

  if [[ -f "$output" ]];then
    read -p "overwrite $output? y/n "
    [[ "$REPLY" = "y" ]] || exit 0
  elif [[ -e "$output" ]];then
    errorout "$output exists and can/should not be written to"
  fi
  
  local tmpfile1=/tmp/$$.dat
  local tmpfile="$TDIR"/$$.dat

  if [[ "$output" ]];then
    local dir=$(dirname "$output")
    local file=$(basename "$output")
    [[ -d "$dir" ]] || mkdir -p "$dir"
    [[ -w "$dir" ]] || errorout "you don't have permissions to write to $dir"
    
    outputfile="$output"
    [[ "$dir" ]] && TDIR="$dir"
    PNGFILE="$TDIR"/$(basename "$file" .dat).png
    #PLOTFILE="$TDIR"/$(basename "$output" .dat).plt
  else
    [[ -w "$(pwd)" ]] || errorout "you don't have permissions to write to $(pwd)"
    local file=$(basename "$tmpfile")
    outputfile="$tmpfile"
    local istemp=true
  fi
  
  SMAPI=$(lsmod | grep -s tp_smapi)
  if [[ "$SMAPI" ]];then
    local powerfile=/sys/devices/platform/smapi/BAT0/power_now
  else
    echo "for more accurate results use tp_smapi"
    local powerfile=/sys/class/power_supply/BAT0/power_now
  fi
  
  touch "$tmpfile1" || errorout "could not create $tmpfile1"
  trap "rm $tmpfile1" EXIT
  
  # do the actual recording included in countdown()
  countdown
  
  # file formatting
  if [[ "$SMAPI" ]];then
    # we strip the leading "-" from the data file
    sed -i 's/-//g' "$tmpfile1"
  else
    # strip the trailing last 3 characters
     sed -i 's/.\{3\}$//' "$tmpfile1"
  fi
  # and divide by 1000 to convert from mW to W
  cat "$tmpfile1" | awk '{print $1/1000}' > "$tmpfile"
    
  [[ "$output" ]] && mv "$tmpfile" "$output"
  
  [[ "$quiet" ]] || echo average was $(average "$outputfile") W
  
  plot "$outputfile"

}
# }}}

# calculate average {{{
average() {

  [[ "$@" ]] || errorout 'please specify a file to read from.'
  [[ -f "$@" ]] || errorout 'file not found.'
  check_datafile "$@"
  
  awk 'BEGIN{s=0;}{s+=($1);}END{print s/NR;}' "$@"
  
}
# }}}

# make the plot file {{{
makeplotfile() {

  cat << EOF
# gnuplot file
# created by thinkwatt
# $DATE

set title "$TITLE"
set xlabel "$XLABEL"
set ylabel "$YLABEL"
set terminal $TERMINAL
set output "$PNGFILE"
EOF
  [[ "$YRANGE" ]] && echo "set yrange $YRANGE"
  [[ "$XRANGE" ]] && echo "set yrange $YRANGE"
  [[ "$GRID" == yes ]] && echo "set grid"
  [[ "$YTICS" ]] && echo "set ytics $YTICS"
  [[ "$MYTICS" ]] && echo "set mytics $MYTICS"
  [[ "$XTICS" ]] && echo "set xtics $XTICS"
  [[ "$MXTICS" ]] && echo "set mxtics $MXTICS"
  [[ "$GRIDSET" ]] && echo "set grid $GRIDSET"

  echo 
  if [[ "$TITLE1" ]];then
    echo "plot \"$datafile\" using (\$1) with lines title \"$TITLE1\" lt 2, \\"
  else
    echo "plot \"$datafile\" using (\$1) with lines lt 2, \\"
  fi

  if [[ "$TITLE2" ]];then
    if [[ "$avg" ]];then
      echo "\"$datafile\" using (\$1) smooth bezier title \"$TITLE2\" lt 1, \\"
    else
      echo "\"$datafile\" using (\$1) smooth bezier title \"$TITLE2\" lt 1"
    fi
  else
    if [[ "$avg" ]];then
      echo "\"$datafile\" using (\$1) smooth bezier lt 1, \\"
    else
      echo "\"$datafile\" using (\$1) smooth bezier lt 1"
    fi
  fi

  [[ "$avg" ]] && echo "$avg title \"$file (average, $avg W)\""

}
# }}}

# do the plotting
plot() {

  # check if we have gnuplot and $TDIR is present
  have_gnuplot=$(find $(sed 's/:/ /g' <<<$PATH) 2>/dev/null | grep -is gnuplot)
  [[ "$have_gnuplot"  ]] || errorout 'please install gnuplot first'
  [[ -d "$TDIR" ]] || mkdir -p "$TDIR" || errorout "could not create $TDIR"

  # is input file a valid data file?
  local datafile="$@"
  check_datafile "$datafile"
  [[ "$datafile" ]] || errorout 'please specify a file to read from.'
  [[ -f "$datafile" ]] || errorout 'filplotfilee not found.'
   
  # define some of the variables for the plot file
  DATE=$(date +%Y-%m-%d,\ %T)
  TITLE="power consumption of my laptop, created by thinkwatt on $DATE"
  XLABEL="sec (seconds)"
  YLABEL="W (Watt)"
  TERMINAL="png"
  GRID=yes
  #TITLE1="your custom title for line1"
  #TITLE2="your custom title for line2"
  #TITLE3="your custom title for line3"
  # some more options for gnuplot, enable and modify them here if you like
  MYTICS=2
  MXTICS=2
  #YTICS=1
  #XTICS=(better leave this alone)
  GRIDSET="mytics"
  #YRANGE="[4000:16000]"
  #XRANGE="[0:2000]"
  # moar
  local avg=$(average "$datafile" | cut -c1-4)
  local dir=$(dirname "$datafile")
  local file=$(basename "$datafile")
  [[ -z "$TITLE1" ]] && local TITLE1="$file (actual)"
  [[ -z "$TITLE2" ]] && local TITLE2="$file (trend)"
  [[ "$PNGFILE" ]] || PNGFILE=$(basename "$datafile" .dat).png
  
  # now we can plot   
  makeplotfile > "$PLOTFILE" || errorout "could not write the plotfile (permission issue?)"
  gnuplot "$PLOTFILE" || errorout "could now write graph (permission issue?)"

  [[ "$quiet" ]] || echo "graph saved as $PNGFILE"

}

# parse options {{{
parse_options() {

  [[ -z "$1" ]] && message

  while [[ -n "$1" ]];do
    case "$1" in
      -h|--help)    message		;;
      -q|--quiet)   quiet=true		;;
      -o|--output)  output="$2"		;;
      -r|--record)  mode='record'	;;
      -p|--plot)    mode='plot'		;;
      -a|--average) mode='average'	;;
      *)            args+=( "$1" )	;;
    esac
    shift
  done
}
# }}}

# main {{{
main() {

  case "$mode" in
    record)  record "${args[@]}"	;;
    average) average "${args[@]}"	;;
    plot)    plot "${args[@]}"		;;
    *)       errorout 'invalid mode. use -r, -p or -a.' ;;
  esac
  
}
# }}}

parse_options "$@"
check_ac
main
