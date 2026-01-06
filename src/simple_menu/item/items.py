# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jordi Marqués <jordi.amospalla.es>
#
# This file is part of simple-menu.
#
# simple-menu is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# simple-menu is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# simple-menu. If not, see <https://www.gnu.org/licenses/>.

import logging
import sys
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .base import BaseItem

logger = logging.getLogger(__name__)

# Used for argparse choices.
item_names_value = (
    "audiomenu",
    "item",
    "item_external",
    "menu_external",
    "menu_inline",
    "syncthingmenu",
    "systemdunit",
    "zerotiernetwork",
)

# Used on get_item_class() as variable type.
item_names_type = Literal[
    "audiomenu",
    "item",
    "item_external",
    "menu_external",
    "menu_inline",
    "syncthingmenu",
    "systemdunit",
    "zerotiernetwork",
]


def get_item_class(name: item_names_type) -> type["BaseItem"]:
    klass: type[BaseItem]
    logger.debug("get_item_class: asked for '%s'.", name)
    match name.strip().lower():
        case "audiomenu":
            from simple_menu.item.sound import MenuAudio  # noqa: PLC0415

            klass = MenuAudio
        case "menu_inline":
            from simple_menu.item.menu_inline import MenuInline  # noqa: PLC0415

            klass = MenuInline
        case "menu_external":
            from simple_menu.item.menu_external import MenuExternal  # noqa: PLC0415

            klass = MenuExternal
        case "item":
            from simple_menu.item.item import Item  # noqa: PLC0415

            klass = Item
        case "item_external":
            from simple_menu.item.item_external import ItemExternal  # noqa: PLC0415

            klass = ItemExternal
        case "syncthingmenu":
            from simple_menu.item.syncthing import ItemSyncthing  # noqa: PLC0415

            klass = ItemSyncthing
        case "systemdunit":
            from simple_menu.item.systemd import ItemSystemdUnit  # noqa: PLC0415

            klass = ItemSystemdUnit
        case "zerotiernetwork":
            from simple_menu.item.zerotier import ItemZerotierNetwork  # noqa: PLC0415

            klass = ItemZerotierNetwork
        case _:
            logger.error(f"Invalid item type '{name}'.")
            sys.exit(1)
    return klass
