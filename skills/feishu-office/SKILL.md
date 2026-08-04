---
name: feishu-office
description: "Use when Feishu or Lark work involves resolving people, analyzing chat history for decisions or action items, working with Docx or Wiki documents, reviewing ended-meeting artifacts or Minutes, editing whiteboards, or applying MarlowStyle."
---

# Feishu Office

Use this Skill as a thin coordinator. Treat the embedded Skills in the running
CLI as the source of truth; never copy or guess business commands.

Read the shared setup and safety guidance first:

lark-cli skills read lark-shared --json

## Routing

| Request | Read these embedded Skills |
| --- | --- |
| People and directory | `lark-contact` |
| Chats and messages | `lark-im` |
| Docx or Wiki document content | `lark-doc` |
| Ended meeting discovery or artifacts | `lark-vc` |
| Minutes token, URL, or local media | `lark-minutes` |
| Known Note ID or resolved unified transcript | `lark-note` |
| Multi-meeting recap or report | `lark-workflow-meeting-summary` |
| Whiteboards | `lark-whiteboard` |

Choose the narrowest matching row. Combine rows only for a cross-domain request
or when the selected official Skill hands off to another domain.

The meeting routes cover ended meetings, existing Note or Minutes artifacts,
and local-media conversion. Scheduling, future calendar events, and in-progress
meetings stay with their own official Skills and are not coordinated here.

After selecting a route, read each listed Skill with
`lark-cli skills read <skill> --json`. If its current instructions point to an
official reference, read that reference on demand through the same `skills read`
interface and follow the exact path it provides.

Read `lark-contact` in addition to `lark-im` only when person resolution or
directory data is required.

## Chat Analysis

- Use `lark-cli` as the primary execution surface. For a named or known chat,
  resolve the target and read it directly; reserve cross-chat message search for
  discovery. A global-search permission failure is not evidence that direct chat
  history is unavailable; try the direct route and report its own result.
- Bound retrieval by chat, time, people, or topic. If the scope is ambiguous,
  use the smallest useful boundary and state it. Follow current IM pagination and
  thread guidance until that scope is complete; otherwise disclose the boundary.
- Inspect surrounding messages and relevant thread replies. Classify each item
  as a confirmed decision, proposal, unresolved question, or action item.
- Support important claims with sender, time, message ID, and an available link.
  Keep excerpts limited to the necessary evidence, and redact credentials and
  tokens by default.

## Workflow

1. Complete the required reads for the selected scope, or record the exact
   boundary before analysis or drafting.
2. For a multi-domain request, finish every upstream read and analysis step
   before any downstream write.
3. Follow the current official risk guidance for every write. Preview or confirm
   risky or ambiguous writes, and verify by reading back only when that guidance
   requires it.
4. Return the synthesized result and distinguish completed writes, drafts, and
   incomplete branches.

For a whiteboard, load `references/marlow-style.md` only when the user explicitly
names MarlowStyle or asks for “my style”. The bundled
`assets/marlow-style.png` is its visual preview.

## Updates and Failures

Follow the current `lark-shared` guidance for authentication, safety, notices,
and updates. Treat a CLI update as a separate, explicitly confirmed global
mutation.

If the CLI or any required embedded guidance is unavailable, stop and report the
exact failed `skills read` command. Resume only when current official guidance is
available.
