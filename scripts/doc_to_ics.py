"""Turn the PTA's yearly calendar Google Doc into a calendar file (.ics) that Google Calendar can import.

The doc is plain month-by-month text such as:

    August
        8/11: TK/K Park Meet Up (3:00 - 5:00)
        9/29 - 10/7: Catalog Fundraiser - TBD
        4/13 or 4/14: Site Beautification (2:30) - TBD on date

Get the text with File > Download > Plain text (.txt) in Google Docs, then run:

    python scripts/doc_to_ics.py calendar.txt --year 2026 -o pta-calendar.ics

--year is the year the school year STARTS in (August 2026 for the 2026-27 year). Only the English section is read
(it stops at a line starting "Calendario"). Import the result in Google Calendar: Settings > Import & export.
Check the result: times without AM/PM are guessed (1 to 6 = PM, 7 to 11 = AM, or PM after a PM start).
"""
import argparse
import hashlib
import re
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

TZ = "America/Los_Angeles"
START_MONTH = 8  # a school year starts in August
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
MONTH_HEADER = re.compile(r"^\s*(%s)\s*$" % "|".join(MONTHS), re.I)
DASH = r"(?:-|–|—|to)"
EVENT_LINE = re.compile(
    r"^\s*(\d{1,2})/(\d{1,2})\s*(?:%s\s*(\d{1,2})/(\d{1,2}))?\s*(?:or\s+(\d{1,2})/(\d{1,2}))?\s*:\s*(.+?)\s*$" % DASH
)
TBD = re.compile(r"\s*-?\s*\bTBD\b.*$", re.I)
NOTE = re.compile(r"\*(.+?)\*")
TIME_PAREN = re.compile(r"\(\s*(\d{1,2}):(\d{2})(?:\s*-\s*(\d{1,2}):(\d{2}))?\s*\)")
TIME_TRAIL = re.compile(r"\s(\d{1,2}):(\d{2})(?:\s*-\s*(\d{1,2}):(\d{2}))?\s*$")
TYPOS = {"MeetingZoom": "Meeting Zoom"}


def _year_for(month, start_year):
    return start_year if month >= START_MONTH else start_year + 1


def _to_24h(h1, m1, h2, m2):
    """Guess AM/PM for school-day times: 1-6 and 12 are PM, 7-11 are AM unless the range starts in the PM."""
    start_pm = h1 == 12 or h1 <= 6
    s = (h1 if h1 == 12 else h1 + 12 if start_pm else h1, m1)
    if h2 is None:
        return s, None
    if start_pm:
        e_h = h2 if h2 == 12 else h2 + 12
    else:
        e_h = h2 + 12 if h2 < h1 and h2 != 12 else h2
    return s, (e_h, m2)


def parse_doc(text, school_year_start):
    """Return a list of event dicts: title, start, end, all_day, tentative, location, description.

    start/end are date objects for all-day events (end is the inclusive last day, or None) and naive local
    datetimes for timed events (end may be None).
    """
    events, seen, last, in_month = [], set(), None, False
    for raw in text.splitlines():
        if re.match(r"^\s*calendario\b", raw, re.I):
            break
        if MONTH_HEADER.match(raw):
            in_month, last = True, None
            continue
        if not in_month or not raw.strip():
            continue
        m = EVENT_LINE.match(raw)
        if not m:
            if last is not None:  # an indented line with no date: a note about the event above it
                last["notes"].append(raw.strip())
            continue
        m1, d1, m2, d2, alt_m, alt_d, rest = m.groups()
        for wrong, right in TYPOS.items():
            rest = rest.replace(wrong, right)
        notes, tentative = [], False
        for note in NOTE.findall(rest):
            notes.append(note.strip())
        rest = NOTE.sub("", rest)
        if TBD.search(rest):
            tentative = True
            rest = TBD.sub("", rest)
        times = None
        tm = TIME_PAREN.search(rest) or TIME_TRAIL.search(rest)
        if tm:
            h1, mi1, h2, mi2 = tm.groups()
            times = _to_24h(int(h1), int(mi1), int(h2) if h2 else None, int(mi2) if mi2 else None)
            rest = rest[: tm.start()] + rest[tm.end():]
        title = re.sub(r"\s+", " ", rest).strip(" -–—,")
        start_d = date(_year_for(int(m1), school_year_start), int(m1), int(d1))
        end_d = date(_year_for(int(m2), school_year_start), int(m2), int(d2)) if m2 else None
        if alt_m:
            tentative = True
            notes.append("Date to be confirmed: %s/%s or %s/%s." % (m1, d1, alt_m, alt_d))
        if tentative and not alt_m:
            notes.append("Date or time to be confirmed.")
        location = "Zoom" if re.search(r"\bZoom\b", title) else None
        for pattern, place in ((r"\bin (?:the )?Library\b", "Library"), (r"\bin (?:the )?MPR\b", "MPR")):
            if re.search(pattern, title):
                location = place
        if times:
            (sh, sm), end_t = times
            start = datetime(start_d.year, start_d.month, start_d.day, sh, sm)
            end = datetime(start_d.year, start_d.month, start_d.day, end_t[0], end_t[1]) if end_t else None
            all_day = False
        else:
            start, end, all_day = start_d, end_d, True
        key = (title.lower(), start, end)
        if key in seen:  # e.g. Spring Break is listed under both March and April
            last = None
            continue
        seen.add(key)
        last = {"title": title, "start": start, "end": end, "all_day": all_day, "tentative": tentative,
                "location": location, "notes": notes}
        events.append(last)
    for e in events:
        e["description"] = "\n".join(e.pop("notes"))
    return events


def _shift(value, days):
    return value + timedelta(days=days) if value is not None else None


def build_ics(text, school_year_start, shift_days=0, name="Monte Vista PTA"):
    tz = ZoneInfo(TZ)
    cal = Calendar()
    cal.add("prodid", "-//Monte Vista PTA//Calendar from Google Doc//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", name)
    cal.add("x-wr-timezone", TZ)
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    for e in parse_doc(text, school_year_start):
        start, end = _shift(e["start"], shift_days), _shift(e["end"], shift_days)
        ev = Event()
        digest = hashlib.sha1(("%s|%s|%s" % (e["title"], start, end)).encode()).hexdigest()[:20]
        ev.add("uid", digest + "@montevistapta.org")
        ev.add("dtstamp", stamp)
        ev.add("summary", e["title"])
        if e["all_day"]:
            ev.add("dtstart", start)
            ev.add("dtend", (end or start) + timedelta(days=1))  # iCalendar's all-day end is exclusive
        else:
            ev.add("dtstart", start.replace(tzinfo=tz))
            if end:
                ev.add("dtend", end.replace(tzinfo=tz))
        if e["location"]:
            ev.add("location", e["location"])
        if e["description"]:
            ev.add("description", e["description"])
        if e["tentative"]:
            ev.add("status", "TENTATIVE")
        cal.add_component(ev)
    cal.add_missing_timezones()
    return cal.to_ical().decode()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("doc", help="the calendar doc saved as plain text")
    ap.add_argument("--year", type=int, required=True, help="year the school year starts in (August)")
    ap.add_argument("--shift-days", type=int, default=0, help="move every event by this many days (364 = 52 weeks, same weekdays)")
    ap.add_argument("--name", default="Monte Vista PTA")
    ap.add_argument("-o", "--output", help="write here instead of printing")
    args = ap.parse_args(argv)
    text = open(args.doc, encoding="utf-8").read()
    ics = build_ics(text, args.year, args.shift_days, args.name)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            f.write(ics)
        print("wrote %s (%d events)" % (args.output, ics.count("BEGIN:VEVENT")), file=sys.stderr)
    else:
        sys.stdout.write(ics)


if __name__ == "__main__":
    main()
