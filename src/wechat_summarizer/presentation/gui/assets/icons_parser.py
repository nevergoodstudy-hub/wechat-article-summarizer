"""SVG path parser used by the GUI icon renderer."""

from __future__ import annotations

import re


class SVGPathParser:
    """SVG路径解析器"""

    COMMAND_PATTERN = re.compile(r"([MLHVCSQTAZmlhvcsqtaz])([^MLHVCSQTAZmlhvcsqtaz]*)")
    NUMBER_PATTERN = re.compile(r"-?\d+\.?\d*(?:e[+-]?\d+)?")

    @classmethod
    def parse(
        cls, path_data: str, scale: float = 1.0, offset_x: float = 0, offset_y: float = 0
    ) -> list[tuple]:
        """解析SVG路径数据"""
        commands: list[tuple] = []
        current_x, current_y = 0.0, 0.0
        start_x, start_y = 0.0, 0.0

        for match in cls.COMMAND_PATTERN.finditer(path_data):
            cmd = match.group(1)
            args = [float(n) for n in cls.NUMBER_PATTERN.findall(match.group(2))]
            is_relative = cmd.islower()
            cmd_upper = cmd.upper()

            if cmd_upper == "M":
                current_x, current_y, start_x, start_y = cls._append_move_commands(
                    commands, args, is_relative, current_x, current_y, scale, offset_x, offset_y
                )
            elif cmd_upper == "L":
                current_x, current_y = cls._append_line_commands(
                    commands, args, is_relative, current_x, current_y, scale, offset_x, offset_y
                )
            elif cmd_upper == "H":
                current_x = cls._append_horizontal_commands(
                    commands, args, is_relative, current_x, current_y, scale, offset_x, offset_y
                )
            elif cmd_upper == "V":
                current_y = cls._append_vertical_commands(
                    commands, args, is_relative, current_x, current_y, scale, offset_x, offset_y
                )
            elif cmd_upper == "C":
                current_x, current_y = cls._append_curve_commands(
                    commands, args, is_relative, current_x, current_y, scale, offset_x, offset_y
                )
            elif cmd_upper == "S":
                current_x, current_y = cls._append_smooth_curve_commands(
                    commands, args, is_relative, current_x, current_y, scale, offset_x, offset_y
                )
            elif cmd_upper == "Q":
                current_x, current_y = cls._append_quad_commands(
                    commands, args, is_relative, current_x, current_y, scale, offset_x, offset_y
                )
            elif cmd_upper == "Z":
                current_x, current_y = start_x, start_y
                commands.append(
                    ("close", [(start_x * scale + offset_x, start_y * scale + offset_y)])
                )

        return commands

    @staticmethod
    def _append_move_commands(
        commands: list[tuple],
        args: list[float],
        is_relative: bool,
        current_x: float,
        current_y: float,
        scale: float,
        offset_x: float,
        offset_y: float,
    ) -> tuple[float, float, float, float]:
        start_x, start_y = current_x, current_y
        index = 0
        while index < len(args) - 1:
            x, y = args[index], args[index + 1]
            if is_relative:
                x += current_x
                y += current_y
            current_x, current_y = x, y
            if index == 0:
                start_x, start_y = x, y
                commands.append(("move", [(x * scale + offset_x, y * scale + offset_y)]))
            else:
                commands.append(("line", [(x * scale + offset_x, y * scale + offset_y)]))
            index += 2
        return current_x, current_y, start_x, start_y

    @staticmethod
    def _append_line_commands(
        commands: list[tuple],
        args: list[float],
        is_relative: bool,
        current_x: float,
        current_y: float,
        scale: float,
        offset_x: float,
        offset_y: float,
    ) -> tuple[float, float]:
        index = 0
        while index < len(args) - 1:
            x, y = args[index], args[index + 1]
            if is_relative:
                x += current_x
                y += current_y
            current_x, current_y = x, y
            commands.append(("line", [(x * scale + offset_x, y * scale + offset_y)]))
            index += 2
        return current_x, current_y

    @staticmethod
    def _append_horizontal_commands(
        commands: list[tuple],
        args: list[float],
        is_relative: bool,
        current_x: float,
        current_y: float,
        scale: float,
        offset_x: float,
        offset_y: float,
    ) -> float:
        for x in args:
            if is_relative:
                x += current_x
            current_x = x
            commands.append(("line", [(x * scale + offset_x, current_y * scale + offset_y)]))
        return current_x

    @staticmethod
    def _append_vertical_commands(
        commands: list[tuple],
        args: list[float],
        is_relative: bool,
        current_x: float,
        current_y: float,
        scale: float,
        offset_x: float,
        offset_y: float,
    ) -> float:
        for y in args:
            if is_relative:
                y += current_y
            current_y = y
            commands.append(("line", [(current_x * scale + offset_x, y * scale + offset_y)]))
        return current_y

    @staticmethod
    def _append_curve_commands(
        commands: list[tuple],
        args: list[float],
        is_relative: bool,
        current_x: float,
        current_y: float,
        scale: float,
        offset_x: float,
        offset_y: float,
    ) -> tuple[float, float]:
        index = 0
        while index < len(args) - 5:
            x1, y1, x2, y2, x, y = args[index : index + 6]
            if is_relative:
                x1, y1, x2, y2, x, y = (
                    x1 + current_x,
                    y1 + current_y,
                    x2 + current_x,
                    y2 + current_y,
                    x + current_x,
                    y + current_y,
                )
            current_x, current_y = x, y
            commands.append(
                (
                    "curve",
                    [
                        (x1 * scale + offset_x, y1 * scale + offset_y),
                        (x2 * scale + offset_x, y2 * scale + offset_y),
                        (x * scale + offset_x, y * scale + offset_y),
                    ],
                )
            )
            index += 6
        return current_x, current_y

    @staticmethod
    def _append_smooth_curve_commands(
        commands: list[tuple],
        args: list[float],
        is_relative: bool,
        current_x: float,
        current_y: float,
        scale: float,
        offset_x: float,
        offset_y: float,
    ) -> tuple[float, float]:
        index = 0
        while index < len(args) - 3:
            x2, y2, x, y = args[index : index + 4]
            if is_relative:
                x2 += current_x
                y2 += current_y
                x += current_x
                y += current_y
            x1, y1 = current_x, current_y
            current_x, current_y = x, y
            commands.append(
                (
                    "curve",
                    [
                        (x1 * scale + offset_x, y1 * scale + offset_y),
                        (x2 * scale + offset_x, y2 * scale + offset_y),
                        (x * scale + offset_x, y * scale + offset_y),
                    ],
                )
            )
            index += 4
        return current_x, current_y

    @staticmethod
    def _append_quad_commands(
        commands: list[tuple],
        args: list[float],
        is_relative: bool,
        current_x: float,
        current_y: float,
        scale: float,
        offset_x: float,
        offset_y: float,
    ) -> tuple[float, float]:
        index = 0
        while index < len(args) - 3:
            x1, y1, x, y = args[index : index + 4]
            if is_relative:
                x1 += current_x
                y1 += current_y
                x += current_x
                y += current_y
            current_x, current_y = x, y
            commands.append(
                (
                    "quad",
                    [
                        (x1 * scale + offset_x, y1 * scale + offset_y),
                        (x * scale + offset_x, y * scale + offset_y),
                    ],
                )
            )
            index += 4
        return current_x, current_y


__all__ = ["SVGPathParser"]
