"""Read the PTA's calendar feed (.ics) and write the events the website shows.

Where the feed comes from, in order:
  1. the CALENDAR_ICS_URL environment variable,
  2. calendar.ical_url in _data/site.yml (the public iCal address of the Google Calendar),
  3. calendar/sample.ics in this repository (sample data, used until a real calendar is connected).

Output (same content, two places): _data/calendar.json (for the page templates) and
assets/data/events.json (for the month calendar in the browser).

Run from the repository root:  python scripts/sync_calendar.py
The nightly GitHub Action runs this before it builds the site, so the site follows the calendar.
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import recurring_ical_events
import yaml
from icalendar import Calendar

ROOT = Path(__file__).resolve().parent.parent
TZ = "America/Los_Angeles"
THUMBS = ["t1", "t2", "t3", "t4"]
DEFAULT_EMOJI = "🎉"


def load_source(src):
    """Return the raw calendar bytes from a web address or a file path."""
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src.replace("webcal://", "https://"), headers={"User-Agent": "monte-vista-pta-site-sync"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    return Path(src).read_bytes()


def resolve_source(site_yml, sample, env=None):
    env = os.environ if env is None else env
    if env.get("CALENDAR_ICS_URL"):
        return env["CALENDAR_ICS_URL"].strip()
    try:
        url = ((yaml.safe_load(Path(site_yml).read_text()) or {}).get("calendar") or {}).get("ical_url")
    except FileNotFoundError:
        url = None
    return str(url).strip() if url and str(url).strip() else str(sample)


def _add_months(d, n):
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    return date(y, m + 1, 1)


def _clean_text(raw):
    """Calendar descriptions may contain HTML. Return (plain text, first link or '')."""
    raw = (raw or "").replace("\\n", "\n")
    links = re.findall(r'href="(https?://[^"]+)"', raw, flags=re.I)
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    raw = re.sub(r"</(p|div|li|ul|ol)>", "\n", raw, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    if not links:
        links = re.findall(r"https?://[^\s<>\"]+", text)
    return text, (links[0] if links else "")


def _clock(dt):
    h = dt.hour % 12 or 12
    return "%d:%02d %s" % (h, dt.minute, "AM" if dt.hour < 12 else "PM")


def _time_label(start, end):
    if end is None or end == start:
        return _clock(start)
    a, b = _clock(start), _clock(end)
    if a[-2:] == b[-2:] and start.date() == end.date():
        return "%s-%s" % (a[:-3], b)
    return "%s-%s" % (a, b)


def _utc(dt):
    """Clock time in the form calendar apps take in an add-to-calendar link: 20261114T010000Z."""
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _icon(title, icons):
    low = title.lower()
    for rule in icons or []:
        if any(w.lower() in low for w in rule.get("words", [])):
            return rule.get("emoji") or DEFAULT_EMOJI, rule.get("thumb") or THUMBS[0]
    return DEFAULT_EMOJI, THUMBS[int(hashlib.sha1(title.encode()).hexdigest(), 16) % len(THUMBS)]


def build_events(ics_bytes, today, months_ahead=12, icons=None, tz_name=TZ):
    """Return the events from the start of this month to months_ahead later, one dict per occurrence."""
    if b"BEGIN:VCALENDAR" not in ics_bytes[:2000] and b"BEGIN:VCALENDAR" not in ics_bytes:
        raise ValueError("That is not a calendar file (no BEGIN:VCALENDAR). Is the calendar address public?")
    tz = ZoneInfo(tz_name)
    cal = Calendar.from_ical(ics_bytes)
    first = today.replace(day=1)
    window = (datetime(first.year, first.month, 1, tzinfo=tz), datetime.combine(_add_months(first, months_ahead), datetime.min.time(), tzinfo=tz))
    out = []
    for ev in recurring_ical_events.of(cal).between(*window):
        if str(ev.get("STATUS", "")).upper() == "CANCELLED":
            continue
        start = ev["DTSTART"].dt
        all_day = not isinstance(start, datetime)
        end = ev["DTEND"].dt if "DTEND" in ev else None
        if all_day:
            last = (end - timedelta(days=1)) if end else start                  # all-day DTEND is the day AFTER the last day
            last = max(last, start)
            d0, d1, label, s_iso = start, last, "All day", start.isoformat()
            utc_start = utc_end = ""
        else:
            s = start.astimezone(tz) if start.tzinfo else start.replace(tzinfo=tz)
            e = (end.astimezone(tz) if end.tzinfo else end.replace(tzinfo=tz)) if isinstance(end, datetime) else None
            d0, d1 = s.date(), (e.date() if e else s.date())
            label, s_iso = _time_label(s, e), s.strftime("%Y-%m-%dT%H:%M")
            utc_start, utc_end = _utc(s), _utc(e if e and e > s else s + timedelta(hours=1))   # no end time: assume one hour
        title = re.sub(r"\s+", " ", str(ev.get("SUMMARY", "")).strip()) or "(untitled event)"
        desc, url = _clean_text(str(ev.get("DESCRIPTION", "")))
        location = re.sub(r"\s+", " ", str(ev.get("LOCATION", "")).replace("\\,", ",")).strip()
        place = location.split(",")[0].strip() if location.count(",") >= 2 else location
        first_line = next((ln.strip() for ln in desc.splitlines() if ln.strip() and not re.match(r"^https?://\S+$", ln.strip())), "")
        blurb = first_line if len(first_line) <= 140 else first_line[:137].rstrip() + "..."
        emoji, thumb = _icon(title, icons)
        uid = str(ev.get("UID", title))
        out.append({
            "id": hashlib.sha1(("%s|%s" % (uid, s_iso)).encode()).hexdigest()[:10],
            "title": title, "date": d0.isoformat(), "end_date": d1.isoformat() if d1 > d0 else "",
            "time": label, "all_day": all_day, "start_utc": utc_start, "end_utc": utc_end, "place": place, "location": location,
            "blurb": blurb, "description": desc, "url": url, "emoji": emoji, "thumb": thumb,
            "tentative": str(ev.get("STATUS", "")).upper() == "TENTATIVE" or bool(re.search(r"\bTBD\b", title, re.I)),
            "_sort": (d0.isoformat(), 0 if all_day else 1, s_iso),
        })
    out.sort(key=lambda e: e["_sort"])
    for e in out:
        del e["_sort"]
    return out


def write_outputs(events, *paths):
    text = json.dumps(events, ensure_ascii=False, indent=1) + "\n"
    for p in paths:
        p = Path(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", help="calendar web address or file (default: see the order above)")
    ap.add_argument("--today", help="pretend today is YYYY-MM-DD (for testing)")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)
    root = Path(args.root)
    site = yaml.safe_load((root / "_data" / "site.yml").read_text()) or {}
    cfg = site.get("calendar") or {}
    src = args.source or resolve_source(root / "_data" / "site.yml", root / "calendar" / "sample.ics")
    today = date.fromisoformat(args.today) if args.today else datetime.now(ZoneInfo(TZ)).date()
    icons_path = root / "_data" / "event_icons.yml"
    icons = yaml.safe_load(icons_path.read_text()) if icons_path.exists() else []
    try:
        events = build_events(load_source(src), today, int(cfg.get("months_ahead") or 12), icons)
    except Exception as exc:
        print("Calendar sync FAILED (the site keeps its last good data): %s" % exc, file=sys.stderr)
        return 1
    write_outputs(events, root / "_data" / "calendar.json", root / "assets" / "data" / "events.json")
    print("Calendar sync: %d events from %s" % (len(events), "the sample file" if src.endswith("sample.ics") else re.sub(r"(/ical/)[^/]+", r"\1...", src)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
