#! /bin/bash

# main variables
repo_path="$HOME/GitHub-repos/archlinux-dotfiles"
files_system="files-system"
files_home="files-home"
files_scripts="files-scripts"
files_build="files-build"

# init colors
initializeANSI()
{
  esc=""

  blackf="${esc}[30m";   redf="${esc}[31m";    greenf="${esc}[32m"
  yellowf="${esc}[33m"   bluef="${esc}[34m";   purplef="${esc}[35m"
  cyanf="${esc}[36m";    whitef="${esc}[37m"
  
  blackb="${esc}[40m";   redb="${esc}[41m";    greenb="${esc}[42m"
  yellowb="${esc}[43m"   blueb="${esc}[44m";   purpleb="${esc}[45m"
  cyanb="${esc}[46m";    whiteb="${esc}[47m"

  boldon="${esc}[1m";    boldoff="${esc}[22m"
  italicson="${esc}[3m"; italicsoff="${esc}[23m"
  ulon="${esc}[4m";      uloff="${esc}[24m"
  invon="${esc}[7m";     invoff="${esc}[27m"

  reset="${esc}[0m"
}
initializeANSI

# check if files contain some password
function check_pass() { 
    for file in $(cat "$1"); do
        if [[ ! -e "$file" ]]; then
            continue
        fi

        if [[ "$file" =~ "pass" ]]; then
            warn_pass "$file"
            continue
        fi

        if [[ $(cat "$file" | egrep -i "passwd|password") != "" ]]; then
            warn_pass "$file"
            continue
        fi
    done
}

# display warning about file containing password
function warn_pass() {
    echo -e "${boldon}${redf}  WARNING:${whitef} file might contain password:${boldoff}${yellowf}  ${1}${reset}"
}

# change directory to the repo
cd "$repo_path"

# create list of files to consider to transfer
find ./{usr,etc} -type f -print > "$files_system"
find ./home -type f -print > "$files_home"
find ~/Scripts -type f -print > "$files_scripts"
find ~/aur/build-dirs -mindepth 2 -maxdepth 2 -type f -name "PKGBUILD" -print0 | xargs -0 grep -l "groups=('modified')" > "$files_build"

# remap ./ to /
sed -i "s|^./|/|g" "$files_system"
sed -i "s|^./|/|g" "$files_scripts"
sed -i "s|^./|/|g" "$files_build"
sed -i "s|^./home|/home/$USER|g" "$files_home"

# remove specific files from the list
sed -i "/\/etc\/grub.d\/01_password-security/d" "$files_system"
sed -i "/\/home\/lahwaacz\/Scripts\/backup-wordpress-kmlinux-server-side.sh/d" "$files_scripts"

for f in "$files_system" "$files_home" "$files_scripts" "$files_build"; do
    check_pass "$f"
done

# change home path to relative
sed -i "s|^/home/lahwaacz/||g" "$files_home"
sed -i "s|^/home/lahwaacz/||g" "$files_scripts"
sed -i "s|^/home/lahwaacz/aur/build-dirs/||g" "$files_build"

# update files
echo -e "${boldon}${whitef}Transfering system files...${reset}"
rsync -ahv --files-from="$files_system" / .
echo -e "${boldon}${whitef}Transfering home files...${reset}"
rsync -ahv --files-from="$files_home" "$HOME" ./home
echo -e "${boldon}${whitef}Transfering Scripts...${reset}"
rsync -ahv --files-from="$files_scripts" "$HOME" .
echo -e "${boldon}${whitef}Transfering PKGBUILDS...${reset}"
rsync -ahv --files-from="$files_build" ~/aur/build-dirs ./Build

# cleanup
rm -f "$files_system" "$files_home" "$files_scripts" "$files_build"
