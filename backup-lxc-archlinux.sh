#! /bin/bash

backup_dir="/home/lahwaacz/stuff/Archiv/backups-lxc-archlinux"
base_name="lxc-archlinux-$(date +%Y-%m-%d)"

[ ! -d "$backup_dir" ] && mkdir -p "$backup_dir"

sudo tar -cpf "${backup_dir}/${base_name}.tar" -C /srv/lxc-archlinux .
sudo chown lahwaacz:lahwaacz "${backup_dir}/${base_name}.tar"
pxz -z9 -T 2 "${backup_dir}/${base_name}.tar"
