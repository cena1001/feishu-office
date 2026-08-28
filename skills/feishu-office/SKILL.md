---
name: feishu-office
description: "Use for everyday Feishu or Lark work involving people lookup; chat reading, analysis, decisions, or action items; Docx or Wiki analysis or edits; meeting artifacts; Feishu Project issues; editable whiteboards; MarlowStyle, Marlow Flow, or the user's whiteboard style."
---

# Feishu Office

Use this Skill as a thin coordinator. Treat the routed official Skills provided
by installed CLIs as the source of truth; never copy or guess business commands.

## Routing

| Request | Route |
| --- | --- |
| People and directory | `lark-contact` |
| Chats and messages | `lark-im` |
| Docx or Wiki document content | `lark-doc` |
| Ended meeting, Note, Minutes, or local media | `lark-meeting` |
| Multi-meeting recap or report | `lark-workflow-meeting-summary` |
| Feishu Project Issue or work item | Installed official `meegle` Skill; otherwise `references/feishu-project.md` |
| Whiteboards | `lark-whiteboard` |

Choose the narrowest matching row. Combine rows only for a cross-domain request
or when the selected official Skill hands off to another domain.

The meeting routes cover ended meetings, existing Note or Minutes artifacts,
and local-media conversion. Scheduling, future calendar events, and in-progress
meetings stay with their own official Skills and are not coordinated here.
Route the content of a Docx or Wiki meeting-summary document through `lark-doc`;
use `lark-meeting` for meeting metadata, transcripts, Note, Minutes, or media.

For a `lark-*` route, read each listed Skill through the CLI's `skills read`
interface. Follow its current prerequisites and read referenced official
guidance on demand through the same interface. Do not pre-read `lark-shared`
unless the selected Skill requires it or the task involves authentication,
permissions, notices, or updates. For a Project route, use the separately
installed official `meegle` Skill when available; otherwise read the local
fallback reference before deciding whether the task can continue.

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

1. Close the evidence graph for the requested scope: follow task-relevant links
   and inspect decision-relevant embedded images, whiteboards, chat attachments,
   or meeting artifacts. Record every unread branch and why.
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

Follow the current `lark-shared` guidance for `lark-cli` authentication, safety,
notices, and updates, and the official `meegle` guidance for Project auth and
safety. Treat any CLI update as a separate, explicitly confirmed global mutation.

If a required `lark-*` Skill is unavailable, stop and report the exact failed
`skills read` request. Project work follows the capability order in its fallback
reference instead of assuming browser access.
