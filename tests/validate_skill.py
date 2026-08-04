#!/usr/bin/env python3
"""Validate the public feishu-office Agent Skill package."""

from __future__ import annotations

import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "feishu-office"
SKILL_FILE = SKILL_ROOT / "SKILL.md"
OPENAI_FILE = SKILL_ROOT / "agents" / "openai.yaml"
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
    for path in (SKILL_FILE, OPENAI_FILE, STYLE_FILE, PREVIEW_FILE):
        require(path.is_file(), f"missing required file: {display_path(path)}")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the two-field YAML subset used by this Skill."""
    lines = text.splitlines()
    require(len(lines) >= 4 and lines[0] == "---", "SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValidationError("SKILL.md frontmatter is missing its closing delimiter") from exc

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, raw_value = line.partition(":")
        require(bool(separator), f"invalid frontmatter line: {line}")
        key = key.strip()
        raw_value = raw_value.strip()
        require(key not in fields, f"duplicate frontmatter field: {key}")
        if raw_value.startswith('"'):
            try:
                value = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"invalid quoted frontmatter value for {key}") from exc
        else:
            value = raw_value
        require(isinstance(value, str) and value.strip(), f"frontmatter field {key} is empty")
        fields[key] = value

    require(
        set(fields) == {"name", "description"}, "frontmatter must contain only name and description"
    )
    require(fields["name"] == "feishu-office", "frontmatter name must be feishu-office")
    require(len(fields["description"]) <= 1024, "frontmatter description is too long")
    return fields


def section(text: str, title: str) -> str:
    """Return one level-two Markdown section."""
    heading = re.search(rf"(?m)^## {re.escape(title)}[ \t]*$", text)
    require(heading is not None, f"missing section: ## {title}")
    start = heading.end()
    next_heading = re.search(r"(?m)^## ", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def parse_routes(routing: str) -> dict[str, set[str]]:
    """Read route labels and official Skill names from the routing table."""
    routes: dict[str, set[str]] = {}
    for line in routing.splitlines():
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "Request":
            continue
        routes[cells[0]] = set(re.findall(r"\blark-[a-z0-9-]+\b", " ".join(cells[1:])))
    return routes


def validate_skill() -> None:
    """Validate metadata, official routing, and core behavior guardrails."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    description = frontmatter["description"].casefold()
    for trigger in ("feishu", "chat history", "action items", "docx", "meeting", "whiteboards"):
        require(trigger in description, f"description is missing a branch trigger: {trigger}")

    routing_heading = text.index("## Routing")
    shared_command = "lark-cli skills read lark-shared --json"
    require(shared_command in text[:routing_heading], "lark-shared must be read before routing")

    expected_routes = {
        "People and directory": {"lark-contact"},
        "Chats and messages": {"lark-im"},
        "Docx or Wiki document content": {"lark-doc"},
        "Ended meeting discovery or artifacts": {"lark-vc"},
        "Minutes token, URL, or local media": {"lark-minutes"},
        "Known Note ID or resolved unified transcript": {"lark-note"},
        "Multi-meeting recap or report": {"lark-workflow-meeting-summary"},
        "Whiteboards": {"lark-whiteboard"},
    }
    routes = parse_routes(section(text, "Routing"))
    require(routes == expected_routes, "routing table does not match the supported intent map")

    chat = " ".join(section(text, "Chat Analysis").casefold().split())
    concept_groups = {
        "direct chat before cross-chat discovery": ("direct", "cross-chat", "discovery"),
        "bounded pagination and threads": ("scope", "pagination", "thread", "boundary"),
        "decision-state classification": (
            "confirmed decision",
            "proposal",
            "unresolved question",
            "action item",
        ),
        "evidence and redaction": ("sender", "time", "message id", "redact"),
    }
    for label, terms in concept_groups.items():
        require(all(term in chat for term in terms), f"Chat Analysis is missing {label}")

    commands = re.findall(r"(?m)^[ \t]*(lark-cli\s+[^\n]+)$", text)
    require(
        commands == [shared_command], "SKILL.md must contain only the shared skills-read command"
    )
    for pattern, label in {
        r"whiteboard\s+\+query\b": "stale whiteboard command",
        r"whiteboard-cli@": "pinned whiteboard-cli package",
        r"\.\./lark-": "relative lark Skill path",
        r"kai[_-]?wu": "KaiWu naming",
    }.items():
        require(re.search(pattern, text, re.IGNORECASE) is None, f"SKILL.md contains {label}")

    updates = section(text, "Updates and Failures")
    require(
        "lark-shared" in updates and "global" in updates,
        "update policy must delegate to lark-shared",
    )


def validate_openai_metadata() -> None:
    """Validate the small Codex-facing interface contract."""
    text = OPENAI_FILE.read_text(encoding="utf-8")
    for pattern, label in {
        r'^\s*display_name:\s*".+"\s*$': "quoted display_name",
        r'^\s*short_description:\s*".{25,64}"\s*$': "25-64 character short_description",
        r'^\s*default_prompt:\s*".*\$feishu-office.*"\s*$': "default_prompt using $feishu-office",
    }.items():
        require(
            re.search(pattern, text, re.MULTILINE) is not None, f"openai.yaml is missing {label}"
        )


def validate_style() -> None:
    """Validate MarlowStyle semantics without operational instructions."""
    lines = [line.casefold() for line in STYLE_FILE.read_text(encoding="utf-8").splitlines()]
    palette = {
        "canvas": "#ffffff",
        "grouping lane": "#eceef6",
        "normal node": "#ffffff",
        "border": "#2b2b2b",
        "connector": "#2b2b2b",
        "focal node": "#fbe3e5",
        "actor or trigger": "#c8564e",
        "phase chip": "#f7d9dc",
        "title highlight": "#f4e04d",
    }
    for role, color in palette.items():
        require(
            any(role in line and color in line for line in lines),
            f"MarlowStyle is missing {role} {color}",
        )
    require(
        any("main flow" in line and "solid" in line for line in lines),
        "MarlowStyle is missing solid main flow",
    )
    require(
        any("side flow" in line and "dashed" in line for line in lines),
        "MarlowStyle is missing dashed side flow",
    )

    normalized = "\n".join(lines)
    for pattern, label in {
        r"\blark-cli\b": "lark-cli instructions",
        r"\bwhiteboard-cli\b": "whiteboard-cli instructions",
        r"\b(?:oauth|authentication|authorization|scopes?)\b": "auth or scope instructions",
    }.items():
        require(re.search(pattern, normalized) is None, f"MarlowStyle contains {label}")


def validate_png_structure() -> None:
    """Check PNG signature, chunk bounds, CRCs, and required chunks."""
    data = PREVIEW_FILE.read_bytes()
    require(
        data.startswith(b"\x89PNG\r\n\x1a\n"), "MarlowStyle preview has an invalid PNG signature"
    )

    offset = 8
    chunk_types: list[bytes] = []
    while offset < len(data):
        require(offset + 12 <= len(data), "MarlowStyle PNG has a truncated chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        require(chunk_end <= len(data), "MarlowStyle PNG has a truncated payload")
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : chunk_end])[0]
        require(
            zlib.crc32(chunk_type + payload) & 0xFFFFFFFF == expected_crc,
            "MarlowStyle PNG has an invalid CRC",
        )
        chunk_types.append(chunk_type)
        offset = chunk_end

    require(chunk_types[:1] == [b"IHDR"], "MarlowStyle PNG must begin with IHDR")
    require(b"IDAT" in chunk_types, "MarlowStyle PNG is missing IDAT")
    require(chunk_types[-1:] == [b"IEND"], "MarlowStyle PNG must end with IEND")


def validate_repository_metadata() -> None:
    """Validate public documentation, attribution, and ignore rules."""
    for path in (README_FILE, LICENSE_FILE, GITIGNORE_FILE):
        require(path.is_file(), f"missing required file: {display_path(path)}")

    readme = README_FILE.read_text(encoding="utf-8")
    for requirement in (
        "https://github.com/larksuite/cli",
        "lark-cli >= 1.0.53",
        "npx @larksuite/cli@latest install",
        "npx skills add . -g",
        "npx skills add cena1001/feishu-office -g",
        "lark-cli update --check --json",
        "npx skills update feishu-office -g",
        "https://github.com/vercel-labs/skills",
        "MarlowStyle",
    ):
        require(requirement in readme, f"README.md must contain: {requirement}")
    require(
        "面向 Claude Code 和 Codex" not in readme, "README.md must not limit support to two agents"
    )
    require(
        readme.index("git pull") < readme.index("npx skills add . -g -y"),
        "local update order is invalid",
    )

    license_text = LICENSE_FILE.read_text(encoding="utf-8")
    for requirement in (
        "MIT License",
        "Copyright (c) 2026 Zara Zhang (@zarazhangrui)",
        "Copyright (c) 2026 Marlow",
        "https://github.com/zarazhangrui/beautiful-feishu-whiteboard",
        "Permission is hereby granted",
    ):
        require(requirement in license_text, f"LICENSE must contain: {requirement}")
    warranty = re.sub(r"""["'“”‘’]""", "", license_text)
    require(
        "THE SOFTWARE IS PROVIDED AS IS" in " ".join(warranty.split()).upper(),
        "LICENSE lacks MIT warranty text",
    )

    ignore_entries = {
        line.strip()
        for line in GITIGNORE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    require(
        {".DS_Store", ".env", "node_modules/", "docs/plans/"} <= ignore_entries,
        ".gitignore is incomplete",
    )


def main() -> int:
    """Run all package validations with a concise pass/fail result."""
    try:
        validate_required_files()
        validate_skill()
        validate_openai_metadata()
        validate_style()
        validate_png_structure()
        validate_repository_metadata()
    except (OSError, UnicodeError, ValueError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: feishu-office Skill package checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
