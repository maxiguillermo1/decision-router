#!/usr/bin/env python3
"""X engage gate (playbook desk pattern F) — drafts only; never auto-post."""

from __future__ import annotations

import argparse
import json
import sys

from decision_router import system_one
from decision_router.recipes import ENGAGE_ACTION, SAFE_TO_ENGAGE


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True, help="Post text (truncated in state)")
    p.add_argument("--views", type=int, default=0)
    p.add_argument("--likes", type=int, default=0)
    p.add_argument("--author", default="")
    p.add_argument("--watchlist", action="store_true")
    p.add_argument("--floor-views", type=int, default=5000)
    p.add_argument("--backend", default="rules", choices=("rules", "jev"))
    args = p.parse_args()

    state = {
        "post_text": args.text[:2000],
        "views": args.views,
        "likes": args.likes,
        "author": args.author,
        "watchlist": args.watchlist,
        "floor_views": args.floor_views,
    }
    result = system_one(
        state,
        {"engage_action": ENGAGE_ACTION, "safe_to_engage_without_human": SAFE_TO_ENGAGE},
        backend=args.backend,
    )
    out = {
        "backend": result.backend,
        "engage_action": {
            "choice": result.choices["engage_action"].choice,
            "confidence": result.choices["engage_action"].confidence,
        },
        "safe_to_engage_without_human": {
            "value": result.nouls["safe_to_engage_without_human"].value,
            "confidence": result.nouls["safe_to_engage_without_human"].confidence,
        },
        "policy": "Never auto-post. Low confidence → treat as skip/review.",
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
