#! /bin/bash

backup_dir="/home/lahwaacz/stuff/Archiv/backups-configs"
base_name="configs-$(date +%Y-%m-%d@%H:%M:%S)"

[ ! -d "$backup_dir" ] && mkdir -p "$backup_dir"

paths=(
    ~/.*rc
    ~/.*.conf
    "$HOME/.config"
    "$HOME/.gnupg"
    "$HOME/.sage"
    "$HOME/.ssh"
)

for path in "${paths[@]}"; do
    tar -rpf "${backup_dir}/${base_name}.tar" -C / ${path#/}
done
gzip "${backup_dir}/${base_name}.tar"
