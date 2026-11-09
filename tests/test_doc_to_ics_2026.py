"""The 2026-27 doc has quirks the 2025-26 one did not: missing colons, a lost date, "4:00p" times, nested items."""
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import doc_to_ics  # noqa: E402

DOC = (Path(__file__).parent / "fixtures" / "pta-calendar-2026-27.txt").read_text()


@pytest.fixture(scope="module")
def parsed():
    return doc_to_ics.parse_doc_with_warnings(DOC, school_year_start=2026)


@pytest.fixture(scope="module")
def events(parsed):
    return parsed[0]


@pytest.fixture(scope="module")
def warnings(parsed):
    return parsed[1]


def find(events, title_part, start=None):
    hits = [e for e in events if title_part.lower() in e["title"].lower() and (start is None or e["start"] == start)]
    assert hits, f"no event matching {title_part!r} {start}"
    return hits[0]


def test_date_without_a_colon_is_still_an_event(events):
    e = find(events, "Dine-Out Night - Chipotle")
    assert e["start"] == date(2026, 10, 13)
    assert find(events, "Friday Flag", date(2027, 4, 30))


def test_dash_instead_of_a_colon_and_tbd(events):
    e = find(events, "Dine Out", date(2027, 4, 22))
    assert e["title"] == "Dine Out" and e["tentative"]


def test_date_range_with_dashes_still_works(events):
    assert find(events, "Book Fair", date(2026, 10, 19))["end"] == date(2026, 10, 23)


def test_p_after_a_time_means_pm(events):
    e = find(events, "PTA Meeting on Zoom", datetime(2026, 9, 1, 16, 0))
    assert e["location"] == "Zoom" and e["title"] == "PTA Meeting on Zoom"


def test_morning_time_stays_am_and_noon_end_works(events):
    first_day = find(events, "First Day of School")
    assert first_day["start"] == datetime(2026, 8, 12, 8, 15)
    site = find(events, "Site Beautification", datetime(2027, 4, 10, 8, 0))
    assert site["end"] == datetime(2027, 4, 10, 12, 0) and site["tentative"]


def test_undated_line_with_a_time_becomes_an_event_on_the_date_above(events, warnings):
    e = find(events, "Back to School Night")
    assert e["start"] == datetime(2026, 8, 20, 17, 30) and e["end"] == datetime(2026, 8, 20, 19, 0)
    assert "assumed" in e["description"].lower()
    assert any("Back to School Night" in w for w in warnings)
    assert "PTA/Title I Presentation 5:30 - 6:00" in e["description"]      # still a note on that event


def test_indented_sub_items_are_named_after_their_parent(events):
    assert find(events, "Penguin Patch in MPR: Set Up")["start"] == date(2026, 11, 30)
    sales = find(events, "Penguin Patch in MPR: Grade Level Sales")
    assert sales["start"] == date(2026, 12, 1) and sales["end"] == date(2026, 12, 7)


def test_a_line_that_is_not_understood_is_reported_not_silently_attached(events, warnings):
    assert any("1130- Penguin Patch Set-up" in w for w in warnings)
    fall = find(events, "Fall Break")
    assert "1130" not in fall["description"]
    assert any("LAST DAY OF SCHOOL" in w for w in warnings)


def test_zoom_meetings_at_4_are_all_pm(events):
    meetings = [e for e in events if "PTA Meeting" in e["title"] and "Zoom" in e["title"]]
    assert len(meetings) >= 8
    assert all(e["start"].hour == 16 for e in meetings if isinstance(e["start"], datetime))


def test_event_count_matches_the_documents_dated_lines(events):
    # 79 lines start with a date, minus Spring Break listed twice, plus the Back to School Night that lost its date
    assert len(events) == 79


def test_winter_break_crosses_the_new_year(events):
    e = find(events, "Winter Break")
    assert e["start"] == date(2026, 12, 21) and e["end"] == date(2027, 1, 6)


def test_everything_falls_in_the_school_year(events):
    starts = [e["start"].date() if isinstance(e["start"], datetime) else e["start"] for e in events]
    assert min(starts) == date(2026, 8, 10) and max(starts) == date(2027, 6, 3)


def test_cli_prints_what_to_check(tmp_path, capsys):
    doc = tmp_path / "d.txt"
    doc.write_text(DOC)
    out = tmp_path / "o.ics"
    doc_to_ics.main([str(doc), "--year", "2026", "-o", str(out)])
    err = capsys.readouterr().err
    assert "Please check" in err and "Back to School Night" in err and out.exists()
