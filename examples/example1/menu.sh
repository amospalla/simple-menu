#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        # When this item is included in a menu, this is it thext that will show.
        echo "menu :: :: :: <ok> :: show a menu"
        ;;
    "execute")
        # This is the action executed when the item is selected.
        mypath="$(dirname "${0}")"
        commands=(
            "simple-menu" "menu" "--title" "Menu1"
            --type item --value "notification :: Type :: Subtype :: <warning> :: Hello"
            --type item_external --value "${mypath}/item1.sh"
            --type item_external --value "${mypath}/item2.sh::some_value"
            --type item_external --value "${mypath}/item3.sh"
        )
        exec "${commands[@]}"
        ;;
    *)
        # If started manually, show the menu
        "${0}" execute "${@}"
        ;;
esac
