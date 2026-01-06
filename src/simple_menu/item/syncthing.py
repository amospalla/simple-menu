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

from simple_menu.modules.syncthing import Syncthing

from .base import BaseItem, ItemTextType
from .item import Item
from .menu import Menu

logger = logging.getLogger(__name__)

icons: dict[str, str] = {
    "error": "<warning>",
    "idle": "<ok>",
    "paused": "<paused>",
    "scan-waiting": "<reload>",
    "scanning": "<reload>",
    "sync-preparing": "<reload>",
    "sync-waiting": "<reload>",
    "syncing": "<reload>",
}


class ItemSyncthing(Menu):
    item_type = "ItemSyncthing"

    async def set_title(self) -> None:
        self.title = "Syncthing"

    async def set_text(self) -> None:
        self.texts.type = ItemTextType.menu
        self.texts.category = "Syncthing"

        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()

        status_icons: list[str] = []
        syncthing.initialize()
        if syncthing.initialized:
            status_text = syncthing.status
            match syncthing.status:
                case "error":
                    status_icons.append("<warning>")
                case "paused":
                    status_icons.append("<paused>")
                case "active":
                    match syncthing.idle:
                        case True:
                            status_icons.append("<ok>")
                        case False:
                            status_icons.append("<reload>")
                            extra_status = " ".join(
                                icons[s] for s in syncthing.folder_statuses
                            )
                            status_text += f" ({extra_status})"
            self.texts.text = status_text
        else:
            self.texts.type = ItemTextType.notification
            self.texts.text = "Syncthing unavailable"
            status_icons.append("<error>")
        self.texts.status = " ".join(set(status_icons))

    async def set_items(self) -> None:
        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()
        self.items.clear()  # This menu recreates dynamically its iitems on each call.
        if not syncthing.initialized:
            return

        for error in syncthing.errors.system:
            self.items.append(
                (
                    Item,
                    self.delimiter.join(
                        (
                            "notification",
                            "",
                            "",
                            "<warning>",
                            f"{error.message}",
                        ),
                    ),
                ),
            )
        for folder_with_errors in syncthing.errors.folders:
            for folder_error in syncthing.errors.folders[folder_with_errors]:
                self.items.append(
                    (
                        Item,
                        self.delimiter.join(
                            (
                                "notification",
                                "",
                                "",
                                "<warning>",
                                f"({folder_error.path}): {folder_error.error}",
                            ),
                        ),
                    ),
                )
        self.items.append((ItemSyncthingPauseToggle, ""))
        for folder in syncthing.folders:
            self.items.append(
                (
                    ItemSyncthingFolderMenu,
                    folder.id,
                ),
            )


class ItemSyncthingFolderMenu(Menu):
    item_type = "ItemSyncthingFolderMenu"

    async def set_text(self) -> None:
        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()
        folder = syncthing.get_folder_by_id_or_name(self.value)
        self.title += f" {folder}"
        self.texts.category = "Folder"
        self.texts.type = ItemTextType.menu
        if not folder:
            self.texts.text = ""
            return

        self.texts.category = "<folder>"

        if folder.paused:
            self.texts.status = "<paused>"
        elif folder.errors:
            self.texts.status = "<warning>"
        else:
            self.texts.status = icons[folder.status]

        if folder.status != "idle" and not folder.paused:
            self.texts.text = f"{folder.label} ({folder.status})"
        else:
            self.texts.text = f"{folder.label}"

        self.title = f"Syncthing/Folder/<{folder.label}>"

    async def set_items(self) -> None:
        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()
        self.items.clear()  # This menu recreates dynamically its iitems on each call.
        if syncthing.initialized:
            folder = syncthing.get_folder_by_id_or_name(self.value)
            if folder:
                if (
                    not folder.paused and folder.errors
                ):  # A paused folder can not be checked for errors.
                    for error in folder.errors:
                        self.items.append(
                            (
                                Item,
                                self.delimiter.join(
                                    (
                                        "notification",
                                        "",
                                        "",
                                        "<warning>",
                                        (
                                            f"{error.path} {error.error}"
                                            f"     <warning>  path: {error.path}, "
                                            f"error: {error.error}"
                                        ),
                                    ),
                                ),
                            ),
                        )
                self.items.append(
                    (ItemSyncthingFolderPauseToggle, self.value),
                )


class ItemSyncthingPauseToggle(BaseItem):
    item_type = "ItemSyncthingPauseToggle"

    async def set_text(self) -> None:
        self.texts.type = ItemTextType.action
        self.texts.category = "Global"
        self.texts.text = "toggle"
        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()
        if syncthing.paused:
            self.texts.status = "<paused>"
        else:
            self.texts.status = "<running>"

    async def execute(self) -> None:
        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()
        syncthing.pause_toggle()


class ItemSyncthingFolderPauseToggle(BaseItem):
    item_type = "ItemSyncthingFolderPauseToggle"

    async def set_text(self) -> None:
        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()
        self.texts.type = ItemTextType.action
        self.texts.text = ""
        if syncthing.initialized:
            folder = syncthing.get_folder_by_id_or_name(self.value)
            if folder:
                self.texts.text = "toggle <change>"
                if syncthing.get_folder_by_id_or_name(self.value).paused:
                    self.texts.status = "<paused>"
                else:
                    self.texts.status = "<running>"

    async def execute(self) -> None:
        syncthing = Syncthing(
            url=self.configuration.menu_syncthing_api_url,
            api_key=self.configuration.menu_syncthing_api_token,
        )
        syncthing.initialize()
        folder = syncthing.get_folder_by_id_or_name(self.value)
        if folder:
            folder.pause_toggle()
