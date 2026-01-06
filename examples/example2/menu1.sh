#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        # When this item is included in a menu, this is it thext that will show.
        echo "menu :: :: :: <ok> :: open menu 1"
        ;;
    "execute")
        # This is the action executed when the item is selected.
        mypath="$(dirname "${0}")"
        simple-menu menu --title "Menu1" \
            --type item_external --value "${mypath}/menu2.sh" \
            --type item --value "notification :: :: :: :: Item 1 ..." \
            --type item --value "notification :: :: :: :: Item 2 ..." \
            --type item --value "notification :: :: :: :: Item 3 ..."
        ;;
    *)
        # On manual execution show the menu.
        "${0}" execute "${@}"
        ;;
esac
