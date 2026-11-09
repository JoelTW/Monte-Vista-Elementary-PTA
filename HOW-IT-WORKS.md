# How the Monte Vista PTA site works

A small static website built with Jekyll. There is no database and no server: every page is made from the files in this folder, and the result is plain HTML. It is designed to be hosted for free on GitHub Pages.

## The idea
- **Words live in data files**, not in the pages. Change the text, and every place that uses it updates.
- **Pieces of the page are components** (small templates in `_includes/`). You bring one in with one line and change the quoted text.
- **Events come from the PTA's Google Calendar.** A script reads the calendar every few hours; the home page cards, the Events page list and the month calendar all follow it. Setup and day-to-day steps are in `docs/events-and-calendar.md`.

## Where to change things

| To change... | Edit this file | In the CMS |
|---|---|---|
| Events | the PTA's Google Calendar (see `docs/events-and-calendar.md`) | (not in the editor; the calendar is the source) |
| Home page words, action cards, sponsors, President's message | `_data/home.yml` | Home page text |
| Text on About, Events, Get Involved, Give, Contact | `_data/pages.yml` | Page text |
| Yearbook page (photo steps, tips, ways to help, ordering details) and the yearbook email | `_data/pages.yml` (yearbook) and `_data/site.yml` (yearbook_email) | Page text, Site settings |
| "Get to know your PTA" (board and chairs: names, photos, roles) | `_data/team.yml` | Get to know your PTA |
| Email, address, Join / Donate / Spirit Wear / social links | `_data/site.yml` | Site settings |
| Menu items | `_data/nav.yml` | (file only) |
| Colours, fonts, spacing | `assets/css/styles.css` | (file only) |
| Where forms send submissions | `_data/site.yml` > `forms` | Site settings (file only for now) |

The `/components/` page on the running site shows every component with its live example and the line to copy.

## Components (in `_includes/`)
`hero`, `president-card`, `team-card`, `upcoming-events`, `event-card`, `calendar-grid`, `cta-card`, `feature-item`, `volunteer-form`, `header`, `footer`. Each file starts with a comment saying what it does and which options it takes.

## Editing without touching files (Pages CMS)
Pages CMS (https://pagescms.org) gives editors a form instead of raw files. The configuration is in `.pages.yml`. Based on the Pages CMS quick start:
1. Go to app.pagescms.org and sign in with GitHub.
2. Install the Pages CMS GitHub app on the account that owns the repository.
3. Open the repository. Events, Home page text, Page text and Site settings appear on the left.
4. Saving makes a change in the repository, and the site rebuilds (usually within a minute or two).

Each editor needs a free GitHub account and access to the repository. **Not yet tested:** the `.pages.yml` file hasn't been tried against a real repository, so expect small label or field tweaks after the first login.

## Running it on your computer
You need Ruby. This project pins Jekyll 3.10, the same version GitHub Pages runs.
```
cd jekyll-site
BUNDLE_PATH=vendor/bundle bundle install     # first time only
BUNDLE_PATH=vendor/bundle bundle exec jekyll serve --baseurl ""
```
(`--baseurl ""` makes the local copy work at the top of the address. `baseurl` in `_config.yml` is the repository name while the site lives at github.io, and must be set back to `""` when the custom domain is switched on.)
Then open http://127.0.0.1:4000. To only build: `bundle exec jekyll build` (output goes in `_site/`, which isn't committed).

## Hiding the site from search engines (until launch)
While the site is a draft, `hide_from_search_engines: true` in `_data/site.yml` adds a `noindex, nofollow` tag to every page, asking Google and others not to list it or follow its links. **When the site goes live on montevistapta.org, set it to `false`** (or the site will never appear in search). This is a request that search engines honour, not a lock: anyone with the address can still open the site, and the public GitHub repo is still readable. Pages already crawled can take a while to drop out.

## Publishing with GitHub Pages
1. Make a repository (the free plan needs it to be **public**, so never commit anything private).
2. Push this folder's contents. In the repository: Settings > Pages > deploy from the `main` branch.
3. For the custom domain `www.montevistapta.org`, add it under Settings > Pages and point DNS at GitHub as GitHub's instructions say. Set `url:` in `_config.yml` to the real address.
4. **Events and rebuilds:** `.github/workflows/pages.yml` builds the site, reads the calendar every few hours and publishes. Set Pages > Source to **GitHub Actions** for it to take effect. It is untested until it has run once on GitHub.

## Facebook and Instagram ("Follow along")
The site shows a QR code and a button for each page, with no scripts from Facebook or Instagram. The links are in `_data/site.yml` under `links`. The QR images in `assets/qr/` are made from the links listed in `scripts/make_qr.py`, so **if a link changes, edit it there and regenerate the images** (`pip install -r scripts/requirements-images.txt`, then `python scripts/make_qr.py`, then commit). The script puts the Bobcat logo in the middle, and the tests check that every code scans. Facebook's own embed shows only the page name for our page and Instagram has no free feed embed, so there is no automatic post feed. If someone with access to the accounts is found, a widget service could add one later.

## Forms (volunteer, contact, newsletter)
GitHub Pages has no server, so a form service receives the messages and emails them to the PTA. The site's forms send in the background, show a clear thank-you or error message, keep what the person typed if something fails, block double-sends, catch simple spam bots with a hidden field, and always show the PTA email as a fallback.

**Connect a service (one time).** Formspree is the one the site is built and tested for; any service that accepts a normal form post and answers JSON should work.
1. Create an account at formspree.io with a PTA-owned email (so it survives board changes), and create a form. Formspree gives you an address like `https://formspree.io/f/xxxxxxxx`.
2. Paste it into `_data/site.yml` under `forms > endpoint` (or in the editor under Site settings > Forms), and put `Formspree` in `service_name`. One address serves all three forms; each message says which form it came from (the subject line and a `form_type` field).
3. Confirm the notification email address in Formspree, then submit each form once on the live site and check the email arrives.
4. In Formspree, turn on its spam filtering, and consider its reCAPTCHA option.

**Limits and costs.** Formspree's free plan has a monthly cap on submissions (third-party reviews say 50; check their pricing page) and a rate limit (their help centre says 20 posts a minute per form). Over the cap, messages are held rather than emailed. A PTA site is unlikely to hit it, but watch it around membership drives.

**The newsletter box** only emails each address to the PTA. It is not a mailing-list tool: someone has to add the addresses to wherever newsletters are sent from. If the PTA picks a newsletter tool (Mailchimp, Buttondown and so on), the form can be pointed at it instead.

**Privacy.** Each form says that a form service delivers the message and asks people not to include students' full names. Don't collect anything more sensitive than a name, an email address and a short note.

Until an address is entered, each form tells the visitor it is not connected yet and shows the PTA email.

## The Join the PTA poster
The Get Involved page shows the poster (`assets/images/join-poster.jpg`) with a download for a print-quality copy (`assets/downloads/join-poster-print.jpg`). The QR code on it points to the Totem join page. To change the poster, replace those two files; the wording around them is in the editor under Page text > Get Involved. The poster artwork is only 1086 x 1448 pixels, so a print looks soft; a larger original from the designer would print better. If the Join link ever changes, the QR code on the poster has to be remade (ask whoever maintains the site, who keeps the poster originals outside this repository).

## What this proof of concept does NOT include yet
- The forms are built and tested against a fake form server, but not yet connected to a real service (see Forms above).
- The Google Calendar embed is a placeholder (paste the embed code in the CMS, or `_data/pages.yml`).
- Most photos are still placeholders (emoji and colour blocks). The hero uses a normal rectangular photo (`assets/images/hero.jpg`); the site adds the curved gold edge, so no image editing is needed. To swap it, replace that file (a width of about 1400 to 1600 pixels is plenty) and adjust `photo_position` and `photo_alt` in `_data/home.yml`.
- The search icon is a visual placeholder.
- Pages CMS configuration and the nightly-rebuild workflow are untested against a live repository.
- Accessibility has only been checked on the earlier static mockup, not re-audited on this version.
