#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib import error, parse, request

DEFAULT_VAULT = Path("/Users/eunhwa/Obsidian/myVault")
DEFAULT_OUTPUT_SUBDIR = "50_Output"
DEFAULT_US_DREAM_PAGE_ID = "30b8a121-8433-80ce-9384-c6390edec047"
DEFAULT_NOTION_VERSION = "2022-06-28"

INDEX_ROOT_TITLE = "유형별_인덱스"
INDEX_PAGE_BY_ARTIFACT = {
    "LC_인터뷰메모": "LC_인터뷰메모_모음",
    "사이드로그": "사이드로그_모음",
    "영어면접_세션": "영어면접_세션_모음",
    "STAR_스토리": "STAR_스토리_모음",
    "시스템디자인_설계": "시스템디자인_설계_모음",
    "현업_정리_Resume": "현업_정리_Resume_모음",
}

WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n?", re.S)
OBSIDIAN_CALLOUT_RE = re.compile(r"^\s*>?\s*\[!([A-Za-z0-9_+\-]+)\]\s*$")

CALLOUT_ICON_BY_KIND = {
    "note": "📝",
    "tip": "💡",
    "info": "ℹ️",
    "warning": "⚠️",
    "caution": "⚠️",
    "important": "❗",
    "question": "❓",
}


class NotionError(RuntimeError):
    pass


class NotionClient:
    def __init__(self, token: str, notion_version: str, dry_run: bool = False, timeout: int = 30) -> None:
        self.base_url = "https://api.notion.com/v1"
        self.token = token
        self.notion_version = notion_version
        self.dry_run = dry_run
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        req = request.Request(url=url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Notion-Version", self.notion_version)
        req.add_header("Content-Type", "application/json")

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise NotionError(f"Notion API {exc.code} {method} {path}: {raw}") from exc
        except error.URLError as exc:
            raise NotionError(f"Notion API connection error for {method} {path}: {exc}") from exc

        if not raw:
            return {}

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise NotionError(f"Invalid JSON response from Notion API {method} {path}: {raw[:200]}") from exc

    def iterate_block_children(self, block_id: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            resp = self._request("GET", f"/blocks/{normalize_notion_id(block_id)}/children", params=params)
            out.extend(resp.get("results", []))
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")
        return out

    def list_child_pages(self, parent_page_id: str) -> dict[str, str]:
        pages: dict[str, str] = {}
        for block in self.iterate_block_children(parent_page_id):
            if block.get("type") != "child_page":
                continue
            title = (block.get("child_page", {}).get("title") or "").strip()
            block_id = block.get("id")
            if not title or not block_id:
                continue
            pages[title] = block_id
        return pages

    def create_page(self, parent_page_id: str, title: str, icon_emoji: str | None = None) -> str:
        if self.dry_run:
            fake = f"dryrun-{uuid.uuid4().hex[:24]}"
            print(f"DRYRUN CREATE PAGE: parent={parent_page_id} title={title} id={fake}")
            return fake

        payload: dict[str, Any] = {
            "parent": {"page_id": normalize_notion_id(parent_page_id)},
            "properties": {
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title},
                        }
                    ]
                }
            },
        }
        if icon_emoji:
            payload["icon"] = {"type": "emoji", "emoji": icon_emoji}

        resp = self._request("POST", "/pages", payload=payload)
        page_id = resp.get("id")
        if not page_id:
            raise NotionError(f"Create page response missing id for title '{title}'")
        return page_id

    def append_children(self, block_id: str, children: list[dict[str, Any]]) -> None:
        if not children:
            return
        if self.dry_run:
            print(f"DRYRUN APPEND: block={block_id} blocks={len(children)}")
            return
        payload = {"children": children}
        self._request("PATCH", f"/blocks/{normalize_notion_id(block_id)}/children", payload=payload)

    def archive_block(self, block_id: str) -> None:
        if self.dry_run:
            print(f"DRYRUN ARCHIVE BLOCK: {block_id}")
            return
        self._request("PATCH", f"/blocks/{normalize_notion_id(block_id)}", payload={"archived": True})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync missing Obsidian daily output pages into Notion US Dream hierarchy."
    )
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT, help="Obsidian vault root path")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Output root (default: <vault>/50_Output)",
    )
    parser.add_argument(
        "--us-dream-page-id",
        default=DEFAULT_US_DREAM_PAGE_ID,
        help="Notion page ID for US Dream parent page",
    )
    parser.add_argument(
        "--notion-token",
        default=os.getenv("NOTION_TOKEN"),
        help="Notion integration token (default: env NOTION_TOKEN)",
    )
    parser.add_argument(
        "--notion-version",
        default=DEFAULT_NOTION_VERSION,
        help="Notion-Version header",
    )
    parser.add_argument(
        "--week",
        action="append",
        default=[],
        help="Restrict to specific week(s), e.g. 2026-W08 (repeatable)",
    )
    parser.add_argument("--from-date", default=None, help="Start date inclusive (YYYY-MM-DD)")
    parser.add_argument("--to-date", default=None, help="End date inclusive (YYYY-MM-DD)")
    parser.add_argument("--skip-index", action="store_true", help="Skip index pages update")
    parser.add_argument(
        "--replace-existing-doc-content",
        action="store_true",
        help="Replace content of existing doc pages as well (destructive to current doc blocks)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan and print without writes")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def parse_date(value: str | None, field_name: str) -> dt.date | None:
    if value is None:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid {field_name} '{value}'. Use YYYY-MM-DD.") from exc


def normalize_notion_id(value: str) -> str:
    return re.sub(r"[^a-fA-F0-9]", "", value)


def notion_url(page_id: str) -> str:
    clean = normalize_notion_id(page_id)
    return f"https://www.notion.so/{clean}"


def chunk_text(text: str, max_len: int = 1800) -> list[str]:
    if not text:
        return [" "]
    return [text[i : i + max_len] for i in range(0, len(text), max_len)]


def inline_segments(markdown_text: str) -> list[tuple[str, str | None]]:
    segments: list[tuple[str, str | None]] = []
    cursor = 0
    for match in LINK_RE.finditer(markdown_text):
        start, end = match.span()
        if start > cursor:
            segments.append((markdown_text[cursor:start], None))
        segments.append((match.group(1), match.group(2)))
        cursor = end
    if cursor < len(markdown_text):
        segments.append((markdown_text[cursor:], None))
    if not segments:
        segments.append((markdown_text, None))
    return segments


def rich_text_from_markdown(markdown_text: str) -> list[dict[str, Any]]:
    rich: list[dict[str, Any]] = []
    for text, link in inline_segments(markdown_text):
        for part in chunk_text(text):
            node: dict[str, Any] = {"type": "text", "text": {"content": part}}
            if link:
                node["text"]["link"] = {"url": link}
            rich.append(node)
    return rich or [{"type": "text", "text": {"content": " "}}]


def block_with_text(block_type: str, text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": rich_text_from_markdown(text),
        },
    }


def to_do_block(text: str, checked: bool) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": rich_text_from_markdown(text),
            "checked": checked,
        },
    }


def code_block(code: str, language: str = "plain text") -> dict[str, Any]:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": part}} for part in chunk_text(code)],
            "language": language,
        },
    }


def quote_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "quote",
        "quote": {
            "rich_text": rich_text_from_markdown(text),
        },
    }


def bullet_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": rich_text_from_markdown(text),
        },
    }


def numbered_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": rich_text_from_markdown(text),
        },
    }


def callout_block(title: str, icon_emoji: str, children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    block: dict[str, Any] = {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": rich_text_from_markdown(title.strip() or " "),
            "icon": {"type": "emoji", "emoji": icon_emoji},
            "color": "default",
        },
    }
    if children:
        block["children"] = children
    return block


def preprocess_markdown(markdown: str) -> str:
    text = markdown.replace("\r\n", "\n").replace("\r", "\n")

    # Strip YAML frontmatter at the top, if present.
    m = FRONTMATTER_RE.match(text)
    if m:
        text = text[m.end() :]

    normalized_lines: list[str] = []
    for line in text.split("\n"):
        # Obsidian code block IDs: ```id="abc"
        if re.match(r'^```id="[^"]*"\s*$', line.strip()):
            normalized_lines.append("```plain text")
            continue

        # Obsidian language + ID: ```java id="abc"
        lang_with_id = re.match(r"^```([A-Za-z0-9_+\-]+)\s+id=\"[^\"]*\"\s*$", line.strip())
        if lang_with_id:
            normalized_lines.append(f"```{lang_with_id.group(1)}")
            continue

        normalized_lines.append(line)

    return "\n".join(normalized_lines)


def extract_code_language(fence_info: str) -> str:
    info = fence_info.strip()
    if not info:
        return "plain text"
    first = info.split()[0]
    if first.startswith("id="):
        return "plain text"
    lowered = first.lower()
    if lowered in {"text", "plain", "plaintext"}:
        return "plain text"
    return lowered


def is_special_line(line: str) -> bool:
    stripped = line.strip()
    if stripped == "":
        return True
    if stripped == "---":
        return True
    if stripped.startswith("```"):
        return True
    if re.match(r"^#{1,6}\s+", stripped):
        return True
    if re.match(r"^>\s*", stripped):
        return True
    if re.match(r"^\s*-\s+\[[ xX]\]\s+", line):
        return True
    if re.match(r"^\s*[-*+]\s+", line):
        return True
    if re.match(r"^\s*\d+\.\s+", line):
        return True
    return False


def markdown_to_notion_blocks(markdown: str) -> list[dict[str, Any]]:
    lines = preprocess_markdown(markdown).split("\n")
    blocks: list[dict[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            i += 1
            continue

        if stripped == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        code_start = re.match(r"^```(.*)$", stripped)
        if code_start:
            lang = extract_code_language(code_start.group(1) or "")
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            blocks.append(code_block("\n".join(code_lines), language=lang))
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = min(len(heading.group(1)), 3)
            text = heading.group(2).strip() or " "
            blocks.append(block_with_text(f"heading_{level}", text))
            i += 1
            continue

        todo = re.match(r"^\s*-\s+\[([ xX])\]\s+(.*)$", line)
        if todo:
            checked = todo.group(1).lower() == "x"
            text = todo.group(2).strip() or " "
            blocks.append(to_do_block(text, checked=checked))
            i += 1
            continue

        bullet = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if bullet:
            text = bullet.group(1).strip() or " "
            blocks.append(bullet_block(text))
            i += 1
            continue

        numbered = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if numbered:
            text = numbered.group(1).strip() or " "
            blocks.append(numbered_block(text))
            i += 1
            continue

        callout_start = OBSIDIAN_CALLOUT_RE.match(stripped)
        if callout_start:
            kind = callout_start.group(1).lower()
            icon = CALLOUT_ICON_BY_KIND.get(kind, "📝")
            i += 1

            body_lines: list[str] = []
            while i < len(lines):
                current = lines[i]
                current_stripped = current.strip()

                # Stop at the next callout marker.
                if OBSIDIAN_CALLOUT_RE.match(current_stripped):
                    break

                if current_stripped == "":
                    body_lines.append("")
                    i += 1
                    continue

                if re.match(r"^\s*>", current):
                    body_lines.append(re.sub(r"^\s*>\s?", "", current))
                    i += 1
                    continue

                break

            while body_lines and not body_lines[0].strip():
                body_lines.pop(0)
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()

            title = "Note"
            children_lines = body_lines
            for idx, candidate in enumerate(body_lines):
                if candidate.strip():
                    title = candidate.strip()
                    children_lines = body_lines[:idx] + body_lines[idx + 1 :]
                    break

            children_markdown = "\n".join(children_lines).strip()
            children_blocks = markdown_to_notion_blocks(children_markdown) if children_markdown else []
            blocks.append(callout_block(title=title, icon_emoji=icon, children=children_blocks))
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q = re.sub(r"^\s*>\s?", "", lines[i]).rstrip()
                quote_lines.append(q)
                i += 1
            blocks.append(quote_block("\n".join(quote_lines).strip() or " "))
            continue

        para_lines = [line.strip()]
        i += 1
        while i < len(lines) and not is_special_line(lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        blocks.append(block_with_text("paragraph", " ".join(para_lines).strip() or " "))

    return blocks


def parse_block_plain_text(block: dict[str, Any]) -> str:
    block_type = block.get("type")
    if not block_type:
        return ""
    data = block.get(block_type, {})
    if "title" in data and isinstance(data.get("title"), str):
        return data["title"]
    rich = data.get("rich_text")
    if not isinstance(rich, list):
        return ""
    return "".join(part.get("plain_text", "") for part in rich)


def scan_output_tree(
    output_root: Path,
    week_filters: set[str],
    from_date: dt.date | None,
    to_date: dt.date | None,
) -> dict[str, dict[str, list[Path]]]:
    plan: dict[str, dict[str, list[Path]]] = {}

    if not output_root.exists():
        raise SystemExit(f"Output root not found: {output_root}")

    for week_dir in sorted(output_root.iterdir()):
        if not week_dir.is_dir() or not WEEK_RE.match(week_dir.name):
            continue
        week = week_dir.name
        if week_filters and week not in week_filters:
            continue

        date_map: dict[str, list[Path]] = {}
        for date_dir in sorted(week_dir.iterdir()):
            if not date_dir.is_dir() or not DATE_RE.match(date_dir.name):
                continue
            day = dt.date.fromisoformat(date_dir.name)
            if from_date and day < from_date:
                continue
            if to_date and day > to_date:
                continue

            md_files = sorted([p for p in date_dir.iterdir() if p.is_file() and p.suffix.lower() == ".md"])
            if md_files:
                date_map[date_dir.name] = md_files

        if date_map:
            plan[week] = date_map

    return plan


class SyncEngine:
    def __init__(
        self,
        client: NotionClient,
        us_dream_page_id: str,
        verbose: bool = False,
        replace_existing_doc_content: bool = False,
    ) -> None:
        self.client = client
        self.us_dream_page_id = us_dream_page_id
        self.verbose = verbose
        self.replace_existing_doc_content = replace_existing_doc_content
        self.child_cache: dict[str, dict[str, str]] = {}
        self.index_entries: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))

        self.created_weeks: list[str] = []
        self.created_dates: list[str] = []
        self.created_docs: list[str] = []

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def child_pages(self, parent_id: str) -> dict[str, str]:
        parent_id = normalize_notion_id(parent_id)
        if parent_id not in self.child_cache:
            self.child_cache[parent_id] = self.client.list_child_pages(parent_id)
        return self.child_cache[parent_id]

    def ensure_child_page(self, parent_id: str, title: str, icon_emoji: str | None = None) -> tuple[str, bool]:
        pages = self.child_pages(parent_id)
        if title in pages:
            return pages[title], False

        page_id = self.client.create_page(parent_id=parent_id, title=title, icon_emoji=icon_emoji)
        pages[title] = page_id
        return page_id, True

    def append_markdown_page_content(self, page_id: str, markdown_text: str) -> None:
        blocks = markdown_to_notion_blocks(markdown_text)
        if not blocks:
            return
        for i in range(0, len(blocks), 100):
            self.client.append_children(page_id, blocks[i : i + 100])

    def replace_markdown_page_content(self, page_id: str, markdown_text: str) -> None:
        existing_blocks = self.client.iterate_block_children(page_id)
        for block in existing_blocks:
            block_id = block.get("id")
            if not block_id:
                continue
            self.client.archive_block(block_id)
        self.append_markdown_page_content(page_id, markdown_text)

    def sync_week(self, week: str, date_files: dict[str, list[Path]]) -> None:
        week_page_id, created_week = self.ensure_child_page(
            self.us_dream_page_id,
            title=week,
            icon_emoji="📍",
        )
        if created_week:
            self.created_weeks.append(week)
            print(f"CREATE WEEK: {week}")
        else:
            self._log(f"EXIST WEEK: {week}")

        for date_str in sorted(date_files.keys()):
            date_page_id, created_date = self.ensure_child_page(week_page_id, title=date_str, icon_emoji="🗓️")
            if created_date:
                self.created_dates.append(date_str)
                print(f"CREATE DATE: {week}/{date_str}")
            else:
                self._log(f"EXIST DATE: {week}/{date_str}")

            for md_path in date_files[date_str]:
                doc_title = md_path.stem
                doc_page_id, created_doc = self.ensure_child_page(date_page_id, title=doc_title)
                if created_doc:
                    content = md_path.read_text(encoding="utf-8")
                    self.append_markdown_page_content(doc_page_id, content)
                    self.created_docs.append(f"{week}/{date_str}/{doc_title}")
                    print(f"CREATE DOC: {week}/{date_str}/{doc_title}")
                else:
                    if self.replace_existing_doc_content:
                        content = md_path.read_text(encoding="utf-8")
                        self.replace_markdown_page_content(doc_page_id, content)
                        print(f"REFRESH DOC: {week}/{date_str}/{doc_title}")
                    else:
                        self._log(f"EXIST DOC: {week}/{date_str}/{doc_title}")

            child_titles = self.child_pages(date_page_id)
            for artifact, index_page_title in INDEX_PAGE_BY_ARTIFACT.items():
                artifact_page_id = child_titles.get(artifact)
                if artifact_page_id:
                    self.index_entries[index_page_title][week].append((date_str, artifact_page_id))

    def sync_index_pages(self) -> None:
        if not self.index_entries:
            return

        index_root_id, created_root = self.ensure_child_page(
            self.us_dream_page_id,
            title=INDEX_ROOT_TITLE,
            icon_emoji="📇",
        )
        if created_root:
            print(f"CREATE INDEX ROOT: {INDEX_ROOT_TITLE}")

        for index_page_title, week_map in sorted(self.index_entries.items()):
            index_page_id, created = self.ensure_child_page(index_root_id, title=index_page_title)
            if created:
                print(f"CREATE INDEX PAGE: {index_page_title}")

            existing_blocks = self.client.iterate_block_children(index_page_id)
            existing_lines = [parse_block_plain_text(b).strip() for b in existing_blocks]
            existing_lines = [line for line in existing_lines if line]
            existing_week_headings = {line for line in existing_lines if WEEK_RE.match(line)}

            existing_signatures: set[str] = set()
            for line in existing_lines:
                m_date = re.search(r"(\d{4}-\d{2}-\d{2})", line)
                if not m_date:
                    continue
                for artifact_title, mapped_index in INDEX_PAGE_BY_ARTIFACT.items():
                    if mapped_index != index_page_title:
                        continue
                    if artifact_title in line:
                        existing_signatures.add(f"{artifact_title}|{m_date.group(1)}")

            index_artifact_title = next(
                (artifact for artifact, page_name in INDEX_PAGE_BY_ARTIFACT.items() if page_name == index_page_title),
                None,
            )
            if not index_artifact_title:
                continue

            for week in sorted(week_map.keys()):
                if week not in existing_week_headings:
                    self.client.append_children(index_page_id, [block_with_text("heading_2", week)])
                    existing_week_headings.add(week)
                    print(f"UPDATE INDEX: {index_page_title} add week heading {week}")

                seen_dates: set[str] = set()
                for date_str, artifact_page_id in sorted(week_map[week], key=lambda x: x[0]):
                    if date_str in seen_dates:
                        continue
                    seen_dates.add(date_str)

                    sig = f"{index_artifact_title}|{date_str}"
                    if sig in existing_signatures:
                        continue

                    bullet = {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": f"{date_str}: "}},
                                {
                                    "type": "text",
                                    "text": {
                                        "content": index_artifact_title,
                                        "link": {"url": notion_url(artifact_page_id)},
                                    },
                                },
                            ]
                        },
                    }
                    self.client.append_children(index_page_id, [bullet])
                    existing_signatures.add(sig)
                    print(f"UPDATE INDEX: {index_page_title} add {date_str}")


def main() -> None:
    args = parse_args()

    from_date = parse_date(args.from_date, "--from-date")
    to_date = parse_date(args.to_date, "--to-date")
    if from_date and to_date and from_date > to_date:
        raise SystemExit("--from-date must be <= --to-date")

    vault = args.vault.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve() if args.output_root else vault / DEFAULT_OUTPUT_SUBDIR

    if not args.notion_token:
        raise SystemExit("Missing Notion token. Set NOTION_TOKEN or pass --notion-token.")

    week_filters = set(args.week)
    plan = scan_output_tree(output_root, week_filters=week_filters, from_date=from_date, to_date=to_date)

    if not plan:
        print("NOOP: no matching markdown outputs found")
        return

    client = NotionClient(
        token=args.notion_token,
        notion_version=args.notion_version,
        dry_run=args.dry_run,
    )
    engine = SyncEngine(
        client=client,
        us_dream_page_id=args.us_dream_page_id,
        verbose=args.verbose,
        replace_existing_doc_content=args.replace_existing_doc_content,
    )

    print(f"START: weeks={len(plan)} dry_run={args.dry_run}")
    for week in sorted(plan.keys()):
        engine.sync_week(week, plan[week])

    if not args.skip_index:
        engine.sync_index_pages()

    print("DONE")
    print(f"SUMMARY: created_week={len(engine.created_weeks)} created_date={len(engine.created_dates)} created_doc={len(engine.created_docs)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise
    except NotionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
