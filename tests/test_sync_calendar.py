"""A calendar feed (.ics) becomes the list of events the site shows."""
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import sync_calendar as sc  # noqa: E402

TODAY = date(2026, 11, 8)


def ics(*events):
    return ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\n" + "".join(
        "BEGIN:VEVENT\r\n" + "\r\n".join(e.strip().splitlines()) + "\r\nEND:VEVENT\r\n" for e in events
    ) + "END:VCALENDAR\r\n").encode()


def build(*events, **kw):
    return sc.build_events(ics(*events), today=kw.pop("today", TODAY), **kw)


def one(*events, **kw):
    out = build(*events, **kw)
    assert len(out) == 1, out
    return out[0]


def test_utc_timed_event_is_shown_in_pacific_time():
    e = one("UID:a\nSUMMARY:Fall Festival\nDTSTART:20261114T010000Z\nDTEND:20261114T040000Z")  # 5-8 PM on the 13th in PST
    assert e["date"] == "2026-11-13" and e["time"] == "5:00-8:00 PM" and e["all_day"] is False and e["end_date"] == ""


def test_time_range_across_noon_shows_both_periods():
    e = one("UID:a\nSUMMARY:Lunch\nDTSTART;TZID=America/Los_Angeles:20261120T113000\nDTEND;TZID=America/Los_Angeles:20261120T130000")
    assert e["time"] == "11:30 AM-1:00 PM"


def test_timed_event_without_an_end_shows_only_the_start():
    e = one("UID:a\nSUMMARY:Meeting\nDTSTART;TZID=America/Los_Angeles:20261124T160000")
    assert e["time"] == "4:00 PM"


def test_all_day_event():
    e = one("UID:a\nSUMMARY:Flag Friday\nDTSTART;VALUE=DATE:20261120\nDTEND;VALUE=DATE:20261121")
    assert e["date"] == "2026-11-20" and e["end_date"] == "" and e["all_day"] and e["time"] == "All day"


def test_multi_day_all_day_event_end_is_the_last_day_not_the_day_after():
    e = one("UID:a\nSUMMARY:Book Fair\nDTSTART;VALUE=DATE:20261207\nDTEND;VALUE=DATE:20261212")
    assert e["date"] == "2026-12-07" and e["end_date"] == "2026-12-11"


def test_overnight_event_ends_the_next_day():
    e = one("UID:a\nSUMMARY:Campout\nDTSTART;TZID=America/Los_Angeles:20261127T180000\nDTEND;TZID=America/Los_Angeles:20261128T090000")
    assert e["date"] == "2026-11-27" and e["end_date"] == "2026-11-28" and e["time"] == "6:00 PM-9:00 AM"


def test_weekly_series_keeps_local_time_across_the_end_of_daylight_saving():
    out = build("UID:s\nSUMMARY:Club\nDTSTART;TZID=America/Los_Angeles:20261027T180000\nDTEND;TZID=America/Los_Angeles:20261027T193000\nRRULE:FREQ=WEEKLY;COUNT=4")
    assert [e["date"] for e in out] == ["2026-11-03", "2026-11-10", "2026-11-17"]   # Oct 27 is before the window (starts Nov 1)
    assert {e["time"] for e in out} == {"6:00-7:30 PM"}       # DST ended Nov 1; still 6 PM local
    assert len({e["id"] for e in out}) == len(out)            # every occurrence has its own id


def test_deleted_occurrence_of_a_series_is_left_out():
    out = build("UID:s\nSUMMARY:Club\nDTSTART;TZID=America/Los_Angeles:20261110T180000\nRRULE:FREQ=WEEKLY;COUNT=3\nEXDATE;TZID=America/Los_Angeles:20261117T180000")
    assert [e["date"] for e in out] == ["2026-11-10", "2026-11-24"]


def test_cancelled_event_is_left_out():
    assert build("UID:a\nSUMMARY:Gone\nSTATUS:CANCELLED\nDTSTART;VALUE=DATE:20261120") == []


def test_events_outside_the_window_are_left_out_and_this_months_past_days_stay():
    out = build(
        "UID:old\nSUMMARY:Last month\nDTSTART;VALUE=DATE:20261030",
        "UID:early\nSUMMARY:Earlier this month\nDTSTART;VALUE=DATE:20261102",
        "UID:far\nSUMMARY:Too far away\nDTSTART;VALUE=DATE:20271215",
        months_ahead=12,
    )
    assert [e["title"] for e in out] == ["Earlier this month"]      # kept so the month grid still shows it


def test_events_are_sorted_by_date_then_time():
    out = build(
        "UID:3\nSUMMARY:C\nDTSTART;TZID=America/Los_Angeles:20261120T180000",
        "UID:1\nSUMMARY:A\nDTSTART;VALUE=DATE:20261120",
        "UID:2\nSUMMARY:B\nDTSTART;TZID=America/Los_Angeles:20261120T090000",
        "UID:0\nSUMMARY:First\nDTSTART;VALUE=DATE:20261112",
    )
    assert [e["title"] for e in out] == ["First", "A", "B", "C"]          # all-day first on a given day


def test_google_style_html_description_becomes_plain_text_with_a_link():
    e = one('UID:a\nSUMMARY:Dine Out\nDTSTART;VALUE=DATE:20261120\nDESCRIPTION:Bring a flyer<br><b>Show it</b> at the register.<br>Menu: <a href="https://example.com/menu">our menu</a>')
    assert "<" not in e["description"] and "Show it at the register." in e["description"]
    assert e["url"] == "https://example.com/menu"
    assert e["blurb"] == "Bring a flyer"


def test_long_address_location_is_shortened_to_the_place_name():
    e = one("UID:a\nSUMMARY:Night\nDTSTART;VALUE=DATE:20261120\nLOCATION:Monte Vista Elementary School\\, 1720 Monte Vista Dr\\, Vista\\, CA 92084\\, USA")
    assert e["place"] == "Monte Vista Elementary School" and "1720" in e["location"]


def test_tentative_status_or_tbd_in_the_title_is_flagged():
    a = one("UID:a\nSUMMARY:Play\nSTATUS:TENTATIVE\nDTSTART;VALUE=DATE:20261120")
    b = one("UID:b\nSUMMARY:Play - TBD\nDTSTART;VALUE=DATE:20261120")
    assert a["tentative"] and b["tentative"]


def test_keywords_pick_an_emoji_and_unknown_titles_still_get_one():
    icons = [{"words": ["book fair"], "emoji": "📚", "thumb": "t4"}]
    assert one("UID:a\nSUMMARY:Winter Book Fair\nDTSTART;VALUE=DATE:20261120", icons=icons)["emoji"] == "📚"
    other = one("UID:b\nSUMMARY:Something new\nDTSTART;VALUE=DATE:20261120", icons=icons)
    assert other["emoji"] and other["thumb"] in ("t1", "t2", "t3", "t4")


def test_missing_title_gets_a_placeholder_and_markup_is_kept_as_text_for_the_page_to_escape():
    assert one("UID:a\nDTSTART;VALUE=DATE:20261120")["title"] == "(untitled event)"
    assert one("UID:b\nSUMMARY:<b>Hi</b> & friends\nDTSTART;VALUE=DATE:20261120")["title"] == "<b>Hi</b> & friends"


def test_rejects_something_that_is_not_a_calendar():
    with pytest.raises(ValueError):
        sc.build_events(b"<html>Sign in to continue</html>", today=TODAY)


def test_outputs_are_written_for_jekyll_and_for_the_calendar_script(tmp_path):
    events = build("UID:a\nSUMMARY:Hi\nDTSTART;VALUE=DATE:20261120")
    sc.write_outputs(events, tmp_path / "_data" / "calendar.json", tmp_path / "assets" / "data" / "events.json")
    a = json.loads((tmp_path / "_data" / "calendar.json").read_text())
    b = json.loads((tmp_path / "assets" / "data" / "events.json").read_text())
    assert a == b == events


def test_source_comes_from_the_environment_then_the_site_settings_then_the_sample(tmp_path):
    site = tmp_path / "site.yml"
    site.write_text("calendar:\n  ical_url: https://example.com/a.ics\n")
    seed = tmp_path / "seed.ics"
    assert sc.resolve_source(site, seed, env={"CALENDAR_ICS_URL": "https://example.com/env.ics"}) == "https://example.com/env.ics"
    assert sc.resolve_source(site, seed, env={}) == "https://example.com/a.ics"
    site.write_text("calendar:\n  ical_url: ''\n")
    assert sc.resolve_source(site, seed, env={}) == str(seed)


def test_load_source_reads_a_local_file(tmp_path):
    f = tmp_path / "x.ics"
    f.write_bytes(ics("UID:a\nSUMMARY:Hi\nDTSTART;VALUE=DATE:20261120"))
    assert b"BEGIN:VCALENDAR" in sc.load_source(str(f))


def test_data_file_loads_the_way_jekyll_loads_it(tmp_path):
    """Jekyll 3 reads _data/*.json with a YAML parser, which rejects \\ud83c-style emoji escapes."""
    import yaml
    events = build('UID:a\nSUMMARY:Fall "Festival" \\\\ \U0001F383 & more\nDTSTART;VALUE=DATE:20261120\nDESCRIPTION:Line one\\nLine two')
    out = tmp_path / "calendar.json"
    sc.write_outputs(events, out)
    assert "\\ud83c" not in out.read_text().lower()
    assert yaml.safe_load(out.read_text()) == events
