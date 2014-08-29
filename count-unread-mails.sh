#! /bin/bash

# count new emails of all accounts (for display in statusbar)
#find ~/Maildir/*/*/new/ -type f | wc -l > /dev/shm/new-mails-count
#find ~/Maildir/*/INBOX/new/ -type f | wc -l > /dev/shm/new-mails-count
find ~/Maildir/*/{INBOX,arch,arch-general,arch-wiki}/new/ -type f | wc -l > /dev/shm/new-mails-count
