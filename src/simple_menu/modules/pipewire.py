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
import dataclasses
import json
import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)

MAX_VOLUME = 100.0
MIN_VOLUME = 0.0


@dataclasses.dataclass
class PipewireNodeData:
    id: int


class Const:
    class PipeWire:
        class Interface:
            Device = "PipeWire:Interface:Device"
            Metadata = "PipeWire:Interface:Metadata"
            Node = "PipeWire:Interface:Node"
            # client = "PipeWire:Interface:Client"
            # core = "PipeWire:Interface:Core"
            # factory = "PipeWire:Interface:Factory"
            Link = "PipeWire:Interface:Link"
            # module = "PipeWire:Interface:Module"
            Port = "PipeWire:Interface:Port"
            # profiler = "PipeWire:Interface:Profiler"

    class Props:
        class MediaClass:
            AudioDevice = "Audio/Device"
            AudioSink = "Audio/Sink"
            AudioSource = "Audio/Source"
            MidiBridge = "Midi/Bridge"
            StreamInputAudio = "Stream/Input/Audio"
            StreamOutputAudio = "Stream/Output/Audio"
            VideoDevice = "Video/Device"
            VideoSource = "Video/Source"


class Pipewire:
    def __init__(self) -> None:
        self.pwdump: list[dict[str, Any]] = []
        self.nodes: list[dict[str, Any]] = []

    async def build(self) -> None:
        # Sometimes pw-dump returns an invalid json, that is, more than list at
        # root level. Usually happens if running pw-dump after some
        # modification has been made. Try again until succeed.
        for _ in range(10):
            try:
                pwdump_process = await asyncio.create_subprocess_exec(
                    "pw-dump",
                    "--no-colors",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                self.pwdump_json = (await pwdump_process.stdout.read()).decode("utf-8")  # type:ignore[union-attr]
                self.pwdump = json.loads(self.pwdump_json)
            except:  # noqa: E722, PERF203, S112
                continue
            else:
                break
        self.nodes = [
            node
            for node in self.pwdump
            if node["type"]
            in {
                Const.PipeWire.Interface.Device,
                Const.PipeWire.Interface.Metadata,
                Const.PipeWire.Interface.Node,
                Const.PipeWire.Interface.Link,
                Const.PipeWire.Interface.Port,
            }
        ]

    @property
    def devices(self) -> list[dict[str, Any]]:
        return [
            {
                "id": node["id"],
                "type": node["type"],
                "media.class": node["info"]["props"]["media.class"],
                "description": node["info"]["props"].get("device.description", ""),
                "form-factor": node["info"]["props"].get("device.form-factor", ""),
                "profile": {
                    k: v
                    for k, v in node["info"]["params"]["Profile"][0].items()
                    if k != "classes"
                },
                "profiles": [
                    {k: v for k, v in profile.items() if k != "classes"}
                    for profile in node["info"]["params"]["EnumProfile"]
                ],
                "route": {
                    k: v
                    for k, v in node["info"]["params"]["Route"][0].items()
                    if k
                    not in {
                        "device",
                        "devices",
                        "info",
                        "profile",
                        "profiles",
                        "props",
                        "save",
                    }
                },
                "routes": [
                    {
                        k: v
                        for k, v in profile.items()
                        if k not in {"info", "profiles", "devices"}
                    }
                    for profile in node["info"]["params"]["EnumRoute"]
                ],
            }
            for node in self.nodes
            if node["type"] == Const.PipeWire.Interface.Device
            and node["info"]["props"]["media.class"]
            == Const.Props.MediaClass.AudioDevice
        ]

    @property
    def sinks(self) -> list[dict[str, Any]]:
        return [
            node
            for node in self.sinks_sources
            if node["media.class"] == Const.Props.MediaClass.AudioSink
        ]

    @property
    def sources(self) -> list[dict[str, Any]]:
        return [
            node
            for node in self.sinks_sources
            if node["media.class"] == Const.Props.MediaClass.AudioSource
        ]

    @property
    def sinks_sources(self) -> list[dict[str, Any]]:
        return [
            {
                "id": node["id"],
                "type": node["type"],
                "media.class": node["info"]["props"]["media.class"],
                "object.serial": node["info"]["props"]["object.serial"],
                "state": node["info"]["state"],
                "device.id": node["info"]["props"].get("device.id", ""),
                "device.profile.description": node["info"]["props"].get(
                    "device.profile.description",
                    "",
                ),
                "node.name": node["info"]["props"]["node.name"],
                "description": node["info"]["props"]["node.description"],
                "volume": node["info"]["params"]["Props"][0]["channelVolumes"],
                "mute": node["info"]["params"]["Props"][0]["mute"],
            }
            for node in self.nodes
            if node["type"] == Const.PipeWire.Interface.Node
            and node["info"]["props"].get("media.class", "")
            in {
                Const.Props.MediaClass.AudioSink,
                Const.Props.MediaClass.AudioSource,
            }
        ]

    @property
    def streams(self) -> list[dict[str, Any]]:
        return [
            {
                "id": node["id"],
                "type": node["type"],
                "media.class": node["info"]["props"]["media.class"],
                "object.serial": node["info"]["props"]["object.serial"],
                "state": node["info"]["state"],
                "media.name": node["info"]["props"]["media.name"],
                "application.name": node["info"]["props"].get("application.name", ""),
                "node.name": node["info"]["props"].get("node.name"),
                "stream.is-live": node["info"]["props"]["stream.is-live"],
                "volume": node["info"]["params"]["Props"][0]["channelVolumes"],
                "mute": node["info"]["params"]["Props"][0]["mute"],
                "target.object": node["info"]["props"].get("target.object", ""),
            }
            # node
            for node in self.nodes
            if node["type"] == Const.PipeWire.Interface.Node
            and node["info"]["props"].get("media.class", "")
            in {
                Const.Props.MediaClass.StreamInputAudio,
                Const.Props.MediaClass.StreamOutputAudio,
            }
            and node["info"]["props"]["media.name"]
            not in {
                "Peak detect",  # Pavucontrol
            }
        ]

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            subnode["key"]: subnode["value"]["name"]
            for node in self.nodes
            if node["type"] == Const.PipeWire.Interface.Metadata
            and node["props"]["metadata.name"] == "default"
            for subnode in node["metadata"]
            if subnode["key"]
            in {
                "default.audio.sink",
                "default.audio.source",
                "default.configured.audio.sink",
                "default.configured.audio.source",
            }
        }

    @property
    def default_sink(self) -> dict[str, Any]:
        return next(
            node
            for node in self.sinks_sources
            if node["node.name"] == self.metadata["default.audio.sink"]
        )

    @property
    def default_source(self) -> dict[str, Any]:
        return next(
            node
            for node in self.sinks_sources
            if node["node.name"] == self.metadata["default.audio.source"]
        )

    def get_node_volume(self, node: dict[str, Any]) -> int:
        return int(100 * node["volume"][0] ** (1 / 3))

    def get_node_mute(self, node: dict[str, Any]) -> bool:
        return node["mute"]  # type:ignore[no-any-return]

    def get_node_by_id(self, nodeid: int) -> dict[str, Any]:
        raw_node = next(node for node in self.nodes if node["id"] == nodeid)
        match raw_node["info"]["props"]["media.class"]:
            case Const.Props.MediaClass.AudioDevice:
                nodes_list = self.devices
            case Const.Props.MediaClass.AudioSink:
                nodes_list = self.sinks_sources
            case Const.Props.MediaClass.AudioSource:
                nodes_list = self.sinks_sources
            case Const.Props.MediaClass.StreamInputAudio:
                nodes_list = self.streams
            case Const.Props.MediaClass.StreamOutputAudio:
                nodes_list = self.streams
        return next(node for node in nodes_list if node["id"] == nodeid)

    def get_current_stream_source_or_sink(
        self,
        stream_id: int,
        sink_source: Literal["sink", "source"],
    ) -> dict[str, Any]:
        """Return the source or sink where the stream is playing or recording from."""
        port = next(
            node
            for node in self.nodes
            if node["type"] == Const.PipeWire.Interface.Port
            and node["info"]["props"]["node.id"] == stream_id
            and node["info"]["props"]["port.direction"]
            == {
                "sink": "out",
                "source": "in",
            }[sink_source]
        )

        link_key_name = {
            "sink": "output-port-id",
            "source": "input-port-id",
        }[sink_source]
        link2_key_name = {
            "sink": "link.input.node",
            "source": "link.output.node",
        }[sink_source]

        sink_source_nodes = {"sink": self.sinks, "source": self.sources}[sink_source]

        link = next(
            node
            for node in self.nodes
            if node["type"] == Const.PipeWire.Interface.Link
            and node["info"][link_key_name] == port["id"]
            and node["info"]["props"][link2_key_name]
            in {node["id"] for node in sink_source_nodes}
        )

        if sink_source == "sink":
            nodes_list = self.sinks
        else:
            nodes_list = self.sources
        source_sink_key_name = {
            "source": "output-node-id",
            "sink": "input-node-id",
        }[sink_source]
        return next(
            node
            for node in nodes_list
            if node["id"] == link["info"][source_sink_key_name]
        )

    async def dump(self) -> None:
        print(
            json.dumps(
                [
                    *self.devices,
                    *self.sinks,
                    *self.sources,
                    *self.streams,
                ],
            ),
        )

    async def set_default(self, node_id: int) -> None:
        args = [
            "wpctl",
            "set-default",
            str(node_id),
        ]
        logger.info("Execute '%s'.", args)
        proc = await asyncio.create_subprocess_exec(*args)
        await proc.wait()

    async def set_device_profile(self, device_id: int, profile_id: int) -> None:
        args = [
            "pw-cli",
            "set-param",
            str(device_id),
            "Profile",
            f"{{ index = {profile_id} }}",
        ]
        logger.info("Execute '%s'.", args)
        proc = await asyncio.create_subprocess_exec(*args)
        await proc.wait()

        # Pavucontrol sometimes does not update its values when using wpctl to
        # change profile.
        # await asyncio.create_subprocess_exec(
        #     "wpctl",
        #     "set-profile",
        #     str(device_id),
        #     str(profile_id),
        # )

    async def set_device_route(self, device_id: int, route_id: int) -> None:
        # await asyncio.create_subprocess_exec(
        #     "pw-cli",
        #     "set-param",
        #     str(device_id),
        #     "Route",
        #     f"{{ index = {route_id} }}",
        # )
        args = [
            "wpctl",
            "set-route",
            str(device_id),
            str(route_id),
        ]
        logger.info("Execute '%s'.", args)
        proc = await asyncio.create_subprocess_exec(*args)
        await proc.wait()

    async def mute_toggle(self, node_id: int) -> None:
        args = [
            "wpctl",
            "set-mute",
            str(node_id),
            "toggle",
        ]
        logger.info("Execute '%s'.", args)
        proc = await asyncio.create_subprocess_exec(*args)
        await proc.wait()

    async def volume_modify(self, node_id: int, value: int) -> None:
        if value >= 0:
            string = f"{value}%+"
        else:
            string = f"{value * -1}%-"
        args = [
            "wpctl",
            "set-volume",
            str(node_id),
            string,
        ]
        logger.info("Execute '%s'.", args)
        proc = await asyncio.create_subprocess_exec(*args)
        await proc.wait()

    async def move_stream(self, stream_id: int, destination_id: int) -> None:
        stream_data = self.get_node_by_id(stream_id)
        destination_data = self.get_node_by_id(destination_id)
        match stream_data["media.class"]:
            case Const.Props.MediaClass.StreamInputAudio:
                command = "move-source-output"
            case Const.Props.MediaClass.StreamOutputAudio:
                command = "move-sink-input"

        args = [
            "pactl",
            command,
            str(stream_data["object.serial"]),
            str(destination_data["object.serial"]),
        ]
        logger.info("Execute '%s'.", args)
        proc = await asyncio.create_subprocess_exec(*args)
        await proc.wait()


async def main() -> None:
    pipewire = Pipewire()
    await pipewire.build()
    await pipewire.dump()


if __name__ == "__main__":
    asyncio.run(main())
