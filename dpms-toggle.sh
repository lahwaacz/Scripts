#!/bin/bash
# screenblank - Toggle screen blanking/powersaving on/off

XBLANKTEXT=$(xset -q | grep timeout | awk '{printf $2}')
DPMSTEST=$(xset -q | grep "  DPMS is Enabled")

if [[ "$XBLANKTEXT" -gt 0 ]] || [[ -n "$DPMSTEST" ]]; then
    xset s off; xset -dpms
    echo " Disabled screen blanking and powersaving"
else
    xset s on; xset +dpms
    echo " Enabled screen blanking and powersaving"
fi
