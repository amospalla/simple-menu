#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        # When this item is included in a menu, this is it thext that will be shown.
        echo "action :: MyCategory :: :: <folder> :: I do notify"
        ;;
    "execute")
        # This is executes when the item is selected.
        notify-send "here it is the notification"
        ;;
esac
