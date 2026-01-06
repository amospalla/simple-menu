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

"""Helper for sudo actions."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from simple_menu.configuration import get_configuration
from simple_menu.constants import PROGRAM_NAME

VALID_UNIT_NAME = re.compile(r"^[a-zA-Z0-9_.$S-]+$")
VALID_ZEROTIER_NETWORK_NAME = re.compile(r"^[a-z0-9]+$")


def validate_unit_name(unit_name: str) -> str:
    if not VALID_UNIT_NAME.match(unit_name):
        print(f"Error: invalid unit name {unit_name}.")
        raise argparse.ArgumentTypeError(f"Invalid unit name {unit_name}.")
    return unit_name


def validate_zerotier_network_name(unit_name: str) -> str:
    if not VALID_UNIT_NAME.match(unit_name):
        print(f"Error: invalid unit name {unit_name}.")
        raise argparse.ArgumentTypeError(f"Invalid unit name {unit_name}.")
    return unit_name


class Helper:
    def __init__(self, args: argparse.Namespace, program_name: Path) -> None:
        self.args = args
        self.program_name = program_name

        config_file = Path(f"/etc/{PROGRAM_NAME}/{PROGRAM_NAME}.toml")
        if not config_file.exists():
            print(f"Error: configuration file {config_file} does not exist.")
            sys.exit(1)

        self.configuration = get_configuration(
            config_file=config_file,
            requested_interface="auto",
            requested_token_separators=args.token_separators,
        )

        if self.args.systemd_unit_toggle:
            self.systemd_unit_toggle(unit_name=args.systemd_unit_toggle)
        elif self.args.zerotier_network_get:
            self.zerotier_network_get_status_or_exit(
                zerotier_network=args.zerotier_network_get,
            )
        elif self.args.zerotier_network_toggle:
            self.zerotier_network_toggle_or_exit(args.zerotier_network_toggle)
        else:
            print("Error: no action specified.")
            sys.exit(1)

    @staticmethod
    def systemd_unit_is_active(unit_name: str) -> bool:
        proc = subprocess.run(
            args=["systemctl", "is-active", "--quiet", unit_name],
            check=False,
        )
        return not proc.returncode

    def systemd_unit_toggle(self, unit_name: str) -> None:
        if unit_name in self.configuration.helper_systemd_toggle_allowed:
            if self.systemd_unit_is_active(unit_name):
                subprocess.run(  # noqa:S603
                    ["systemctl", "stop", "--quiet", unit_name],  # noqa:S607
                    check=False,
                )
            else:
                subprocess.run(  # noqa:S603
                    ["systemctl", "start", "--quiet", unit_name],  # noqa:S607
                    check=False,
                )
        else:
            print(f"Error: daemon {unit_name} is not allowed to be toggled.")
            sys.exit(1)

    def zerotier_network_allowed_or_exit(self, zerotier_network: str) -> None:
        if zerotier_network not in self.configuration.helper_zerotier_allowed:
            sys.exit(0)

    def zerotier_network_get_status_or_exit(self, zerotier_network: str) -> None:
        self.zerotier_network_allowed_or_exit(zerotier_network)

        if self.systemd_unit_is_active("zerotier-one"):
            proc = subprocess.run(
                args=["zerotier-cli", "listnetworks"],
                check=True,
                capture_output=True,
                text=True,
            )
            if zerotier_network in proc.stdout:
                print("started")
            else:
                print("stopped")
        else:
            print("zerotier-one is not running")

    def zerotier_network_toggle_or_exit(self, zerotier_network: str) -> None:
        self.zerotier_network_allowed_or_exit(zerotier_network)

        proc = subprocess.run(
            args=["zerotier-cli", "listnetworks"],
            check=True,
            capture_output=True,
            text=True,
        )
        if zerotier_network in proc.stdout:
            subprocess.run(
                args=["zerotier-cli", "leave", zerotier_network],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            subprocess.run(
                args=["zerotier-cli", "join", zerotier_network],
                check=True,
                capture_output=True,
                text=True,
            )

    def zerotier_network_get_status(self, zerotier_network: str) -> None:
        self.zerotier_network_allowed_or_exit(zerotier_network)
        proc = subprocess.run(  # noqa:S603
            ["systemctl", "is-active", "--quiet", zerotier_network],  # noqa:S607
            check=False,
        )
        if proc.returncode == 0:
            subprocess.run(  # noqa:S603
                ["systemctl", "stop", "--quiet", zerotier_network],  # noqa:S607
                check=False,
            )
        else:
            subprocess.run(  # noqa:S603
                ["systemctl", "start", "--quiet", zerotier_network],  # noqa:S607
                check=False,
            )
