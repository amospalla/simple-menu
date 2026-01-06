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

"""Text menu generation."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from simple_menu import sudo_helper
from simple_menu.configuration import get_configuration
from simple_menu.constants import interface_choices
from simple_menu.item import items
from simple_menu.item.items import get_item_class
from simple_menu.item.menu import Menu

logger = logging.getLogger(__name__)


def set_logging(verbose: int) -> None:
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG

    logging.basicConfig(level=level)


def parse_args() -> argparse.Namespace:
    """Argument parser definition."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="count", help="set verbose mode", default=0)
    parser.add_argument("-c", "--config-file", type=Path)
    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        choices=interface_choices,
    )
    parser.add_argument("-s", "--token-separator", type=str, action="append")
    command_subparser = parser.add_subparsers(dest="command", required=True)
    subparser_menu = command_subparser.add_parser("menu")
    subparser_item = command_subparser.add_parser("item")
    subparser_helper = command_subparser.add_parser("helper")

    # Menu subparser
    subparser_menu.add_argument("--title", type=str, default="Menu")
    subparser_menu.add_argument(
        "-l",
        "--loop-timeout",
        default=0.0,
        type=float,
        help="run in loop mode with this timeout",
    )
    subparser_menu.add_argument(
        "-o",
        "--run-once",
        action="store_true",
        default=False,
        help="quit menu after first selection",
    )
    subparser_menu.add_argument(
        "-t",
        "--type",
        action="append",
        required=True,
        choices=items.item_names_value,
        # nargs="+",
        help="add item type to the menu",
    )
    subparser_menu.add_argument(
        "-v",
        "--value",
        action="append",
        # nargs="+",
        required=True,
        help="item value",
    )

    # Item subparser
    subparser_item.add_argument(
        "--type",
        required=True,
        choices=items.item_names_value,
        help="item type",
    )
    subparser_item.add_argument(
        "--value",
        required=True,
        help="item value",
    )

    # Helper arguments parser
    subparser_helper.add_argument(
        "--systemd-unit-toggle",
        help="Toggle Systemd unit status.",
        type=sudo_helper.validate_unit_name,
    )
    subparser_helper.add_argument(
        "--zerotier-network-get",
        help="Get Zerotier network id status",
        type=sudo_helper.validate_zerotier_network_name,
    )
    subparser_helper.add_argument(
        "--zerotier-network-toggle",
        help="Toggle Zerotier network id",
        type=sudo_helper.validate_zerotier_network_name,
    )

    return parser.parse_args()


async def main_async(args: argparse.Namespace) -> None:
    try:
        configuration = get_configuration(
            config_file=args.config_file,
            requested_interface=args.interface,
            requested_token_separators=args.token_separator,
        )
        if args.command == "item":
            item_class = get_item_class(args.type)
            instance = item_class(
                configuration=configuration,
                value=args.value,
            )
            await instance.execute()
        elif args.command == "menu":
            await Menu(
                configuration=configuration,
                value=configuration.token_separators[0].join(
                    (
                        "title",
                        args.title,
                        "loop-timeout",
                        str(args.loop_timeout),
                        "keep-opened",
                        str(int(not args.run_once)),
                    ),
                ),
                menu_items=[
                    (
                        get_item_class(args.type[i]),
                        args.value[i],
                    )
                    for i in range(len(args.type))
                ],
            ).execute()
    except SystemExit as e:
        logger.info("Quit requested.")
        sys.exit(e.code)
    except:  # noqa:E722
        logger.exception("Error")
        sys.exit(1)


def main() -> None:
    """Main program entry point."""
    # Parse arguments and set logging.
    args = parse_args()
    set_logging(args.verbose)
    logger.info("User supplied arguments: '%s'.", args)

    if args.command == "menu" and len(args.type) != len(args.value):
        print("Error: each item type must have one and only one value.")
        sys.exit(1)

    # Run, item, menu or helper as requested.
    if args.command in {"item", "menu"}:
        # Start menu/item execution in async.
        asyncio.run(main_async(args))
    elif args.command == "helper":
        sudo_helper.Helper(args=args, program_name=Path(sys.argv[0]))


if __name__ == "__main__":
    main()
