# Events and the calendar

The site shows events in two ways, and they work together.

## 1. Event cards (the small cards on the home page and the list on the Events page)
Each event is one small file in `_events/` (or one entry in the Events form in the CMS). The home page shows the next 3 and the Events page shows all upcoming ones grouped by month. Fields: title, date, time, place, one-line description, emoji or photo, card colour.

- **Several days in a row** (a book fair that runs all week): set `date` to the first day and `end_date` to the last day. The card stays on the list until the last day. Put the days in `time`, for example "Mon-Fri, 3:00-5:00 PM".
- **Past events** drop off the list the next time the site rebuilds. See HOW-IT-WORKS.md for the nightly rebuild.
- **A repeating series** (a monthly meeting): add one card for the next meeting. After it passes, change its date, or add the next one.

## 2. A month calendar (Google Calendar embed)
Parents also like a month view and a "subscribe" link. Use a public Google Calendar for this.

1. Sign in to a PTA-owned Google account (not a personal one, so it survives board changes).
2. Google Calendar > Other calendars (+) > Create new calendar, named "Monte Vista PTA Events", time zone Pacific Time - Los Angeles.
3. Settings for that calendar > Access permissions > Make available to public (See all event details). Only put public events on it.
4. Settings > Integrate calendar > the embed customizer: Mode = Month, height about 700. Copy the `<iframe>` code. Paste it into the CMS under **Page text > Events page > Google Calendar embed code** (or `calendar_embed` in `_data/pages.yml`).
5. For phones, a second embed in **Agenda** mode reads better than a month grid.
6. Add a link to the calendar's "Public address in iCal format" so parents can subscribe from their own phone calendars.

## Repeating events in Google Calendar
- **By hand (a few series):** create the event with its time, then set the repeat to Custom (every 1 week on Mon-Fri, ends on a date) or Monthly on the second Tuesday.
- **Import many at once:** [events-import-template.csv](events-import-template.csv) (single events only; CSV can't repeat) or [events-import-template.ics](events-import-template.ics) (supports repeats). Import via Google Calendar > Settings > Import & export. Try a small file first.
- Common repeat rules for the `.ics` file: `FREQ=DAILY;COUNT=5`, `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;COUNT=5`, `FREQ=WEEKLY;BYDAY=TU;UNTIL=20270630T000000Z`, `FREQ=MONTHLY;BYDAY=2TU;UNTIL=20270630T000000Z`.

## Not built (an idea for later)
Keeping two places up to date is the weak point. A small script or GitHub Action could read the Google Calendar's iCal feed and create the `_events/` files automatically, so the calendar is the only thing anyone edits. It isn't built, so today an event added to the calendar does not become a card until someone adds it.
