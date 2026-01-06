#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        # This item accepts a parameter.
        echo "action :: SomeCategory :: :: <folder> :: notify about parameter1 '${2}'"
        ;;
    "execute")
        # This is executes when the item is selected.
        notify-send "parameter1 was ${2}"
        ;;
esac
