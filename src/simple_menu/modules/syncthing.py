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

"""Syncthing abstraction for simple-menu.

The classes on this module expect to be called and forgotten.
"""

import json
import logging
import operator
import ssl
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from functools import cache, cached_property
from typing import Any, Literal, cast
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

DEFAULT_BASEURL = "http://localhost:8384"


@dataclass
class FolderErrorType:
    path: str
    error: str


@dataclass
class SystemErrorType:
    level: int
    message: str
    when: datetime


@dataclass
class SyncthingErrors:
    folders: dict[str, list[FolderErrorType]]
    system: list[SystemErrorType]


class Folder:
    """Syncthing Folder.

    Args:
        configuration: folder configuration dictionary.
        syncthing: parent Syncthing class.
        label: syncthing folder label.
        id: syncthing folder id.
    """

    def __init__(
        self,
        syncthing: "Syncthing",
        identifier: str,
        label: str,
        paused: bool,
    ) -> None:
        self.syncthing = syncthing
        self.id = identifier
        self.label = label
        self.paused = paused

    @cached_property
    def errors(self) -> list[FolderErrorType]:
        if self.paused:
            # When folder is paused the endpoint folder/errors?folder=id is
            # not available (404)
            return []
        if folder_errors := self.syncthing.get_endpoint(
            f"folder/errors?folder={self.id}",
        )["errors"]:
            return [FolderErrorType(**error) for error in folder_errors]
        return []

    @cached_property
    def status(self) -> str:
        if self.paused:
            return "paused"
        elif self.errors:
            return "error"
        else:
            # This endpoint returns 404 when folder is paused:
            return self.syncthing.get_endpoint(f"db/status?folder={self.id}")["state"]  # type:ignore[no-any-return]

    def pause_toggle(self) -> None:
        if self.paused:
            self.resume()
        else:
            self.pause()

    def pause(self) -> None:
        self.syncthing.get_endpoint(
            endpoint=f"config/folders/{self.id}",
            method="PATCH",
            data=b'{"paused": true}',
        )

    def resume(self) -> None:
        self.syncthing.get_endpoint(
            endpoint=f"config/folders/{self.id}",
            method="PATCH",
            data=b'{"paused": false}',
        )

    def __str__(self) -> str:
        return self.label


class Device:
    def __init__(self, syncthing: "Syncthing", paused: bool) -> None:
        self.syncthing = syncthing
        self.paused = paused


class Syncthing:
    def __init__(
        self,
        url: str,
        api_key: str,
    ) -> None:
        self.api_key = api_key
        self.baseurl = url
        self.headers = {"X-API-Key": api_key}
        self.initialized = False

    def initialize(self) -> None:
        if self.ping:
            self.configuration_raw = self.get_endpoint(endpoint="config")

            self.devices = [
                Device(
                    syncthing=self,
                    paused=device["paused"],
                )
                for device in self.configuration_raw["devices"]
            ]

            self.folders = [
                Folder(
                    syncthing=self,
                    identifier=folder["id"],
                    label=folder["label"],
                    paused=folder["paused"],
                )
                for folder in self.configuration_raw["folders"]
            ]
            self.folders.sort(key=operator.attrgetter("label"))

            self.initialized = True

    @cache  # noqa:B019
    def get_endpoint(
        self,
        endpoint: str,
        data: bytes = b"",
        method: Literal["GET", "POST"] = "GET",
    ) -> dict[str, Any]:
        url = f"{self.baseurl}/rest/{endpoint}"
        req = urllib.request.Request(  # noqa:S310
            url=url,
            data=data,
            headers=self.headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, context=context) as response:  # noqa:S310
                if data := response.read().decode("utf-8"):
                    return cast("dict[str, Any]", json.loads(data))
                else:
                    return {}
        except HTTPError as e:
            logger.info("Error: '%s' - '%s' - '%s'", e.code, e.reason, url)
            logger.debug(
                "Error: '%s' - '%s' - '%s'",
                e.code,
                e.reason,
                url,
                exc_info=True,
            )
            raise
        except URLError as e:
            logger.info("Error: '%s'", e.reason)
            logger.debug(
                "Error: '%s' - '%s'",
                e.reason,
                url,
                exc_info=True,
            )
            raise

    @property
    def ping(self) -> bool:
        try:
            response = self.get_endpoint(endpoint="system/ping")
        except (HTTPError, URLError):
            return False
        else:
            return bool(response["ping"] == "pong")

    @cached_property
    def paused(self) -> bool:
        return all(device.paused for device in self.devices)

    @cached_property
    def are_all_folders_paused(self) -> bool:
        return all(folder.paused for folder in self.folders)

    @cached_property
    def errors(self) -> SyncthingErrors:
        """Return both folder and system errors, if any.

        Example:
            {
                "folder": [
                    {
                        "projectes": {
                            "path": "root"
                            "error": "hashing: open /path/file: permission denied",
                        }
                    }
                ],
                "system": [
                    {
                        "level": 3,
                        "message": 'Error on folder "foo" (ctynp-xcwca): folder ...'
                        "when": "2023-11-19T15:31:28.676953755+01:00"
                    }
                ]
            }
        """
        return SyncthingErrors(
            folders={
                folder.label: folder.errors for folder in self.folders if folder.errors
            },
            system=[
                SystemErrorType(**error)
                for error in self.get_endpoint("system/error")["errors"] or []
            ],
        )

    @cached_property
    def status(self) -> str:
        if self.errors.folders or self.errors.system:
            return "error"
        elif self.paused or self.are_all_folders_paused:
            return "paused"
        else:
            return "active"

    @cached_property
    def idle(self) -> bool:
        return not {f.status for f in self.folders} - {"idle", "paused"}

    @cached_property
    def folder_statuses(self) -> set[str]:
        return {folder.status for folder in self.folders}

    def __str__(self) -> str:
        return self.status

    def pause_toggle(self) -> None:
        if self.paused:
            self.resume()
        else:
            self.pause()

    def pause(self) -> None:
        self.get_endpoint(endpoint="system/pause", method="POST", data=b"{}")

    def resume(self) -> None:
        self.get_endpoint(endpoint="system/resume", method="POST", data=b"{}")

    def get_folder_by_id_or_name(self, text: str) -> Folder:
        return next(
            iter(
                folder for folder in self.folders if text in {folder.id, folder.label}
            ),
        )
