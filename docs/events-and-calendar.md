# Events and the calendar

The events on the site come from **one Google Calendar**. Anyone who can edit that calendar updates the whole site: the month calendar, the "Upcoming events" list on the Events page, and the "What's Happening" cards on the home page.

## How it works
1. The PTA keeps a **public Google Calendar** ("Monte Vista PTA Events").
2. Every few hours (and whenever the site is changed) a GitHub Action runs `scripts/sync_calendar.py`. It reads the calendar's public **iCal address**, works out every date (including repeating events, time zones and all-day ranges), and writes the event data.
3. The site is rebuilt with that data. The month calendar is drawn in the browser; the lists are plain HTML.

An event added or changed in Google Calendar shows up on the site within a few hours. To update right now: GitHub > Actions > "Build and deploy site" > Run workflow.

Until a real calendar is connected, the site shows **sample events** from `calendar/sample.ics` (the 2025-26 PTA calendar, moved forward 52 weeks so weekdays stay right).

## Connect the real calendar (one time)
1. Sign in to a PTA-owned Google account (not a personal one, so it survives board changes).
2. Google Calendar > Other calendars (+) > Create new calendar, named "Monte Vista PTA Events", time zone Pacific Time - Los Angeles.
3. Settings for that calendar > **Access permissions for events** > tick **Make available to public** (See all event details). Only put public events on it.
4. Same settings page > **Integrate calendar** > copy **Public address in iCal format** (it ends in `basic.ics`).
5. Paste it into `_data/site.yml` under `calendar > ical_url`, or in the editor under **Site settings > Events calendar**. Commit it.
6. GitHub > Settings > Pages > Source = **GitHub Actions** (one time). Then run the workflow once and check the Events page.
7. Add the PTA people who should edit events to the calendar: Settings > Share with specific people > "Make changes to events".

## Putting the yearly Google Doc into the calendar
The PTA writes a calendar document each year. `scripts/doc_to_ics.py` turns its text into a file Google Calendar can import:
1. In the Google Doc: File > Download > Plain text (.txt). Delete the Spanish half, or leave it (the script stops at a line starting "Calendario").
2. Run: `python scripts/doc_to_ics.py calendar.txt --year 2026 -o pta-calendar.ics` (the year the school year *starts*).
3. Google Calendar > Settings > Import & export > Import, choose the file and the "Monte Vista PTA Events" calendar.
4. **Read the "Please check" list the script prints.** It names every line it had to guess about or could not use: a line that lost its date (it uses the date of the line above), indented sub-items (named after the event above, for example "Penguin Patch in MPR: Set Up"), and lines it did not understand (left out, so add those by hand).
5. **Check the result.** Times without AM/PM are guessed (1 to 6 = PM, 7 to 11 = AM; a trailing p as in "4:00p" is believed). Items marked TBD, and "4/13 or 4/14" style dates, come in as *tentative* and show a "to be confirmed" label on the site. Dates may be written "10/13: ...", "10/13 ..." or "10/13- ...". Fix dates in Google Calendar as they firm up.
6. **The doc itself** is linked from the Events page. The link and its wording are settings (`calendar > doc_url` and `doc_label` in `_data/site.yml`); change them each school year, or clear the link to hide it.

## Day-to-day
- **Add an event:** create it in Google Calendar with a title, date, time and location. Put a short sentence on the first line of the description (it becomes the one-line blurb on the cards) and a link anywhere in it if you want a "More information" link.
- **Several days in a row** (a book fair): make it an all-day event that spans the days.
- **A repeating event** (a monthly meeting): use Google Calendar's repeat ("Monthly on the first Tuesday"). Each date appears separately on the site.
- **Not sure of the date yet:** put TBD in the title, or set the event's status to Tentative. The site shows "Date or time to be confirmed".
- **Cancelled:** delete the event, or set its status to cancelled.
- **Emoji and card colour** come from words in the title. See `_data/event_icons.yml` to add or change them.

## Event details, categories and "Add to calendar"
Clicking an event card (home page or Events page) or a day on the month calendar opens a pop-up with a category tag, the title, date, time, place, description, a small picture, and a gold **Add to calendar** button. The button opens three choices: Google Calendar, Outlook.com, and a downloadable `.ics` file (Apple Calendar and most other apps). The pop-up is `_includes/event-dialog.html` plus `assets/js/event-dialog.js`. Without JavaScript a card simply links to the Events page.

**Descriptions.** Type them in the Description box of the Google Calendar event. Plain text, one paragraph per line. A web address in it becomes the "More information" link. Events with no description still work, they just show less.

**Categories.** Every event gets a tag (Meeting, Fundraiser, Celebration, Family, Community, School, or "PTA Event" when nothing fits) and the matching picture. The rules are in `_data/event_categories.yml` (editable in the CMS under "Event categories"): the first category whose words appear in the event title wins, so the order matters. To override one event, type a line such as `Category: Fundraiser` in its Google Calendar description. That line is not shown to visitors. Keep each category's `slug` as it is: it picks the picture in `assets/images/events/`.

**Pictures and icons.** The seven pictures in `assets/images/events/` are simple drawings made for this site. Replace a file with another picture of the same name to change one. The brand icons in `assets/images/icons/` come from the Simple Icons set (CC0, public domain).

**Good to know**
- Timed events need `start_utc` and `end_utc` in the event data (`sync_calendar.py` writes them). An event with no end time is added as one hour long.
- Events whose date or time is still "to be confirmed" say so inside the visitor's calendar entry too.
- The "Outlook.com" link is built from Microsoft's published address format but has not been tried against a real Outlook account. The Google link and `.ics` file were checked.

## Good to know
- **Everything in the calendar is public**, including descriptions, locations and links. Don't put anything private in it.
- **The calendar's text is shown as plain text**, so a typo or odd character can't break the page.
- **If the calendar can't be read** (it was made private, or the address changed), the workflow fails and the site keeps showing its last good version. Check the Actions tab.
- **Scheduled runs pause after 60 days with no activity in the repository** (a GitHub rule). Any new commit starts them again.
- **Past events** drop off the lists at the next rebuild (within a few hours). The month calendar starts at the current month.
