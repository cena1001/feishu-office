#!/usr/bin/env python3
"""Validate the public feishu-office Agent Skill package."""

from __future__ import annotations

import re
import struct
import sys
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "feishu-office"
SKILL_FILE = SKILL_ROOT / "SKILL.md"
STYLE_FILE = SKILL_ROOT / "references" / "marlow-style.md"
PREVIEW_FILE = SKILL_ROOT / "assets" / "marlow-style.png"
README_FILE = ROOT / "README.md"
LICENSE_FILE = ROOT / "LICENSE"
GITIGNORE_FILE = ROOT / ".gitignore"


class ValidationError(Exception):
    """Raised when the Skill package violates a required invariant."""


def require(condition: bool, message: str) -> None:
    """Raise a readable validation error when a requirement is unmet."""
    if not condition:
        raise ValidationError(message)


def display_path(path: Path) -> str:
    """Return a stable project-relative path for diagnostics."""
    return path.relative_to(ROOT).as_posix()


def validate_required_files() -> None:
    """Require the complete minimal public Skill package."""
    required_files = (
        SKILL_FILE,
        SKILL_ROOT / "agents" / "openai.yaml",
        STYLE_FILE,
        PREVIEW_FILE,
    )
    for path in required_files:
        require(path.is_file(), f"missing required file: {display_path(path)}")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the exact two-line frontmatter format used by this Skill."""
    lines = text.splitlines()
    require(len(lines) >= 4, "SKILL.md must contain two-line YAML frontmatter")
    require(lines[0] == "---", "SKILL.md must start with an exact --- delimiter")
    require(
        lines[1] == "name: feishu-office",
        "SKILL.md frontmatter name must be exactly: name: feishu-office",
    )
    require(lines[3] == "---", "SKILL.md frontmatter must contain exactly two single-line fields")

    prefix = "description: "
    require(
        lines[2].startswith(prefix),
        "SKILL.md frontmatter description must be an unindented single-line plain string",
    )
    description = lines[2][len(prefix) :]
    require(
        bool(description) and description == description.strip(),
        "SKILL.md frontmatter description must not be empty or padded",
    )
    require(
        description.casefold() not in {"true", "false", "yes", "no", "on", "off", "null", "~"},
        "SKILL.md frontmatter description must not be a YAML boolean or null",
    )
    forbidden_characters = set("#:[]{},&*!|>'\"%@`~")
    require(
        not any(character in forbidden_characters for character in description),
        "SKILL.md frontmatter description contains YAML structure, quote, or comment characters",
    )
    require(
        not description.startswith(("-", "?")),
        "SKILL.md frontmatter description must not start with a YAML structure indicator",
    )

    return {"name": "feishu-office", "description": description}


def parse_routing_table(section: str) -> dict[str, set[str]]:
    """Parse the first Markdown table in Routing that contains route rows."""

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip()[1:-1].split("|")]

    def is_separator(row: list[str]) -> bool:
        return bool(row) and all(
            re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) is not None for cell in row
        )

    table_blocks: list[list[str]] = []
    current_block: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            current_block.append(stripped)
        elif current_block:
            table_blocks.append(current_block)
            current_block = []
    if current_block:
        table_blocks.append(current_block)

    for block in table_blocks:
        if len(block) < 3 or not is_separator(cells(block[1])):
            continue

        routes: dict[str, set[str]] = {}
        for line in block[2:]:
            row = cells(line)
            if len(row) < 2:
                continue
            label = row[0].casefold()
            if "people" in label and "chat" in label:
                category = "People/chat"
            elif re.search(r"\bdocuments?\b", label):
                category = "Documents"
            elif re.search(r"\bmeetings?\b", label):
                category = "Meetings"
            elif re.search(r"\bwhiteboards?\b", label):
                category = "Whiteboards"
            else:
                continue

            require(category not in routes, f"Routing table contains duplicate {category} rows")
            route_text = " ".join(row[1:]).casefold()
            routes[category] = set(re.findall(r"\blark-[a-z0-9-]+\b", route_text))

        if routes:
            return routes

    raise ValidationError("## Routing must contain a Markdown routing table")


def markdown_section(text: str, title: str, level: int) -> str:
    """Return one exact Markdown section, stopping at a same-or-higher heading."""
    lines = text.splitlines(keepends=True)
    section_lines: list[str] = []
    found = False
    fence_marker: str | None = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            if found:
                section_lines.append(line)
            continue

        heading = (
            None
            if fence_marker
            else re.fullmatch(
                r"(#{1,6})[ \t]+(.+?)[ \t]*",
                line.rstrip("\r\n"),
            )
        )
        if heading is not None:
            heading_level = len(heading.group(1))
            heading_title = heading.group(2)
            if not found and heading_level == level and heading_title == title:
                found = True
                continue
            if found and heading_level <= level:
                break

        if found:
            section_lines.append(line)

    require(found, f"README.md must contain the exact heading: {'#' * level} {title}")
    return "".join(section_lines)


def command_line_position(section: str, command: str, section_name: str) -> int:
    """Locate a command that occupies its own line inside one Markdown section."""
    match = re.search(rf"(?m)^[ \t]*{re.escape(command)}[ \t]*$", section)
    require(match is not None, f"{section_name} must contain this command: {command}")
    return match.start()


def validate_skill() -> None:
    """Validate metadata, official routing coverage, and stale-operation exclusions."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    require(
        set(frontmatter) == {"name", "description"},
        "SKILL.md frontmatter must contain only name and description",
    )
    routing_heading = re.search(r"(?m)^## Routing[ \t]*$", text)
    require(routing_heading is not None, "SKILL.md must contain an exact ## Routing section")
    shared_command = "lark-cli skills read lark-shared --json"
    shared_match = re.search(
        rf"(?m)^[ \t]*{re.escape(shared_command)}[ \t]*$",
        text,
    )
    require(
        shared_match is not None,
        f"SKILL.md must contain this command on its own line: {shared_command}",
    )
    require(
        shared_match.start() < routing_heading.start(),
        "SKILL.md must read lark-shared before ## Routing",
    )

    section_start = routing_heading.end()
    next_heading = re.search(r"(?m)^## ", text[section_start:])
    section_end = (
        section_start + next_heading.start() if next_heading is not None else len(text)
    )
    routes = parse_routing_table(text[section_start:section_end])
    expected_routes = {
        "People/chat": {"lark-contact", "lark-im"},
        "Documents": {"lark-doc"},
        "Meetings": {"lark-vc", "lark-minutes"},
        "Whiteboards": {"lark-whiteboard"},
    }
    for category, expected_skills in expected_routes.items():
        require(category in routes, f"Routing table is missing the {category} row")
        require(
            routes[category] == expected_skills,
            f"Routing table {category} row must map exactly to "
            f"{', '.join(sorted(expected_skills))}",
        )

    stale_patterns = {
        r"whiteboard\s+\+query\b": "whiteboard +query",
        r"whiteboard-cli@": "a pinned whiteboard-cli package",
        r"\.\./lark-": "a relative ../lark-* path",
        r"kai[_-]?wu": "a KaiWu/Kai_Wu variant",
    }
    for pattern, label in stale_patterns.items():
        require(
            re.search(pattern, text, flags=re.IGNORECASE) is None,
            f"SKILL.md must not contain {label}",
        )


def validate_style() -> None:
    """Validate MarlowStyle semantics without operational whiteboard instructions."""
    text = STYLE_FILE.read_text(encoding="utf-8")
    normalized = text.casefold()
    normalized_lines = [line.casefold() for line in text.splitlines()]

    require("marlowstyle" in normalized, "MarlowStyle reference must name the profile")

    semantic_palette = (
        ("white canvas", ("canvas",), "#ffffff", ("white",)),
        (
            "lavender-gray grouping lanes",
            ("grouping lane", "grouping lanes", "swimlane", "swimlanes"),
            "#eceef6",
            ("lavender",),
        ),
        ("white normal nodes", ("normal node", "normal nodes"), "#ffffff", ("white",)),
        (
            "graphite borders",
            ("border", "borders"),
            "#2b2b2b",
            ("graphite",),
        ),
        (
            "graphite connectors",
            ("connector", "connectors"),
            "#2b2b2b",
            ("graphite",),
        ),
        (
            "pale-pink focal node",
            ("focal node", "focal step", "special node", "special step"),
            "#fbe3e5",
            ("pale pink", "pale-pink"),
        ),
        (
            "terracotta actor or trigger",
            ("actor", "trigger"),
            "#c8564e",
            ("terracotta",),
        ),
        (
            "pale-pink phase chip",
            ("phase chip", "phase chips", "annotation chip", "annotation chips"),
            "#f7d9dc",
            ("pink",),
        ),
        (
            "maroon phase-chip text",
            ("phase chip", "phase chips", "annotation chip", "annotation chips"),
            "#9a2b2b",
            ("maroon",),
        ),
        (
            "yellow title highlight",
            ("title", "titles"),
            "#f4e04d",
            ("yellow",),
        ),
    )
    for label, roles, color_code, color_names in semantic_palette:
        require(
            any(
                any(role in line for role in roles)
                and color_code in line
                and any(color_name in line for color_name in color_names)
                for line in normalized_lines
            ),
            f"MarlowStyle reference must bind {label} to {color_code} on one line",
        )

    flow_requirements = {
        "solid main flow": (("solid",), ("main flow", "primary flow")),
        "dashed side flow": (("dashed",), ("side flow", "signal flow")),
    }
    for label, term_groups in flow_requirements.items():
        require(
            any(all(any(term in line for term in group) for group in term_groups) for line in normalized_lines),
            f"MarlowStyle reference must define {label} on one line",
        )

    operational_patterns = {
        r"\blark-cli\b": "lark-cli instructions",
        r"\bwhiteboard-cli\b": "whiteboard-cli instructions",
        (
            r"\b(?:auth|authn|authz|authenticat(?:e|ed|es|ing|ion)|"
            r"authoriz(?:e|ed|es|ing|ation)|oauth(?:2(?:\.0)?)?)\b"
        ): "authentication instructions",
        r"\bscopes?\b": "scope instructions",
        r"\brenderer[- ]version\b": "renderer-version instructions",
    }
    for pattern, label in operational_patterns.items():
        require(
            re.search(pattern, normalized) is None,
            f"MarlowStyle reference must not contain {label}",
        )


def validate_png_structure() -> None:
    """Check basic PNG structural sanity without implementing a PNG decoder."""
    data = PREVIEW_FILE.read_bytes()
    signature = b"\x89PNG\r\n\x1a\n"
    require(len(data) > len(signature), "MarlowStyle PNG must be non-empty")
    require(data.startswith(signature), "MarlowStyle preview must have a PNG signature")

    offset = len(signature)
    chunk_index = 0
    seen_ihdr = False
    seen_iend = False
    idat_bytes = 0

    while offset < len(data):
        require(offset + 12 <= len(data), "MarlowStyle PNG has a truncated chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        require(chunk_end <= len(data), "MarlowStyle PNG has a truncated chunk payload")

        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : chunk_end])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        require(actual_crc == expected_crc, "MarlowStyle PNG has an invalid chunk CRC")

        if chunk_index == 0:
            require(chunk_type == b"IHDR", "MarlowStyle PNG must begin with IHDR")
        if chunk_type == b"IHDR":
            require(not seen_ihdr, "MarlowStyle PNG must contain exactly one IHDR")
            require(length == 13, "MarlowStyle PNG has an invalid IHDR")
            width, height = struct.unpack(">II", payload[:8])
            require(width > 0 and height > 0, "MarlowStyle PNG dimensions must be positive")
            seen_ihdr = True
        elif chunk_type == b"IDAT":
            idat_bytes += length
        elif chunk_type == b"IEND":
            require(length == 0, "MarlowStyle PNG has an invalid IEND")
            require(chunk_end == len(data), "MarlowStyle PNG must not contain data after IEND")
            seen_iend = True

        offset = chunk_end
        chunk_index += 1

    require(seen_ihdr, "MarlowStyle PNG is missing IHDR")
    require(idat_bytes > 0, "MarlowStyle PNG must contain non-empty IDAT data")
    require(seen_iend, "MarlowStyle PNG is missing IEND")


def validate_repository_metadata() -> None:
    """Validate the minimal public repository documentation and ignore rules."""
    required_files = (README_FILE, LICENSE_FILE, GITIGNORE_FILE)
    for path in required_files:
        require(
            path.is_file(),
            f"missing required repository file: {display_path(path)}",
        )

    readme = README_FILE.read_text(encoding="utf-8")
    readme_requirements = (
        "https://github.com/larksuite/cli",
        "npx @larksuite/cli@latest install",
        "lark-cli update --check --json",
        "MarlowStyle",
        "git pull",
        "npx skills add . -g -y",
        "npx skills update feishu-office -g",
        "https://github.com/vercel-labs/skills",
        "支持的 AI Agent",
    )
    for requirement in readme_requirements:
        require(requirement in readme, f"README.md must contain: {requirement}")
    require(
        "面向 Claude Code 和 Codex" not in readme,
        "README.md must not present the Skill as Claude Code and Codex only",
    )

    update_section = markdown_section(readme, "更新", 2)
    local_section = markdown_section(update_section, "本地克隆安装", 3)
    github_section = markdown_section(update_section, "GitHub 来源安装", 3)
    git_pull_position = command_line_position(local_section, "git pull", "### 本地克隆安装")
    local_sync_position = command_line_position(
        local_section,
        "npx skills add . -g -y",
        "### 本地克隆安装",
    )
    require(
        git_pull_position < local_sync_position,
        "### 本地克隆安装 must run git pull before npx skills add . -g -y",
    )
    command_line_position(
        github_section,
        "npx skills update feishu-office -g",
        "### GitHub 来源安装",
    )

    license_text = LICENSE_FILE.read_text(encoding="utf-8")
    for requirement in (
        "MIT License",
        "https://github.com/zarazhangrui/beautiful-feishu-whiteboard",
        "Permission is hereby granted",
    ):
        require(requirement in license_text, f"LICENSE must contain: {requirement}")
    copyright_lines = (
        "Copyright (c) 2026 Zara Zhang (@zarazhangrui)",
        "Copyright (c) 2026 Marlow",
    )
    for copyright_line in copyright_lines:
        require(
            re.search(rf"(?m)^{re.escape(copyright_line)}$", license_text) is not None,
            f"LICENSE must contain this exact line: {copyright_line}",
        )
    require(
        re.search(
            r"(?i)derived\s+from\s+beautiful-feishu-whiteboard",
            license_text,
        )
        is not None,
        "LICENSE must identify beautiful-feishu-whiteboard as the derivation source",
    )
    normalized_warranty = re.sub(r"""["'“”‘’]""", "", license_text)
    normalized_warranty = " ".join(normalized_warranty.split()).upper()
    require(
        "THE SOFTWARE IS PROVIDED AS IS" in normalized_warranty,
        'LICENSE must contain the MIT "THE SOFTWARE IS PROVIDED AS IS" disclaimer',
    )

    ignore_entries = {
        line.strip()
        for line in GITIGNORE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for requirement in (".DS_Store", ".env", "node_modules/", "docs/plans/"):
        require(requirement in ignore_entries, f".gitignore must contain: {requirement}")


def main() -> int:
    """Run all package validations with a concise pass/fail result."""
    try:
        validate_required_files()
        validate_skill()
        validate_style()
        validate_png_structure()
        validate_repository_metadata()
    except (OSError, UnicodeError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: feishu-office Skill package checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
