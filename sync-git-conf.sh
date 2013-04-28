#! /bin/bash

# main variables
repo_path="$HOME/git-lahwaacz/archlinux-dotfiles"
files_system="files-system"
files_home="files-home"

# change directory to the repo
cd "$repo_path"

# create list of files to consider to transfer
find ./{usr,etc} -type f -print > "$files_system"
find ./home -type f -print > "$files_home"

# remove specific files from the list
sed -i "/\/etc\/grub.d\/01_password-security/d" "$files_system"
sed -i "/.*\.gpg/d" "$files_home" "$files_system"

# change home path to relative
sed -i "s|^./home/||" "$files_home"

# update files
echo -e "\033[01;37mTransfering system files...\033[00m"
rsync -ahv --stats --files-from="$files_system" / .
echo -e "\033[01;37mTransfering home files...\033[00m"
rsync -ahv --stats --files-from="$files_home" "$HOME" ./home

# cleanup
rm -f "$files_system" "$files_home"
