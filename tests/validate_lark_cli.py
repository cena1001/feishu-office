#!/usr/bin/env python3
"""Smoke-test feishu-office routes against the installed lark-cli release."""

from __future__ import annotations

import json
import subprocess
import sys

from validate_skill import SKILL_FILE, ValidationError, parse_routes, require, section


def main() -> int:
    """Require every routed lark Skill to exist in the installed CLI."""
    try:
        completed = subprocess.run(
            ["lark-cli", "skills", "list", "--json"],
            check=False,
            capture_output=True,
            text=True,
        )
        require(
            completed.returncode == 0,
            f"lark-cli skills list failed: {completed.stderr.strip() or completed.stdout.strip()}",
        )
        payload = json.loads(completed.stdout)
        require(payload.get("ok") is True, "lark-cli skills list did not return ok=true")
        skills = payload.get("skills")
        require(isinstance(skills, list), "lark-cli skills list returned an invalid skills array")

        routes = parse_routes(section(SKILL_FILE.read_text(encoding="utf-8"), "Routing"))
        required = {name for names in routes.values() for name in names if name.startswith("lark-")}
        required.add("lark-shared")
        available = {
            item.get("name") for item in skills if isinstance(item, dict) and item.get("name")
        }
        missing = sorted(required - available)
        require(not missing, f"installed lark-cli is missing routed Skills: {', '.join(missing)}")
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: installed lark-cli provides all {len(required)} routed official Skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
