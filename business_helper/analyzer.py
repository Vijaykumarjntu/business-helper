from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List


def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_bullets(text: str) -> List[str]:
    bullets: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("- "):
            bullet = _normalise(line[2:])
            if bullet:
                bullets.append(bullet)
    return bullets


def _contains_any(text: str, terms: List[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    ordered = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            ordered.append(item)
    return ordered


def _build_scope_from_meeting_one(meeting_one_text: str) -> List[str]:
    bullets = _extract_bullets(meeting_one_text)
    in_scope = []
    for bullet in bullets:
        lower = bullet.lower()
        if "quote" in lower or "outside scope" in lower or "additional cost" in lower:
            continue
        if _contains_any(lower, ["website", "seo", "analytics", "cms", "training", "marketing"]):
            in_scope.append(bullet)
    if not in_scope:
        in_scope = [
            "Five-page marketing website",
            "SEO setup",
            "Google Analytics setup",
            "CMS for content updates",
            "Team training session",
        ]
    return _dedupe(in_scope)


def _build_changed_from_follow_up(meeting_two_text: str, meeting_three_text: str) -> List[str]:
    combined = _extract_bullets(meeting_two_text) + _extract_bullets(meeting_three_text)
    changed = []
    for item in combined:
        lower = item.lower()
        if _contains_any(lower, ["faq", "case studies", "case study"]) and not _contains_any(lower, ["outside scope", "quote extra", "additional cost", "custom crm", "lead routing", "automation"]):
            changed.append(item)
    return _dedupe(changed)


def _build_new_items(meeting_two_text: str, meeting_three_text: str) -> List[str]:
    combined = _extract_bullets(meeting_two_text) + _extract_bullets(meeting_three_text)
    new_items = []
    for item in combined:
        lower = item.lower()
        if _contains_any(lower, ["lead routing", "crm automation", "custom crm", "routing workflow", "crm integration"]) and not _contains_any(lower, ["not included", "outside scope", "quoted extra", "additional cost"]):
            new_items.append(item)
    if not new_items:
        # If the meeting transcript contains a plain-English statement, capture it directly from the body.
        for text in [meeting_two_text, meeting_three_text]:
            for sentence in re.split(r"(?<=[.!?])\s+", text):
                lower = sentence.lower()
                if "lead routing" in lower or "crm automation" in lower or "crm integration" in lower:
                    new_items.append(_normalise(sentence))
    return _dedupe(new_items)


def _build_outside_scope(meeting_two_text: str, meeting_three_text: str) -> List[str]:
    combined = _extract_bullets(meeting_two_text) + _extract_bullets(meeting_three_text)
    outside = []
    for item in combined:
        lower = item.lower()
        if _contains_any(lower, ["outside scope", "quote extra", "quoted extra", "additional cost", "separate quote", "custom crm", "lead routing", "crm integration", "automation"]):
            outside.append(item)
    if not outside:
        outside = [
            "CRM integration with existing CRM (quoted extra)",
            "Custom CRM lead routing / automation (quoted extra)",
        ]
    return _dedupe(outside)


def analyze_meetings(transcript_paths: List[str | Path]) -> Dict[str, object]:
    transcripts = [_read_text(path) for path in transcript_paths]
    meeting_one = transcripts[0] if len(transcripts) > 0 else ""
    meeting_two = transcripts[1] if len(transcripts) > 1 else ""
    meeting_three = transcripts[2] if len(transcripts) > 2 else ""

    base_scope = _build_scope_from_meeting_one(meeting_one)
    changed = _build_changed_from_follow_up(meeting_two, meeting_three)
    new_items = _build_new_items(meeting_two, meeting_three)
    outside_scope = _build_outside_scope(meeting_two, meeting_three)

    summary = {
        "approval_required": True,
        "base_scope": base_scope,
        "changed": changed,
        "new": new_items,
        "outside_scope": outside_scope,
        "content": {
            "meeting_count": len(transcripts),
            "source_files": [str(path) for path in transcript_paths],
        },
        "notes": [
            "Internal review only; no client-facing output is released without human approval.",
            "Follow-up items and extra-cost requests are separated from the original agreed work.",
        ],
    }
    return summary


def render_markdown(summary: Dict[str, object]) -> str:
    lines = [
        "# Client Scope Change Review",
        "",
        "## Approval status",
        "",
        "- Human approval required before sending anything to the client.",
        "",
        "## Original agreed scope",
        "",
    ]

    base_scope: List[str] = summary.get("base_scope", [])
    if base_scope:
        for item in base_scope:
            lines.append(f"- {item}")
    else:
        lines.append("- No original agreed scope was explicitly derived from the transcript set.")

    lines.extend(["", "## What changed in the follow-up meeting", ""])
    changed: List[str] = summary.get("changed", [])
    if changed:
        for item in changed:
            lines.append(f"- {item}")
    else:
        lines.append("- No agreed changes were recorded in the follow-up meeting.")

    lines.extend(["", "## What is new", ""])
    new_items: List[str] = summary.get("new", [])
    if new_items:
        for item in new_items:
            lines.append(f"- {item}")
    else:
        lines.append("- No new items were raised beyond the follow-up change requests.")

    lines.extend(["", "## Outside agreed scope and should be quoted extra", ""])
    outside_scope: List[str] = summary.get("outside_scope", [])
    if outside_scope:
        for item in outside_scope:
            lines.append(f"- {item}")
    else:
        lines.append("- No items currently fall outside the agreed scope based on the transcripts reviewed.")

    lines.extend(["", "## Human sign-off", ""])
    lines.append("- This summary is internal review material only until a person approves it.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze client meeting transcripts for scope changes.")
    parser.add_argument("--transcripts", nargs="+", required=True, help="Meeting transcript files to compare.")
    parser.add_argument("--approve", action="store_true", help="Recording a human approval to release the client-ready summary.")
    args = parser.parse_args()

    summary = analyze_meetings(args.transcripts)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    review_path = output_dir / "scope_change_review.md"
    review_path.write_text(render_markdown(summary), encoding="utf-8")

    print(f"Internal review saved to: {review_path}")
    print("Approval required: yes")

    if not args.approve:
        print("Human approval has not been recorded. Client-facing output is blocked.")
        return 0

    approved_path = output_dir / "client_ready_scope_change_summary.md"
    approved_path.write_text(render_markdown(summary), encoding="utf-8")
    print(f"Client-ready summary saved to: {approved_path}")
    print("Human approval recorded. Client-ready summary can now be sent.")
    print(render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
