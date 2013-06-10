#! /bin/bash

# count new emails of all accounts (for display in statusbar)
find ~/Maildir/*/*/new/ -type f | wc -l > /dev/shm/new-mails-count
