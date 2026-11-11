"""Watch the PTA's yearly calendar Google Doc and report what changed, so a person can update the calendar.

    python scripts/doc_watch.py check  --state state --report report.md
    python scripts/doc_watch.py accept --state state

check   downloads the doc as plain text, reads its events with scripts/doc_to_ics.py, and compares them with the
        events at the last "accept". It writes a readable report and tells the workflow what happened.
accept  records the doc's latest events as the new baseline (the workflow runs this when the review issue is closed).

The state folder holds accepted.json (the baseline) and latest.json (the doc as of the last check). The first check has
no baseline, so it just saves one and reports nothing. The doc must stay shared as "Anyone with the link can view".
For a local test, add --source calendar.txt to read a saved text file instead of downloading.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from doc_to_ics import TZ, parse_doc_with_warnings

ROOT = Path(__file__).resolve().parent.parent
MONTH_LINE = re.compile(r"^\s*(january|february|march|april|may|june|july|august|september|october|november|december)\s*$", re.I | re.M)
FIELDS = ("title", "start", "end", "all_day", "tentative", "location", "description")


class DocProblem(Exception):
    """The doc could not be read. The message is written for a person."""


def doc_id_from_url(url):
    m = re.search(r"/document/d/([A-Za-z0-9_-]+)", url or "")
    if not m:
        raise DocProblem("There is no Google Doc address under calendar > doc_url in _data/site.yml.")
    return m.group(1)


def fetch_text(url):
    export = "https://docs.google.com/document/d/%s/export?format=txt" % doc_id_from_url(url)
    req = urllib.request.Request(export, headers={"User-Agent": "monte-vista-pta-calendar-watch"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            kind = r.headers.get("Content-Type", "")
            body = r.read().decode("utf-8", "replace")
    except Exception as e:  # network trouble, 404 or 403 when the doc is not shared
        raise DocProblem("The doc could not be downloaded (%s). Check it is still shared as \"Anyone with the link can view\"." % e)
    if "text/plain" not in kind:
        raise DocProblem("Google sent a web page instead of the doc's text. The doc is probably no longer shared as \"Anyone with the link can view\".")
    return body.lstrip("﻿")


def school_year_start(today, override=None):
    if override:
        return int(override)
    return today.year if today.month >= 8 else today.year - 1


def read_events(text, year):
    if not MONTH_LINE.search(text):
        raise DocProblem("The doc downloaded, but it has no month headings (August, September, ...), so it was not read. Has its layout changed?")
    events, warnings = parse_doc_with_warnings(text, year)
    if not events:
        raise DocProblem("The doc has month headings but no events could be read from it. Has its layout changed?")
    out = []
    for e in events:
        item = {k: (v.isoformat() if isinstance(v, (date, datetime)) else v) for k, v in e.items() if k in FIELDS}
        item["end"] = item.get("end") or None
        item["location"] = item.get("location") or ""
        item["description"] = item.get("description") or ""
        item["id"] = hashlib.sha1(("%s|%s|%s" % (item["title"], item["start"], item["end"])).encode()).hexdigest()[:20]
        out.append(item)
    out.sort(key=lambda x: (x["start"], x["title"]))
    return out, warnings


def when(e):
    start = datetime.fromisoformat(e["start"])
    if e["all_day"]:
        s = start.strftime("%a %b %-d")
        if e["end"] and e["end"] != e["start"]:
            s += " to " + datetime.fromisoformat(e["end"]).strftime("%a %b %-d")
        return s
    s = start.strftime("%a %b %-d, %-I:%M %p")
    if e["end"]:
        s += " to " + datetime.fromisoformat(e["end"]).strftime("%-I:%M %p")
    return s


def label(e):
    return "**%s**, %s%s" % (e["title"], when(e), " (tentative)" if e["tentative"] else "")


def diff(old, new):
    """Return (added, removed, changed). changed is a list of (old, new, what)."""
    old_ids, new_ids = {e["id"] for e in old}, {e["id"] for e in new}
    added = [e for e in new if e["id"] not in old_ids]
    removed = [e for e in old if e["id"] not in new_ids]
    changed = []
    for r in list(removed):
        match = next((a for a in added if a["title"].lower() == r["title"].lower()), None)
        what = "moved or retimed"
        if not match:
            match = next((a for a in added if a["start"] == r["start"]), None)
            what = "renamed"
        if match:
            removed.remove(r)
            added.remove(match)
            changed.append((r, match, what))
    # same event, different notes or place: the id is unchanged, so look at the other fields
    old_by_id = {e["id"]: e for e in old}
    for e in new:
        o = old_by_id.get(e["id"])
        if o and any(o[k] != e[k] for k in ("tentative", "location", "description")):
            changed.append((o, e, "details changed"))
    return added, removed, changed


def new_warnings(warnings, accepted_warnings):
    """Warnings the baseline did not already have (ignoring line numbers, which move when the doc is edited)."""
    plain = lambda w: re.sub(r"^Line \d+:\s*", "", w)
    known = {plain(w) for w in accepted_warnings}
    return [w for w in warnings if plain(w) not in known]


def report(added, removed, changed, warnings, doc_url):
    lines = ["The PTA calendar doc has changed since the Google Calendar was last updated from it.", ""]
    lines.append("**%d new, %d changed, %d removed.**" % (len(added), len(changed), len(removed)))
    if added:
        lines += ["", "### New"] + ["- " + label(e) for e in added]
    if changed:
        lines += ["", "### Changed"] + ["- %s (%s)\n  was: %s" % (label(n), what, label(o)) for o, n, what in changed]
    if removed:
        lines += ["", "### Removed"] + ["- " + label(e) for e in removed]
    if warnings:
        lines += ["", "### Please check", "The reader had to guess about these new lines in the doc:"] + ["- " + w for w in warnings]
    lines += [
        "", "### What to do",
        "1. Open the [calendar doc](%s) and update the PTA Google Calendar to match the lists above (add, change or delete those events)." % doc_url,
        "2. **Close this issue** when the calendar is up to date. That records the doc as reviewed, so the next change starts a fresh issue.",
        "", "If the doc changes again before you close this, this issue is updated and gets a new comment.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(**values):
    path = os.environ.get("GITHUB_OUTPUT")
    for k, v in values.items():
        print("%s=%s" % (k, v))
        if path:
            with open(path, "a") as f:
                f.write("%s=%s\n" % (k, v))


def load(path):
    return json.loads(path.read_text()) if path.exists() else None


def cmd_check(args):
    state = Path(args.state)
    state.mkdir(parents=True, exist_ok=True)
    cfg = (yaml.safe_load((ROOT / "_data" / "site.yml").read_text()) or {}).get("calendar") or {}
    doc_url = args.doc_url or cfg.get("doc_url") or ""
    today = datetime.now(ZoneInfo(TZ)).date()
    try:
        text = Path(args.source).read_text(encoding="utf-8").lstrip("﻿") if args.source else fetch_text(doc_url)
        events, warnings = read_events(text, school_year_start(today, args.year or cfg.get("doc_school_year")))
    except DocProblem as e:
        Path(args.report).write_text("The check of the calendar doc could not finish.\n\n%s\n\nThis issue closes by itself once a check works again.\n" % e)
        write_outputs(status="problem", latest_changed="false")
        return
    previous = load(state / "latest.json")
    latest = {"events": events, "warnings": warnings}
    (state / "latest.json").write_text(json.dumps(latest, indent=1) + "\n")
    accepted = load(state / "accepted.json")
    if accepted is None:
        (state / "accepted.json").write_text(json.dumps(latest, indent=1) + "\n")
        write_outputs(status="seeded", latest_changed="false")
        return
    added, removed, changed = diff(accepted["events"], events)
    if not (added or removed or changed):
        write_outputs(status="unchanged", latest_changed="false")
        return
    fresh = new_warnings(warnings, accepted["warnings"])
    Path(args.report).write_text(report(added, removed, changed, fresh, doc_url))
    write_outputs(status="changed", latest_changed="true" if (previous or {}).get("events") != events else "false")


def cmd_accept(args):
    state = Path(args.state)
    latest = load(state / "latest.json")
    if latest is None:
        print("Nothing to accept yet.")
        return
    (state / "accepted.json").write_text(json.dumps(latest, indent=1) + "\n")
    print("Recorded the latest doc as reviewed.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("command", choices=["check", "accept"])
    ap.add_argument("--state", required=True, help="folder for accepted.json and latest.json")
    ap.add_argument("--report", default="report.md", help="where check writes the report")
    ap.add_argument("--source", help="read this saved text file instead of downloading the doc")
    ap.add_argument("--doc-url", help="override calendar > doc_url from _data/site.yml")
    ap.add_argument("--year", help="year the school year starts in (default: worked out from today's date)")
    args = ap.parse_args(argv)
    (cmd_check if args.command == "check" else cmd_accept)(args)


if __name__ == "__main__":
    main()
