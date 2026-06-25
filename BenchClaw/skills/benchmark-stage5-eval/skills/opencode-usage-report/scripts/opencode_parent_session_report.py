#!/usr/bin/env python3
import argparse
import glob
import json
import os
import pathlib
import sqlite3
from typing import Any


TOKEN_COLUMNS = [
    "tokens_input",
    "tokens_output",
    "tokens_reasoning",
    "tokens_cache_read",
    "tokens_cache_write",
]

SESSION_ID_ENV_KEYS = [
    "BENCHCLAW_OPENCODE_SESSION_ID",
    "OPENCODE_SESSION_ID",
    "OPENCODE_CURRENT_SESSION_ID",
    "SESSION_ID",
]


def find_db(explicit: str | None = None) -> str:
    data_dir = pathlib.Path(os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local/share")) / "opencode"
    db = explicit or os.environ.get("OPENCODE_DB")

    if db and db != ":memory:":
        if not os.path.isabs(db):
            db = str(data_dir / db)
        if os.path.exists(db):
            return db
        raise SystemExit(f"opencode database not found: {db}")

    candidates = [str(data_dir / "opencode.db")] + glob.glob(str(data_dir / "opencode-*.db"))
    existing = [p for p in candidates if os.path.exists(p)]
    if not existing:
        raise SystemExit(f"no opencode database found under {data_dir}")
    return max(existing, key=os.path.getmtime)


def total_tokens(row: sqlite3.Row) -> int:
    return sum(int(row[col] or 0) for col in TOKEN_COLUMNS)


def short_id(session_id: str) -> str:
    return session_id[-8:]


def model_label(model_json: str | None) -> str:
    if not model_json:
        return ""
    try:
        model = json.loads(model_json)
    except json.JSONDecodeError:
        return ""
    provider = model.get("providerID") or model.get("providerId") or ""
    model_id = model.get("id") or ""
    return f"{provider}/{model_id}" if provider or model_id else ""


def money(value: Any) -> str:
    return f"{float(value or 0):.6f}"


def fmt_int(value: Any) -> str:
    return f"{int(value or 0):,}"


def print_table(headers: list[str], rows: list[list[Any]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))

    template = "  ".join("{:<" + str(width) + "}" for width in widths)
    print(template.format(*headers))
    print(template.format(*["-" * width for width in widths]))
    for row in rows:
        print(template.format(*row))


def session_by_id(con: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    return con.execute(
        """
        select
          id, parent_id, title, agent, model, cost,
          tokens_input, tokens_output, tokens_reasoning,
          tokens_cache_read, tokens_cache_write,
          datetime(time_created / 1000, 'unixepoch', 'localtime') as created,
          datetime(time_updated / 1000, 'unixepoch', 'localtime') as updated
        from session
        where id = ?
        """,
        (session_id,),
    ).fetchone()


def latest_session(con: sqlite3.Connection) -> sqlite3.Row | None:
    return con.execute(
        """
        select
          id, parent_id, title, agent, model, cost,
          tokens_input, tokens_output, tokens_reasoning,
          tokens_cache_read, tokens_cache_write,
          datetime(time_created / 1000, 'unixepoch', 'localtime') as created,
          datetime(time_updated / 1000, 'unixepoch', 'localtime') as updated
        from session
        order by time_updated desc
        limit 1
        """
    ).fetchone()


def latest_parent(con: sqlite3.Connection) -> sqlite3.Row | None:
    return con.execute(
        """
        select
          id, parent_id, title, agent, model, cost,
          tokens_input, tokens_output, tokens_reasoning,
          tokens_cache_read, tokens_cache_write,
          datetime(time_created / 1000, 'unixepoch', 'localtime') as created,
          datetime(time_updated / 1000, 'unixepoch', 'localtime') as updated
        from session
        where parent_id is null
        order by time_updated desc
        limit 1
        """
    ).fetchone()


def root_for_session(con: sqlite3.Connection, session_id: str) -> sqlite3.Row:
    row = session_by_id(con, session_id)
    if not row:
        raise SystemExit(f"session not found: {session_id}")
    seen: set[str] = set()
    while row["parent_id"]:
        if row["id"] in seen:
            raise SystemExit(f"cycle detected in session parent chain at {row['id']}")
        seen.add(row["id"])
        parent = session_by_id(con, row["parent_id"])
        if not parent:
            raise SystemExit(f"parent session not found: {row['parent_id']}")
        row = parent
    return row


def current_session_from_env(con: sqlite3.Connection) -> tuple[sqlite3.Row | None, str | None]:
    for key in SESSION_ID_ENV_KEYS:
        session_id = os.environ.get(key)
        if not session_id:
            continue
        row = session_by_id(con, session_id)
        if row:
            return row, key
    return None, None


def parent_total(con: sqlite3.Connection, parent_id: str) -> sqlite3.Row:
    return con.execute(
        """
        with recursive tree(id) as (
          select id from session where id = ?
          union all
          select s.id from session s join tree on s.parent_id = tree.id
        )
        select
          count(*) as session_count,
          sum(case when s.id = ? then 0 else 1 end) as child_count,
          sum(s.cost) as cost,
          sum(s.tokens_input) as tokens_input,
          sum(s.tokens_output) as tokens_output,
          sum(s.tokens_reasoning) as tokens_reasoning,
          sum(s.tokens_cache_read) as tokens_cache_read,
          sum(s.tokens_cache_write) as tokens_cache_write
        from tree
        join session s on s.id = tree.id
        """,
        (parent_id, parent_id),
    ).fetchone()


def direct_child_reports(con: sqlite3.Connection, parent_id: str) -> list[sqlite3.Row]:
    return con.execute(
        """
        with recursive tree(group_id, id) as (
          select id, id from session where parent_id = ?
          union all
          select tree.group_id, s.id
          from session s
          join tree on s.parent_id = tree.id
        )
        select
          root.id,
          root.title,
          root.agent,
          root.model,
          count(*) as session_count,
          sum(s.cost) as cost,
          sum(s.tokens_input) as tokens_input,
          sum(s.tokens_output) as tokens_output,
          sum(s.tokens_reasoning) as tokens_reasoning,
          sum(s.tokens_cache_read) as tokens_cache_read,
          sum(s.tokens_cache_write) as tokens_cache_write,
          datetime(max(s.time_updated) / 1000, 'unixepoch', 'localtime') as updated
        from tree
        join session root on root.id = tree.group_id
        join session s on s.id = tree.id
        group by root.id
        order by max(s.time_updated) desc
        """,
        (parent_id,),
    ).fetchall()


def all_descendant_sessions(con: sqlite3.Connection, parent_id: str) -> list[sqlite3.Row]:
    return con.execute(
        """
        with recursive tree(depth, id) as (
          select 0, id from session where id = ?
          union all
          select tree.depth + 1, s.id
          from session s
          join tree on s.parent_id = tree.id
        )
        select
          tree.depth,
          s.id,
          s.parent_id,
          s.title,
          s.agent,
          s.model,
          s.cost,
          s.tokens_input,
          s.tokens_output,
          s.tokens_reasoning,
          s.tokens_cache_read,
          s.tokens_cache_write,
          datetime(s.time_updated / 1000, 'unixepoch', 'localtime') as updated
        from tree
        join session s on s.id = tree.id
        order by tree.depth, s.time_updated desc
        """,
        (parent_id,),
    ).fetchall()


def session_depths(con: sqlite3.Connection, parent_id: str) -> dict[str, int]:
    return {
        row["id"]: int(row["depth"])
        for row in con.execute(
            """
            with recursive tree(depth, id) as (
              select 0, id from session where id = ?
              union all
              select tree.depth + 1, s.id
              from session s
              join tree on s.parent_id = tree.id
            )
            select depth, id from tree
            """,
            (parent_id,),
        )
    }


def token_row(row: sqlite3.Row) -> list[str]:
    cache = int(row["tokens_cache_read"] or 0) + int(row["tokens_cache_write"] or 0)
    return [
        fmt_int(row["tokens_input"]),
        fmt_int(row["tokens_output"]),
        fmt_int(row["tokens_reasoning"]),
        fmt_int(cache),
        fmt_int(total_tokens(row)),
        money(row["cost"]),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report token/cost usage for an opencode session and its parent/subagent tree."
    )
    parser.add_argument("--db", help="Path to opencode sqlite database. Defaults to OPENCODE_DB or XDG data dir.")
    parser.add_argument("--session-id", help="Report this opencode session id and its parent tree.")
    parser.add_argument(
        "--current",
        action="store_true",
        help="Use current task session id from environment, falling back to the latest updated session.",
    )
    parser.add_argument(
        "--latest-parent",
        action="store_true",
        help="Use the latest updated parent session. This preserves the original parent-session report behavior.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON instead of tables.")
    parser.add_argument("--details", action="store_true", help="Also print every descendant session.")
    args = parser.parse_args()

    db = find_db(args.db)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row

    current_source = "latest parent session"
    current = None
    if args.session_id:
        current = session_by_id(con, args.session_id)
        if not current:
            raise SystemExit(f"session not found: {args.session_id}")
        current_source = "--session-id"
    elif args.current:
        current, env_key = current_session_from_env(con)
        if current:
            current_source = f"environment variable {env_key}"
        else:
            current = latest_session(con)
            current_source = "latest updated session fallback"
    elif args.latest_parent:
        current = latest_parent(con)
    else:
        current = latest_session(con)
        current_source = "latest updated session fallback"

    if not current:
        raise SystemExit("no session found")

    parent = root_for_session(con, current["id"])
    if not parent:
        raise SystemExit("no parent session found")

    total = parent_total(con, parent["id"])
    children = direct_child_reports(con, parent["id"])
    depths = session_depths(con, parent["id"])
    current_depth = depths.get(current["id"], 0)

    if args.json:
        payload = {
            "database": db,
            "selection": {
                "source": current_source,
                "current_session_id": current["id"],
                "current_short_id": short_id(current["id"]),
                "current_depth": current_depth,
            },
            "current_session": {
                "id": current["id"],
                "short_id": short_id(current["id"]),
                "parent_id": current["parent_id"],
                "title": current["title"],
                "agent": current["agent"],
                "model": model_label(current["model"]),
                "created": current["created"],
                "updated": current["updated"],
                "tokens": {
                    "input": current["tokens_input"] or 0,
                    "output": current["tokens_output"] or 0,
                    "reasoning": current["tokens_reasoning"] or 0,
                    "cache_read": current["tokens_cache_read"] or 0,
                    "cache_write": current["tokens_cache_write"] or 0,
                    "total": total_tokens(current),
                },
                "cost": current["cost"] or 0,
            },
            "parent": {
                "id": parent["id"],
                "short_id": short_id(parent["id"]),
                "title": parent["title"],
                "agent": parent["agent"],
                "model": model_label(parent["model"]),
                "created": parent["created"],
                "updated": parent["updated"],
            },
            "total": {
                "session_count": total["session_count"],
                "child_count": total["child_count"],
                "tokens": {
                    "input": total["tokens_input"] or 0,
                    "output": total["tokens_output"] or 0,
                    "reasoning": total["tokens_reasoning"] or 0,
                    "cache_read": total["tokens_cache_read"] or 0,
                    "cache_write": total["tokens_cache_write"] or 0,
                    "total": total_tokens(total),
                },
                "cost": total["cost"] or 0,
            },
            "subagents": [
                {
                    "id": row["id"],
                    "short_id": short_id(row["id"]),
                    "title": row["title"],
                    "agent": row["agent"],
                    "model": model_label(row["model"]),
                    "session_count": row["session_count"],
                    "tokens": {
                        "input": row["tokens_input"] or 0,
                        "output": row["tokens_output"] or 0,
                        "reasoning": row["tokens_reasoning"] or 0,
                        "cache_read": row["tokens_cache_read"] or 0,
                        "cache_write": row["tokens_cache_write"] or 0,
                        "total": total_tokens(row),
                    },
                    "cost": row["cost"] or 0,
                    "updated": row["updated"],
                }
                for row in children
            ],
        }
        if args.details:
            payload["sessions"] = [
                {
                    "depth": row["depth"],
                    "id": row["id"],
                    "short_id": short_id(row["id"]),
                    "parent_id": row["parent_id"],
                    "title": row["title"],
                    "agent": row["agent"],
                    "model": model_label(row["model"]),
                    "tokens": {
                        "input": row["tokens_input"] or 0,
                        "output": row["tokens_output"] or 0,
                        "reasoning": row["tokens_reasoning"] or 0,
                        "cache_read": row["tokens_cache_read"] or 0,
                        "cache_write": row["tokens_cache_write"] or 0,
                        "total": total_tokens(row),
                    },
                    "cost": row["cost"] or 0,
                    "updated": row["updated"],
                }
                for row in all_descendant_sessions(con, parent["id"])
            ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"DB: {db}")
    print(f"Selected current session: {current['title']} ({current['id']})")
    print(f"Selection source: {current_source}")
    print(f"Current depth under parent: {current_depth}")
    print(f"Parent: {parent['title']} ({parent['id']})")
    print(f"Updated: {parent['updated']}")
    print()

    print_table(
        ["Scope", "SID", "Input", "Output", "Reason", "Cache", "Total", "Cost", "Updated"],
        [["current session", short_id(current["id"]), *token_row(current), current["updated"]]],
    )
    print()

    print_table(
        ["Scope", "Sessions", "Subagents", "Input", "Output", "Reason", "Cache", "Total", "Cost"],
        [
            [
                "parent + recursive children",
                total["session_count"],
                total["child_count"],
                *token_row(total),
            ]
        ],
    )
    print()

    if children:
        print("Subagent aggregates")
        print_table(
            ["SID", "Title", "Agent", "Sessions", "Input", "Output", "Reason", "Cache", "Total", "Cost", "Updated"],
            [
                [
                    short_id(row["id"]),
                    (row["title"] or "")[:42],
                    row["agent"] or "",
                    row["session_count"],
                    *token_row(row),
                    row["updated"],
                ]
                for row in children
            ],
        )
    else:
        print("No child agent sessions found under this parent.")

    if args.details:
        print()
        print("All sessions in tree")
        print_table(
            ["Depth", "SID", "Title", "Agent", "Input", "Output", "Reason", "Cache", "Total", "Cost", "Updated"],
            [
                [
                    row["depth"],
                    short_id(row["id"]),
                    (("  " * row["depth"]) + (row["title"] or ""))[:46],
                    row["agent"] or "",
                    *token_row(row),
                    row["updated"],
                ]
                for row in all_descendant_sessions(con, parent["id"])
            ],
        )


if __name__ == "__main__":
    main()
