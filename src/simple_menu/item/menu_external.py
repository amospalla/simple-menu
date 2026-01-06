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

"""External Menu.

This Menu takes a script from its value and delegates to it:
    - get_text: menu entry text generation.
    - get_items: build menu including title, options and items list.
"""

import asyncio
import logging

from .items import get_item_class
from .menu import Menu

logger = logging.getLogger(__name__)


class MenuExternal(Menu):
    item_type = "MenuExternal"

    def __init__(self, *args, **kwargs) -> None:  # type:ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.command = self.value.split(self.delimiter)

    async def set_text(self) -> None:
        """Get text from external program and return it."""
        logger.debug("%s.set_text(): self.value='%s'", self.item_type, self.value)
        command = [self.command[0], "get_text", *self.command[1:]]
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

    async def set_items(self) -> None:
        """Run external program action."""
        command = [self.command[0], "execute", *self.command[1:]]

        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        stdout, _stderr = await proc.communicate()
        lines = stdout.decode().rstrip().splitlines()

        self.title, self.keep_opened, self.loop_timeout, _value = (
            self.value2menu_options(lines[0])
        )
        if lines[0].split(self.delimiter)[0] in {
            "title",
            "keep-opened",
            "loop-timeout",
        }:
            del lines[0]

        self.items = []

        for line in lines:
            line_tokens = line.split(self.delimiter)

            item_type = get_item_class(line_tokens.pop(0))  # type:ignore[arg-type]
            item_value = self.delimiter.join(line_tokens)
            self.items.append((item_type, item_value))
