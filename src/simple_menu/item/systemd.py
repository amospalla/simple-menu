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
import time
from pathlib import Path

from .base import BaseItem, ItemTextType

logger = logging.getLogger(__name__)


class ItemSystemdUnit(BaseItem):
    """Item to manage systemd services."""

    item_type = "ItemSystemdUnit"

    def __init__(self, *args, **kwargs) -> None:  # type:ignore[no-untyped-def]
        super().__init__(*args, **kwargs)

        if self.value.startswith("user" + self.delimiter):
            self.user = True
            self.unit = self.value.replace("user" + self.delimiter, "")
            self.user_string = "--user"
            self.text_category = "Systemd"
            self.text_subcategory = "User"
        else:
            self.user = False
            self.unit = self.value
            self.user_string = ""
            self.text_category = "Systemd"
            self.text_subcategory = ""

    async def is_unit_active(self) -> bool:
        """Return if the systemd daemon is running."""
        start_time = time.perf_counter()
        elapsed = time.perf_counter() - start_time
        logger.debug("self.unit='%s' is-active elapsed='%s'", self.unit, elapsed)

        proc = await asyncio.create_subprocess_shell(
            f"systemctl {self.user_string} is-active --quiet {self.unit}",
        )
        await proc.wait()
        return not proc.returncode

    async def unit_exists(self) -> bool:
        _cmd = f"systemctl {self.user_string} cat {self.unit}"
        proc = await asyncio.create_subprocess_shell(
            cmd=f"systemctl {self.user_string} cat {self.unit}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return not proc.returncode

    async def set_text(self) -> None:
        """Sets the text that this item shows on the menu."""
        if await self.unit_exists():
            self.texts.text = f"{self.unit.replace('.service', '')} (toggle)"
            if await self.is_unit_active():
                self.texts.status = "<running>"
            else:
                self.texts.status = "<stopped>"
        else:
            self.texts.text = ""

        self.texts.type = ItemTextType.action
        self.texts.category = self.text_category
        self.texts.subcategory = self.text_subcategory

    async def execute(self) -> None:
        """Execute this item."""
        if not await self.unit_exists():
            logger.info("Systemd unit does not exist, exit.")
            return

        if self.user:
            await self.execute_user()
        else:
            await self.execute_system()

    async def execute_system(self) -> None:
        logger.info("Systemd unit exists, toggle it: '%s'.", self.unit)
        command_args = [
            "sudo",
            str(Path(sys.argv[0]).resolve()),
            "helper",
            "--systemd-unit-toggle",
            self.unit,
        ]
        logger.debug("Executing: '%s'.", command_args)

        subprocess.run(  # noqa: ASYNC221
            args=command_args,
            check=False,
        )

    async def execute_user(self) -> None:
        proc = subprocess.run(  # noqa: ASYNC221
            args=f"systemctl --user is-active --quiet {self.unit}",
            shell=True,
            check=False,
        )
        if proc.returncode == 0:
            subprocess.run(  # noqa: ASYNC221
                args=f"systemctl --user stop --quiet {self.unit}",
                shell=True,
                check=False,
            )
        else:
            subprocess.run(  # noqa: ASYNC221
                args=f"systemctl --user start --quiet {self.unit}",
                shell=True,
                check=False,
            )
