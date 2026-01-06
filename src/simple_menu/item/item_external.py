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

"""External Item."""

import asyncio
import logging
import sys

from simple_menu.constants import QUIT_EXIT_CODE

from .base import BaseItem

logger = logging.getLogger(__name__)


class ItemExternal(BaseItem):
    """External program item class."""

    item_type = "ItemExternal"

    async def set_text(self) -> None:
        """Get text from external program and return it."""
        logger.debug("%s.set_text(): Start", self.item_type)
        logger.debug("%s.set_text(): self.value='%s'", self.item_type, self.value)
        command = self.value.split(self.delimiter)
        command = [command[0], "get_text", *command[1:]]
        logger.debug("%s.set_text(): command='%s'", self.item_type, command)
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        stdout, _stderr = await proc.communicate()
        text = stdout.decode().rstrip()
        self.texts, _value = self.str2item_texts(
            text,
            token_separator=self.delimiter,
        )
        logger.debug("%s.set_text(): End", self.item_type)

    async def execute(self) -> None:
        """Run external program action."""
        logger.debug("%s.execute(): Start", self.item_type)
        logger.debug("%s.execute(): self.value='%s'", self.item_type, self.value)
        command = self.value.split(self.delimiter)
        command = [command[0], "execute", *command[1:]]
        logger.debug("%s.execute(): command='%s'", self.item_type, command)

        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()

        if proc.returncode == QUIT_EXIT_CODE:
            sys.exit(QUIT_EXIT_CODE)

        logger.debug("%s.execute(): End", self.item_type)
