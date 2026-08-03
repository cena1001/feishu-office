---
name: feishu-office
description: Use when Feishu/Lark requests involve chat analysis document edits ended meeting artifacts editable whiteboards MarlowStyle or my style
---

# Feishu Office

Use this Skill as a thin coordinator. Treat the embedded Skills in the running
CLI as the source of truth; never copy or guess business commands.

Read the shared setup and safety guidance first:

lark-cli skills read lark-shared --json

## Routing

| Request | Read these embedded Skills |
| --- | --- |
| People and chat | `lark-contact`, `lark-im` |
| Documents | `lark-doc` |
| Meeting artifacts | `lark-vc`, `lark-minutes` |
| Whiteboards | `lark-whiteboard` |

The meeting-artifacts route covers artifacts and minutes from ended meetings
only. Scheduling, future calendar events, and in-progress meetings are outside
this route. When needed, discover and hand them to the corresponding current
official embedded Skill; do not add commands for them here.

After selecting a route, read each listed Skill with
`lark-cli skills read <skill> --json`. If its current instructions point to an
official reference, read that reference on demand through the same `skills read`
interface and follow the exact path it provides.

## Workflow

1. Read the required source material before analysis or drafting.
2. For a multi-domain request, complete upstream reads and analysis before any
   downstream write.
3. Follow the current official risk guidance for every write. Preview or confirm
   risky or ambiguous writes, and verify by reading back only when that guidance
   requires it.
4. Return the synthesized result and distinguish completed writes from drafts.

For a whiteboard, load `references/marlow-style.md` only when the user explicitly
names MarlowStyle or asks for “my style”. The bundled
`assets/marlow-style.png` is its visual preview.

## Updates and Failures

Check for an update only when the user asks or the CLI displays an update notice:

lark-cli update --check --json

Treat the check as read-only. If an update is available, describe it and obtain
explicit confirmation immediately before running:

lark-cli update

Run the update only after that confirmation.

If the CLI or any required embedded guidance is unavailable, stop and report the
exact failed `skills read` command. Do not fall back to remembered, copied, or
locally reconstructed business commands.
