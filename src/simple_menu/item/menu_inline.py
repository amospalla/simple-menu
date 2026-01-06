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

from .base import BaseItem
from .items import get_item_class
from .menu import Menu

logger = logging.getLogger(__name__)


def get_item_type_value(
    value: str,
    token_separators: list[str],
) -> tuple[type[BaseItem], str]:
    tokens = value.split(token_separators[1])
    item_type = get_item_class(tokens.pop(0))  # type:ignore[arg-type]
    inner_value = token_separators[1].join(tokens)

    # Reduce token separator level on value to be returned
    for level in range(len(token_separators) - 1):
        inner_value = inner_value.replace(
            token_separators[level + 1],
            token_separators[level],
        )

    return item_type, inner_value


class MenuInline(Menu):
    item_type = "MenuChoices"

    async def set_items(self) -> None:
        items_text = self.value.split(self.delimiter)
        self.items = []
        for item_text in items_text:
            item_type, item_value = get_item_type_value(
                item_text,
                self.configuration.token_separators,
            )
            self.items.append(
                (
                    item_type,
                    item_value,
                    # self.delimiter.join(
                    #     item_value.split(self.configuration.token_separators[1]),
                    # ),
                ),
            )

        logger.debug(f"{self.item_type}.execute(): End")
