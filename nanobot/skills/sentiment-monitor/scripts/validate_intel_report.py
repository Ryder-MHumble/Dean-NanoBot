#!/usr/bin/env python3
"""
Lightweight report validator for intelligence-style markdown output.

Checks:
- optional P1/P2/P3 presence
- optional URL presence
- max character budget
- optional dual-dimension section completeness
- optional actionable checklist completeness
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import Dict, List, Tuple

PRIORITY_RE = re.compile(r"\bP[123]\b")
URL_RE = re.compile(r"https?://[^\s)]+")
MISSING_LINK_RE = re.compile(r"原始链接缺失|链接缺失")
TOP_POST_PRIORITY_RE = re.compile(r"^\d+\.\s+\[P[123]\]\s+《", re.MULTILINE)
OPPORTUNITY_PRIORITY_RE = re.compile(r"^\d+\.\s+\[P[123]\]\s+\*\*《", re.MULTILINE)
RISK_PRIORITY_RE = re.compile(r"^####\s+P[123]\s+/", re.MULTILINE)
CHECKLIST_ITEM_RE = re.compile(r"^\s*-\s+\[\s\]\s+", re.MULTILINE)
PRIMARY_CASE_SECTION_RE = re.compile(r"##\s+二、我方高相关负面案例")
BENCHMARK_SECTION_RE = re.compile(r"##\s+三、兄弟机构对比")
RELEVANCE_REASON_RE = re.compile(r"高相关依据：")
NO_PRIMARY_HIT_RE = re.compile(r"未发现满足高相关门槛的负面帖子")


def _to_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate intel report quality gates")
    parser.add_argument("--file", default="-", help="Input file path, or '-' for stdin")
    parser.add_argument("--require-priority", default="true", choices=["true", "false"])
    parser.add_argument("--require-links", default="true", choices=["true", "false"])
    parser.add_argument("--require-dual-dimensions", default="false", choices=["true", "false"])
    parser.add_argument("--require-action-checklist", default="true", choices=["true", "false"])
    parser.add_argument("--require-primary-monitoring", default="false", choices=["true", "false"])
    parser.add_argument("--require-benchmark-section", default="false", choices=["true", "false"])
    parser.add_argument("--require-relevance-reasons", default="false", choices=["true", "false"])
    parser.add_argument("--max-chars", type=int, default=8000)
    parser.add_argument("--allow-missing-links", type=int, default=0)
    return parser.parse_args()


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _count_link_required_priority_items(text: str) -> int:
    return (
        len(TOP_POST_PRIORITY_RE.findall(text))
        + len(OPPORTUNITY_PRIORITY_RE.findall(text))
        + len(RISK_PRIORITY_RE.findall(text))
    )


def validate_report_text(
    text: str,
    *,
    require_priority: bool = True,
    require_links: bool = True,
    require_dual_dimensions: bool = False,
    require_action_checklist: bool = True,
    require_primary_monitoring: bool = False,
    require_benchmark_section: bool = False,
    require_relevance_reasons: bool = False,
    max_chars: int = 8000,
    allow_missing_links: int = 0,
) -> Tuple[List[str], Dict[str, int]]:
    body = text.strip()
    if not body:
        return ["empty report"], {}

    errors: List[str] = []

    char_count = len(body)
    priorities = PRIORITY_RE.findall(body)
    urls = URL_RE.findall(body)
    missing_link_marks = MISSING_LINK_RE.findall(body)
    link_required_priority_items = _count_link_required_priority_items(body)
    checklist_items = CHECKLIST_ITEM_RE.findall(body)
    relevance_reasons = RELEVANCE_REASON_RE.findall(body)
    has_no_primary_hit = bool(NO_PRIMARY_HIT_RE.search(body))

    if char_count > max_chars:
        errors.append(f"char_count={char_count} exceeds max={max_chars}")

    if require_priority and not priorities:
        errors.append("missing priority labels P1/P2/P3")

    if require_links:
        if not urls and not missing_link_marks:
            errors.append("missing source links")
        if (
            link_required_priority_items > 0
            and len(urls) + len(missing_link_marks) + allow_missing_links < link_required_priority_items
        ):
            errors.append(
                "link coverage insufficient for risk/opportunity/top-post items: "
                f"urls({len(urls)}) + missing_marks({len(missing_link_marks)}) + "
                f"allow_missing({allow_missing_links}) < required_items({link_required_priority_items})"
            )

    if require_dual_dimensions:
        if "## 一、官方账号运营分析" not in body:
            errors.append("missing section: 一、官方账号运营分析")
        if "## 二、全网舆情洞察" not in body:
            errors.append("missing section: 二、全网舆情洞察")

    if require_action_checklist:
        if "## 四、立即执行清单" not in body and "### 2.4 立即执行清单" not in body:
            errors.append("missing section: 立即执行清单")
        elif not checklist_items:
            errors.append("missing actionable checklist items (- [ ])")
        elif len(checklist_items) < 3:
            errors.append(f"checklist items too few: {len(checklist_items)} < 3")

    if require_primary_monitoring and not PRIMARY_CASE_SECTION_RE.search(body):
        errors.append("missing section: 二、我方高相关负面案例")

    if require_benchmark_section and not BENCHMARK_SECTION_RE.search(body):
        errors.append("missing section: 三、兄弟机构对比")

    if require_relevance_reasons and not has_no_primary_hit:
        case_count = len(RISK_PRIORITY_RE.findall(body))
        if case_count > 0 and len(relevance_reasons) < case_count:
            errors.append(
                "relevance reason coverage insufficient: "
                f"reasons({len(relevance_reasons)}) < cases({case_count})"
            )

    metrics = {
        "char_count": char_count,
        "priority_labels": len(priorities),
        "urls": len(urls),
        "missing_link_marks": len(missing_link_marks),
        "link_required_priority_items": link_required_priority_items,
        "checklist_items": len(checklist_items),
        "relevance_reasons": len(relevance_reasons),
    }
    return errors, metrics


def main() -> int:
    args = parse_args()
    text = read_text(args.file)

    errors, metrics = validate_report_text(
        text,
        require_priority=_to_bool(args.require_priority),
        require_links=_to_bool(args.require_links),
        require_dual_dimensions=_to_bool(args.require_dual_dimensions),
        require_action_checklist=_to_bool(args.require_action_checklist),
        require_primary_monitoring=_to_bool(args.require_primary_monitoring),
        require_benchmark_section=_to_bool(args.require_benchmark_section),
        require_relevance_reasons=_to_bool(args.require_relevance_reasons),
        max_chars=args.max_chars,
        allow_missing_links=args.allow_missing_links,
    )

    if errors:
        print("FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("PASS")
    for key in [
        "char_count",
        "priority_labels",
        "urls",
        "missing_link_marks",
        "link_required_priority_items",
        "checklist_items",
        "relevance_reasons",
    ]:
        print(f"{key}={metrics.get(key, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
