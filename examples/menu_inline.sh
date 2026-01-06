#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        echo "menu::::::::choices text"
        ;;
    "execute")
        # This is equivalent
        # value="title::My Menu Title"
        # value+="::keep-opened::1"
        # value+="::loop-timeout::0.0"
        # value+="::item,,action,,,,,,,,notify value 1,,notify-send,,val1"
        # value+="::item,,action,,,,,,,,notify value 2,,notify-send,,val2"

        # value+="::menu_inline,,menu,,,,,,,,submenu entry text"
        # value+=",,title,,My SubMenu Title"
        # value+=",,keep-opened,,1"
        # value+=",,loop-timeout,,0.0"
        # value+=",,item;;action;;;;;;;;notify value 1;;notify-send;;val1"
        # value+=",,item;;action;;;;;;;;notify value 2;;notify-send;;val2"

        value="
            title :: My Menu Title :: keep-opened :: 1 :: loop-timeout :: 0.0 ::
            item ,, action ,, ,, ,, ,, notify value 1 ,,notify-send,,val1::
            item ,, action ,, ,, ,, ,, notify value 2 ,,notify-send,,val2::
            menu_inline,,
                menu,,,,,,,,submenu entry text,,
                title ,, My SubMenu Title ,, keep-opened ,, 1 ,, loop-timeout ,, 0.0 ,,
                item;;
                    action;;;;;;;;notify value 3
                    ;;notify-send;;val3,,
                item;;
                    action;;;;;;;;notify value 4
                    ;;notify-send;;val4"
        exec simple-menu item --type menu_inline --value "${value}"
        ;;
    "")
        # Show the menu when the script is manually executed.
        "${0}" execute
        ;;
esac
