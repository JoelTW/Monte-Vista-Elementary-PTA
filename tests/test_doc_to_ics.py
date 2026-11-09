"""The PTA's yearly Google Doc (English section) becomes a standard .ics calendar."""
import sys
from datetime import date, datetime
from pathlib import Path

import pytest
from icalendar import Calendar

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import doc_to_ics  # noqa: E402

DOC = (Path(__file__).parent / "fixtures" / "pta-calendar-2025-26.txt").read_text()


@pytest.fixture(scope="module")
def events():
    return doc_to_ics.parse_doc(DOC, school_year_start=2025)


def find(events, title_part, start=None):
    hits = [e for e in events if title_part.lower() in e["title"].lower() and (start is None or e["start"] == start)]
    assert hits, f"no event matching {title_part!r} {start}"
    return hits[0]


def test_stops_at_the_spanish_section(events):
    assert not any("Calendario" in e["title"] or "Agosto" in e["title"] for e in events)
    assert all(e["start"].year in (2025, 2026) for e in events)


def test_timed_event_with_range_is_pm(events):
    e = find(events, "Park Meet Up")
    assert e["start"] == datetime(2025, 8, 11, 15, 0) and e["end"] == datetime(2025, 8, 11, 17, 0)
    assert e["title"] == "TK/K Park Meet Up"           # the time is removed from the title


def test_single_time_has_no_end_and_is_pm(events):
    e = find(events, "Teacher Meet & Greet")
    assert e["start"] == datetime(2025, 8, 12, 16, 0) and e["end"] is None


def test_all_day_event_has_a_date_not_a_time(events):
    e = find(events, "Flag Friday", date(2025, 8, 29))
    assert e["start"] == date(2025, 8, 29) and e["end"] is None and e["all_day"]


def test_date_range_is_inclusive_and_all_day(events):
    e = find(events, "Book Fair", date(2025, 10, 20))
    assert e["end"] == date(2025, 10, 24) and e["all_day"]


def test_range_crossing_the_new_year_gets_the_right_years(events):
    e = find(events, "Winter Break")
    assert e["start"] == date(2025, 12, 22) and e["end"] == date(2026, 1, 6)


def test_tbd_is_marked_tentative_and_removed_from_title(events):
    e = find(events, "Catalog Fundraiser")
    assert e["tentative"] and "TBD" not in e["title"] and e["start"] == date(2025, 9, 29) and e["end"] == date(2025, 10, 7)


def test_either_or_date_uses_the_first_and_is_tentative(events):
    e = find(events, "Site Beautification")
    assert e["start"] == datetime(2026, 4, 13, 14, 30) and e["tentative"]
    assert "4/14" in e["description"]


def test_zoom_meeting_gets_a_location(events):
    e = find(events, "PTA Meeting Zoom", datetime(2025, 12, 2, 16, 0))
    assert e["location"] == "Zoom"


def test_undated_indented_line_becomes_a_note_on_the_previous_event(events):
    e = find(events, "Back to School Night")
    assert "PTA/Title I Presentation 5:30 - 6:00" in e["description"]


def test_duplicate_listing_is_only_one_event(events):
    assert len([e for e in events if e["title"] == "Spring Break"]) == 1


def test_header_notes_are_not_events(events):
    assert not any("subject to change" in e["title"].lower() for e in events)


def test_ics_output_round_trips_and_has_a_timezone():
    ics = doc_to_ics.build_ics(DOC, school_year_start=2025)
    cal = Calendar.from_ical(ics)
    vevents = [c for c in cal.walk("VEVENT")]
    assert len(vevents) == 74          # 75 dated lines in the doc, minus Spring Break listed twice
    assert any(c.name == "VTIMEZONE" for c in cal.walk())
    flag = [v for v in vevents if "Flag Friday" in str(v["SUMMARY"])][0]
    assert not isinstance(flag["DTSTART"].dt, datetime)                       # all-day
    park = [v for v in vevents if "Park Meet Up" in str(v["SUMMARY"])][0]
    assert park["DTSTART"].dt.tzname() in ("PDT", "PST") and park["DTSTART"].dt.hour == 15
    uids = [str(v["UID"]) for v in vevents]
    assert len(uids) == len(set(uids))


def test_shift_moves_every_event_by_whole_weeks():
    ics = doc_to_ics.build_ics(DOC, school_year_start=2025, shift_days=364)
    cal = Calendar.from_ical(ics)
    park = [v for v in cal.walk("VEVENT") if "Park Meet Up" in str(v["SUMMARY"])][0]
    assert park["DTSTART"].dt.date() == date(2026, 8, 10) and park["DTSTART"].dt.weekday() == 0   # still a Monday
