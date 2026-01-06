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

import asyncio
import logging
import subprocess
import sys

from .base import BaseItem, ItemTextType

logger = logging.getLogger(__name__)


class ItemZerotierNetwork(BaseItem):
    """Item to manage systemd services."""

    item_type = "ItemZerotierNetwork"

    def __init__(self, *args, **kwargs) -> None:  # type:ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.network_id, self.network_name = kwargs["value"].split(self.delimiter)

    async def set_text(self) -> None:
        """Returns the text that this item shows on the menu."""
        command = f"sudo {sys.argv[0]} helper --zerotier-network-get {self.network_id}"
        logger.debug("Executing: '%s'.", command)
        zerotier_status = await asyncio.create_subprocess_shell(
            cmd=command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await zerotier_status.wait()
        stdout_bytes, _stderr_bytes = await zerotier_status.communicate()
        stdout = stdout_bytes.decode().strip()

        match stdout:
            case "started":
                self.texts.status = "<running>"
                self.texts.text = f"{self.network_name} (toggle)"
            case "stopped":
                self.texts.status = "<stopped>"
                self.texts.text = f"{self.network_name} (toggle)"
            case "zerotier-one is not running":
                self.texts.text = ""  # Disable

        self.texts.type = ItemTextType.action
        self.texts.category = "Zerotier"
        self.texts.subcategory = "network"

    async def execute(self) -> None:
        logger.info(
            "Zerotier-one network connected, toggle it: %s, %s.",
            self.network_id,
            self.network_name,
        )
        command_args = [
            "sudo",
            sys.argv[0],
            "helper",
            "--zerotier-network-toggle",
            self.network_id,
        ]
        logger.debug("Executing: '%s'.", command_args)

        subprocess.run(  # noqa: ASYNC221
            args=command_args,
            check=False,
        )
