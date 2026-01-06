#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        # When this item is included in a menu, this is it thext that will show.
        echo "menu :: :: :: <ok> :: open menu 4"
        ;;
    "execute")
        # This is the action executed when the item is selected.
        simple-menu menu --title "Menu1/Menu2/Menu4" \
            --type item --value "notification :: :: :: :: Item 1 ..." \
            --type item --value "notification :: :: :: :: Item 2 ..." \
            --type item --value "notification :: :: :: :: Item 3 ..." \
            --type item --value "notification :: :: :: :: Item 4 ..." \
            --type item --value "notification :: :: :: :: Item 5 ..."
        ;;
    *)
        # On manual execution show the menu.
        "${0}" execute "${@}"
        ;;
esac
