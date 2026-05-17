---
name: obsidian-notion-sync
description: Sync missing Obsidian 50_Output daily markdown pages to Notion US Dream hierarchy and update 유형별_인덱스 links. Use when user asks to upload/backfill/sync Obsidian daily outputs into Notion while preserving structure and avoiding duplicates.
---

# Obsidian Notion Sync

Use this skill to mirror Obsidian daily outputs into Notion `US Dream`.

## Inputs
- Vault path (default): `/Users/eunhwa/Obsidian/myVault`
- Output root (default): `<vault>/50_Output`
- Target root page (default): `US Dream` page ID `30b8a121-8433-80ce-9384-c6390edec047`
- Notion token: `NOTION_TOKEN` (only for fallback script mode)

## Behavior
1. Scan `50_Output/<iso-week>/<date>/*.md`.
2. Ensure Notion hierarchy exists under `US Dream`: week page -> date page -> doc pages.
3. Create missing pages idempotently.
4. Render markdown into Notion blocks for doc pages:
   - Strip YAML frontmatter automatically.
   - Normalize Obsidian code fences like ```` ```id="..." ```` / ```` ```java id="..." ````.
   - Convert Obsidian callout markers (`[!Note]`, `>[!Note]`) into Notion `callout` blocks with emoji icon.
5. Update `유형별_인덱스` sub-pages (`*_모음`) with missing date links.
6. Optional: refresh existing doc page content in-place (clear + re-render) with `--replace-existing-doc-content`.

## Execution Mode
Use **MCP-first** by default:
- Obsidian read/scan: `obsidian` MCP tools
- Notion create/update/fetch: `notion` MCP tools
- Keep idempotency: create only missing pages, update only missing index links
- For full refresh requests, use page-level content replacement on existing docs

Fallback to script mode only when MCP is unavailable or explicitly requested.

## Fallback Command
```bash
python3 /Users/eunhwa/.codex/skills/obsidian-notion-sync/scripts/sync_obsidian_to_notion.py
```

## Fallback Typical Usage
```bash
export NOTION_TOKEN='secret_xxx'
python3 /Users/eunhwa/.codex/skills/obsidian-notion-sync/scripts/sync_obsidian_to_notion.py --dry-run --verbose
python3 /Users/eunhwa/.codex/skills/obsidian-notion-sync/scripts/sync_obsidian_to_notion.py --week 2026-W08
python3 /Users/eunhwa/.codex/skills/obsidian-notion-sync/scripts/sync_obsidian_to_notion.py --from-date 2026-02-19 --to-date 2026-02-20
python3 /Users/eunhwa/.codex/skills/obsidian-notion-sync/scripts/sync_obsidian_to_notion.py --week 2026-W08 --replace-existing-doc-content
```

## Options
- `--skip-index`: skip `유형별_인덱스` updates
- `--us-dream-page-id <page-id>`: use a different Notion root page
- `--output-root <path>`: use a different output folder
- `--replace-existing-doc-content`: re-sync content for existing doc pages too (destructive to existing page blocks)
