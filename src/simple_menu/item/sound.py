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

"""Sound devices controls.

MenuAudio:
- text: "audio menu..."
- items:
  - MenuAudioNode("devices")
  - MenuAudioNode("sinks")
  - MenuAudioNode("sources")
  - MenuAudioNode("streams")

MenuAudioNode:
- text: "device ..." | "sink..." | "source..." | "stream..."
- items:
  - if device:             MenuAudioNodeDevice("profiles::<id>")
  - if device:             MenuAudioNodeDevice("routes::<id>")
  - if sink|source:        ItemAudioNodeChange("setdefault::<id>")
  - if sink|source|stream: ItemAudioNodeChange("volume+::<id>")
  - if sink|source|stream: ItemAudioNodeChange("volume-::<id>")
  - if sink|source|stream: ItemAudioNodeChange("togglemute::<id>")
  - if stream:             ItemAudioNodeChange("move::<stream_id>::<sinksource_id>")

MenuAudioNodeDevice:
- text: "current profile ..." | "current port ..."
- items:
  - ItemAudioDeviceChange("profiles::<node_id>::<profile_index")
  - ...
  - ItemAudioDeviceChange("profiles::<node_id>::<profile_index")
  - ItemAudioDeviceChange("routes::<node_id>::<profile_index")
  - ...
  - ItemAudioDeviceChange("routes::<node_id>::<profile_index")

ItemAudioDeviceChange:
- text: "this device/profile text" | "this device/route/text"
- execute: set this profile or route default on the device.

ItemAudioNodeChange:
- text: "is default/set default" | "togglemute..." | "volume..."
- execute: set default, volume+/-, toggle mute.
"""

import asyncio
import logging
from typing import Any, Literal

from simple_menu.modules.pipewire import Const, Pipewire

from .base import BaseItem, ItemTextType
from .item import Item
from .menu import Menu

logger = logging.getLogger(__name__)


class MenuAudio(Menu):
    item_type = "MenuAudio"

    async def set_title(self) -> None:
        self.title = "Audio"

    async def set_text(self) -> None:
        self.texts.type = ItemTextType.menu
        self.texts.category = "Audio"

        pipewire = Pipewire()
        await pipewire.build()

        default_sink = pipewire.default_sink
        default_source = pipewire.default_source

        if pipewire.get_node_mute(default_sink):
            self.texts.status = "<volume-muted>"
        else:
            self.texts.status = "<volume-max>"

        volume_sink = pipewire.get_node_volume(default_sink)
        volume_source = pipewire.get_node_volume(default_source)
        if pipewire.get_node_mute(default_source):
            muted_source = "<microphone-muted>"
        else:
            muted_source = "<microphone>"

        self.texts.text = (
            f"{default_sink['description']}({volume_sink}%) / "
            f"{muted_source} {default_source['description']}({volume_source}%)"
        )

    async def set_items(self) -> None:
        self.items.clear()  # This menu recreates dynamically its iitems on each call.
        pipewire = Pipewire()
        await pipewire.build()
        ids: list[int] = []
        ids.extend([node["id"] for node in pipewire.devices])
        ids.extend(
            [
                node["id"]
                for node in pipewire.sinks_sources
                if node["media.class"] == Const.Props.MediaClass.AudioSink
                and node["description"]
                not in self.configuration.menu_sound_ignore_nodes
            ],
        )
        ids.extend(
            [
                node["id"]
                for node in pipewire.sinks_sources
                if node["media.class"] == Const.Props.MediaClass.AudioSource
                and node["description"]
                not in self.configuration.menu_sound_ignore_nodes
            ],
        )
        ids.extend(
            [
                node["id"]
                for node in pipewire.streams
                if node["media.class"] == Const.Props.MediaClass.StreamOutputAudio
                and f"{node['node.name']}:{node['media.name']}"
                not in self.configuration.menu_sound_ignore_nodes
            ],
        )
        ids.extend(
            [
                node["id"]
                for node in pipewire.streams
                if node["media.class"] == Const.Props.MediaClass.StreamInputAudio
                and f"{node['node.name']}:{node['media.name']}"
                not in self.configuration.menu_sound_ignore_nodes
            ],
        )
        self.items = [(MenuAudioNode, str(identifier)) for identifier in ids]


class MenuAudioNode(Menu):
    item_type = "MenuAudioNode"
    lock = asyncio.Lock()

    async def set_shared_data(self) -> Pipewire:
        pipewire = Pipewire()
        await pipewire.build()
        return pipewire

    async def set_text(self) -> None:  # noqa: C901
        """Returns the text that this item shows on the menu."""
        pipewire = await self.get_shared_data()
        node = pipewire.get_node_by_id(int(self.value))
        self.texts.type = ItemTextType.menu

        match node["media.class"]:
            case Const.Props.MediaClass.AudioDevice:
                self.texts.category = "Card"
                self.texts.text = node["description"]
                name = node["description"]
            case Const.Props.MediaClass.AudioSink:
                volume = pipewire.get_node_volume(node)
                self.texts.status = "<speaker>"
                if pipewire.get_node_mute(node):
                    self.texts.status = "<speaker-muted>"
                if pipewire.default_sink["id"] == node["id"]:
                    self.texts.status = f"<ok> {self.texts.status}"

                self.texts.category = "Output"
                self.texts.text = f"({volume:>3}%) {node['description']}"
                name = node["description"]
            case Const.Props.MediaClass.AudioSource:
                volume = pipewire.get_node_volume(node)
                self.texts.status = "<microphone>"
                if pipewire.get_node_mute(node):
                    self.texts.status = "<microphone-muted>"
                if pipewire.default_source["id"] == node["id"]:
                    self.texts.status = f"<ok> {self.texts.status}"

                self.texts.category = "Input"
                self.texts.text = f"({volume:>3}%) {node['description']}"
                name = node["description"]
            case Const.Props.MediaClass.StreamInputAudio:
                volume = pipewire.get_node_volume(node)
                self.texts.status = "<recording>"
                if pipewire.get_node_mute(node):
                    self.texts.status = "<microphone-muted> <recording>"
                self.texts.category = "Recording"
                self.texts.text = (
                    f"({volume:>3}%) {node['node.name']}:{node['media.name']}"
                )
                name = f"{node['node.name']}:{node['media.name']}"
            case Const.Props.MediaClass.StreamOutputAudio:
                volume = pipewire.get_node_volume(node)
                self.texts.status = "<playing>"
                if pipewire.get_node_mute(node):
                    self.texts.status = "<volume-muted> <playing>"
                self.texts.category = "Playback"
                self.texts.text = (
                    f"({volume:>3}%) {node['node.name']}:{node['media.name']}"
                )
                name = f"{node['node.name']}:{node['media.name']}"
        self.title = f"Audio/{self.texts.category}/<{name}>"

    async def set_items(self) -> None:
        """Starts Sound Sink menu."""
        self.items.clear()  # This menu recreates dynamically its iitems on each call.
        pipewire = Pipewire()
        await pipewire.build()
        node = pipewire.get_node_by_id(int(self.value))
        match node["media.class"]:
            case Const.Props.MediaClass.AudioDevice:
                self.items.append(
                    (MenuAudioNodeDevice, "profiles" + self.delimiter + self.value),
                )
                self.items.append(
                    (MenuAudioNodeDevice, "ports" + self.delimiter + self.value),
                )
            case Const.Props.MediaClass.AudioSink | Const.Props.MediaClass.AudioSource:
                self.items.append(
                    (ItemAudioNodeChange, "togglemute" + self.delimiter + self.value),
                )
                self.items.append(
                    (ItemAudioNodeChange, "volume+" + self.delimiter + self.value),
                )
                self.items.append(
                    (ItemAudioNodeChange, "volume-" + self.delimiter + self.value),
                )
                self.items.append(
                    (ItemAudioNodeChange, "setdefault" + self.delimiter + self.value),
                )
            case Const.Props.MediaClass.StreamInputAudio:
                self.items.append(
                    (ItemAudioNodeChange, "togglemute" + self.delimiter + self.value),
                )
                self.items.append(
                    (ItemAudioNodeChange, "volume+" + self.delimiter + self.value),
                )
                self.items.append(
                    (ItemAudioNodeChange, "volume-" + self.delimiter + self.value),
                )
                for source in pipewire.sources:
                    self.items.append(
                        (
                            ItemAudioNodeChange,
                            "move"
                            + self.delimiter
                            + self.value
                            + self.delimiter
                            + str(source["id"]),
                        ),
                    )
            case Const.Props.MediaClass.StreamOutputAudio:
                self.items.append(
                    (ItemAudioNodeChange, "togglemute" + self.delimiter + self.value),
                )
                self.items.append(
                    (ItemAudioNodeChange, "volume+" + self.delimiter + self.value),
                )
                self.items.append(
                    (ItemAudioNodeChange, "volume-" + self.delimiter + self.value),
                )
                for sink in pipewire.sinks:
                    self.items.append(
                        (
                            ItemAudioNodeChange,
                            "move"
                            + self.delimiter
                            + self.value
                            + self.delimiter
                            + str(sink["id"]),
                        ),
                    )


class MenuAudioNodeDevice(Menu):
    """Menu generator for an Audio Device.

    Accepts values:print
    - "profiles::<node_id>"
    - "ports::<node_id>"
    """

    item_type = "MenuAudioDeviceNode"
    lock = asyncio.Lock()

    async def set_shared_data(self) -> Pipewire:
        pipewire = Pipewire()
        await pipewire.build()
        return pipewire

    async def set_text(self) -> None:
        pipewire = await self.get_shared_data()
        action, node_str = self.value.split(self.delimiter)
        node = pipewire.get_node_by_id(int(node_str))
        self.texts.type = ItemTextType.menu

        match action:
            case "profiles":
                self.texts.category = "Profile"
                self.texts.text = node["profile"]["description"]
                self.title = f"Audio/Card/<{node['description']}>/Profiles"
            case "ports":
                self.texts.category = "Port"
                self.texts.text = node["route"]["description"]
                self.title = f"Audio/Card/<{node['description']}>/Ports"

    async def set_items(self) -> None:
        """Starts Device menu."""
        self.items.clear()  # This menu recreates dynamically its iitems on each call.
        pipewire = Pipewire()
        await pipewire.build()
        action, node_str = self.value.split(self.delimiter)
        node = pipewire.get_node_by_id(int(node_str))
        match action:
            case "profiles":
                self.items.append(
                    (
                        Item,
                        self.delimiter.join(
                            (
                                "notification",
                                "",
                                "",
                                "<ok>",
                                f"{node['profile']['description']}",
                            ),
                        ),
                    ),
                )
                self.items.extend(
                    [
                        (
                            ItemAudioDeviceChange,
                            self.delimiter.join(
                                ("profiles", str(node["id"]), str(profile["index"])),
                            ),
                        )
                        for profile in node["profiles"]
                        if profile["available"] != "no"
                        and profile["index"] != node["profile"]["index"]
                    ],
                )
            case "ports":
                self.items.append(
                    (
                        Item,
                        self.delimiter.join(
                            (
                                "notification",
                                "",
                                "",
                                "<ok>",
                                f"{node['route']['description']}",
                            ),
                        ),
                    ),
                )
                self.items.extend(
                    [
                        (
                            ItemAudioDeviceChange,
                            self.delimiter.join(
                                ("ports", str(node["id"]), str(route["index"])),
                            ),
                        )
                        for route in node["routes"]
                        if route["available"] != "no"
                        and route["index"] != node["route"]["index"]
                    ],
                )


class ItemAudioDeviceChange(BaseItem):
    """Menu item to set a device audio profile or port.

    Example:
    - "profiles::<node_id>::<profile_id>"
    - "ports::<node_id>::<port_id>"
    """

    item_type = "ItemAudioDeviceChange"
    lock = asyncio.Lock()

    async def set_shared_data(self) -> Pipewire:
        pipewire = Pipewire()
        await pipewire.build()
        return pipewire

    async def set_text(self) -> None:
        pipewire = await self.get_shared_data()
        action, node_str, item_id = self.value.split(self.delimiter)
        node = pipewire.get_node_by_id(int(node_str))
        self.texts.type = ItemTextType.action

        match action:
            case "profiles":
                profile = next(
                    p for p in node["profiles"] if p["index"] == int(item_id)
                )
                self.texts.text = (
                    f"{profile['description']} (available {profile['available']})"
                )
            case "ports":
                port = next(p for p in node["routes"] if p["index"] == int(item_id))
                self.texts.text = (
                    f"{port['description']} (available {port['available']})"
                )

    async def execute(self) -> None:
        pipewire = await self.get_shared_data()
        action, node_str, item_id = self.value.split(self.delimiter)
        match action:
            case "profiles":
                await pipewire.set_device_profile(int(node_str), int(item_id))
            case "ports":
                await pipewire.set_device_route(int(node_str), int(item_id))


class ItemAudioNodeChange(BaseItem):
    """Items to manipulate a node.

    Accepts values:
    - "setdefault:<node_id>"  # only available to sink or sources.
    - "volume+:<node_id>"
    - "volume-:<node_id>"
    - "togglemute:<node_id>"
    - "move:<stream_id>:<sink_source_id>"  # only available to streams.
    """

    item_type = "ItemAudioNodeChange"
    lock = asyncio.Lock()

    async def set_shared_data(self) -> Pipewire:
        pipewire = Pipewire()
        await pipewire.build()
        return pipewire

    def get_node_type(self, node: dict[str, Any]) -> Literal["sink", "source"]:
        match node["media.class"]:
            case Const.Props.MediaClass.AudioSink:
                return "sink"
            case Const.Props.MediaClass.AudioSource:
                return "source"
        raise ValueError("Nothing to return from get_node_type()")

    async def is_node_default(self, node: dict[str, Any]) -> bool:
        pipewire: Pipewire = await self.get_shared_data()
        node_type = self.get_node_type(node)
        return (node_type == "sink" and pipewire.default_sink["id"] == node["id"]) or (
            node_type == "source" and pipewire.default_source["id"] == node["id"]
        )

    async def set_text(self) -> None:  # noqa: C901, PLR0912, PLR0915
        pipewire: Pipewire = await self.get_shared_data()
        if len(self.value.split(self.delimiter)) == 2:  # noqa: PLR2004
            action, node_str = self.value.split(self.delimiter)
        else:
            action, node_str, destination_str = self.value.split(self.delimiter)
        node = pipewire.get_node_by_id(int(node_str))

        self.texts.type = ItemTextType.menu

        match action:
            case "setdefault":
                node_type = self.get_node_type(node)
                if await self.is_node_default(node):
                    self.texts.type = ItemTextType.notification
                    self.texts.status = "<ok>"
                    self.texts.text = f"already default {node_type}"
                else:
                    self.texts.type = ItemTextType.action
                    self.texts.status = "<configuration>"
                    self.texts.text = f"set default {node_type}"
            case "volume+":
                volume = pipewire.get_node_volume(node)
                self.texts.type = ItemTextType.action
                self.texts.status = f"{volume}% <upper>"
                self.texts.text = "volume"
            case "volume-":
                volume = pipewire.get_node_volume(node)
                self.texts.type = ItemTextType.action
                self.texts.status = f"{volume}% <lower>"
                self.texts.text = "volume"
            case "togglemute":
                self.texts.type = ItemTextType.action
                self.texts.text = "toggle (un)mute"
                if pipewire.get_node_mute(node):
                    self.texts.status = "<volume-muted>"
                else:
                    self.texts.status = "<volume-max>"
            case "move":
                destination_node = pipewire.get_node_by_id(int(destination_str))

                match node["media.class"]:
                    case Const.Props.MediaClass.StreamInputAudio:
                        current_source = pipewire.get_current_stream_source_or_sink(
                            node["id"],
                            "source",
                        )
                        if destination_node["id"] == current_source["id"]:
                            self.texts.type = ItemTextType.notification
                            self.texts.status = "<ok>"
                            self.texts.text = (
                                f"recording from: {destination_node['description']}"
                            )
                        else:
                            self.texts.type = ItemTextType.action
                            self.texts.status = "<change>"
                            self.texts.text = (
                                f"move to input:  {destination_node['description']}"
                            )
                    case Const.Props.MediaClass.StreamOutputAudio:
                        current_sink = pipewire.get_current_stream_source_or_sink(
                            node["id"],
                            "sink",
                        )
                        if destination_node["id"] == current_sink["id"]:
                            self.texts.type = ItemTextType.notification
                            self.texts.status = "<ok>"
                            self.texts.text = (
                                f"playing on: {destination_node['description']}"
                            )
                        else:
                            self.texts.type = ItemTextType.action
                            self.texts.status = "<change>"
                            self.texts.text = (
                                f"move to:    {destination_node['description']}"
                            )

    async def execute(self) -> None:
        pipewire = await self.get_shared_data()
        if len(self.value.split(self.delimiter)) == 2:  # noqa: PLR2004
            action, node_str = self.value.split(self.delimiter)
        else:
            action, node_str, destination_str = self.value.split(self.delimiter)
        node = pipewire.get_node_by_id(int(node_str))

        self.texts.type = ItemTextType.action

        match action:
            case "setdefault":
                if not await self.is_node_default(node):
                    await pipewire.set_default(int(node_str))
            case "volume+":
                await pipewire.volume_modify(int(node_str), 5)
            case "volume-":
                await pipewire.volume_modify(int(node_str), -5)
            case "togglemute":
                await pipewire.mute_toggle(int(node_str))
            case "move":
                await pipewire.move_stream(int(node_str), int(destination_str))
