#!/bin/bash

# create a new session, named "$1", and detach from it
tmux new-session -d -s "$1"

# move original window
tmux move-window -s "$1":1 -t "$1":10
 
# 1 - todo list
#tmux new-window -t "$1":1 -n todo   'zsh -is eval "vim ~/Dropbox/Notes/todo"'
tmux new-window -t "$1":1
# 2 - git
#tmux new-window -t "$1":2 -n git    'zsh -is eval "cd ~/GitHub-repos/archlinux-dotfiles"'
tmux new-window -t "$1":2
# 3 - empty shell
tmux new-window -t "$1":3

# remove original window
tmux kill-window -t "$1":10
 
# select window and attach
tmux select-window -t "$1":1
tmux attach -t "$1"
