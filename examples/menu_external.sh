#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        echo "menu :: my category :: my subcategory :: <ok> :: choices text"
        ;;
    "execute")
        # Menu options
        echo "title::My Menu"

        # Add item of type "item"
        echo "item::notification:: :: :: ::hola"

        # Add item of type "menu_inline"
        value="menu_inline"                                                            # Item type
        value+=":: menu :: :: :: :: Foo"                                               # Item text
        value+=":: title :: My Choices Title :: keep-opened :: 1 :: loop-timeout::0.0" # Menu title
        value+=":: item,,action,, ,, ,, ,,notify value 1,,notify-send,,val1"           # Subitem 1
        value+=":: item,,action,, ,, ,, ,,notify value 2,,notify-send,,val2"           # Subitem 2
        echo "${value}"
        ;;
    *)
        # Show menu when called manually.
        exec simple-menu item --type menu_external --value "${0}"
        ;;
esac
