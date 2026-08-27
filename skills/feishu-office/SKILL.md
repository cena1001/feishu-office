---
name: feishu-office
description: "Use when Feishu or Lark work involves people lookup, chat analysis for decisions or action items, Docx or Wiki document edits, ended-meeting artifacts or Minutes, editable whiteboards, MarlowStyle, Marlow Flow, or the user's whiteboard style."
---

# Feishu Office

Use this Skill as a thin coordinator. Treat the embedded Skills in the running
CLI as the source of truth; never copy or guess business commands.

## Routing

| Request | Read these embedded Skills |
| --- | --- |
| People and directory | `lark-contact` |
| Chats and messages | `lark-im` |
| Docx or Wiki document content | `lark-doc` |
| Ended meeting, Note, Minutes, or local media | `lark-meeting` |
| Multi-meeting recap or report | `lark-workflow-meeting-summary` |
| Whiteboards | `lark-whiteboard` |

Choose the narrowest matching row. Combine rows only for a cross-domain request
or when the selected official Skill hands off to another domain.

The meeting routes cover ended meetings, existing Note or Minutes artifacts,
and local-media conversion. Scheduling, future calendar events, and in-progress
meetings stay with their own official Skills and are not coordinated here.

After selecting a route, read each listed Skill through the CLI's `skills read`
interface. Follow its current prerequisites and read any referenced official
guidance on demand through the same interface. Do not pre-read `lark-shared`
unless the selected Skill requires it or the task involves authentication,
permissions, notices, or updates.

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
3. Before editing an existing cloud document after a non-trivial read or draft
   gap, read the target again and account for concurrent changes. Follow the
   current `lark-doc` block-level workflow; preserve unrelated content and
   structured blocks such as mentions and whiteboards instead of flattening them.
4. Follow the current official risk guidance for every write. Preview or confirm
   risky or ambiguous writes, then read back changed and protected blocks when
   required by that guidance.
5. Return the synthesized result and distinguish completed writes, drafts, and
   incomplete branches.

For a whiteboard, load `references/marlow-style.md` only when the user explicitly
names MarlowStyle, Marlow Flow, or asks for “my style”. Deliver an editable native
whiteboard by default; use a static image only as a preview or verification
artifact. The bundled `assets/marlow-style.png` is its visual preview.

## Updates and Failures

Follow the current `lark-shared` guidance for authentication, safety, notices,
and updates. Treat a CLI update as a separate, explicitly confirmed global
mutation.

If the CLI or any required embedded guidance is unavailable, stop and report the
exact failed `skills read` command. Resume only when current official guidance is
available.
