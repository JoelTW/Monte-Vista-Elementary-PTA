# How the editor is set up

For whoever maintains the website. The visual editor is [Sveltia CMS](https://sveltiacms.app), a free, open-source editor that runs in the browser and saves to the GitHub repository. There is no database or server to run. It is one page, `admin/index.html`, one config file, `admin/config.yml`, and one preview script, `admin/preview.js`.

## How it works
1. An editor opens `/admin/` on the site and signs in with GitHub.
2. The editor reads `admin/config.yml` and builds a form for each data file in `_data/`, with a live preview beside it.
3. With `publish_mode: editorial_workflow`, **Save** creates a draft: a branch and a pull request in GitHub. The live site does not change.
4. An approver publishes the draft, which merges the pull request into `main`. The "Build and deploy site" workflow then runs and the live site updates in a couple of minutes.

Every published edit is an ordinary Git commit, so history, undo (revert a commit) and authorship come from GitHub, free and without a time limit.

## Cost
Sveltia CMS is free and open source. GitHub Pages and the free GitHub plan cover hosting for a public repository. If sign-in with GitHub is wanted rather than access tokens, one small free Cloudflare Worker is needed (see below).

## Sign-in options
- **Access token:** each editor creates a GitHub fine-grained token for this repository with **Contents** and **Pull requests** read and write permission, then pastes it into **Sign In Using Access Token**. No server, but fiddly for non-technical people. Tokens are passwords: never put one in the repository.
- **Sign in with GitHub:** needs a small [sveltia-cms-auth](https://github.com/MattBlogsIT/sveltia-cms-auth) Cloudflare Worker and a GitHub OAuth app. Once it exists, add its address as `base_url` under `backend:` in `admin/config.yml`.

## The history page
`admin/history.html` is a plain page beside the editor (Sveltia cannot add menu items). It reads the repository's public history and open pull requests from GitHub's API in the visitor's browser: published changes from `main` (who, when, what) and drafts waiting to be published. There is no token and nothing to maintain, but it only works while the repository is public and GitHub limits unsigned requests to about 60 an hour per visitor. If the repository name or branch changes, edit `REPO` and `BRANCH` at the top of its script.

## Adding an editor
1. In GitHub, open the repository, then **Settings > Collaborators > Add people**, and give the person **Write** access.
2. They accept the email invitation and sign in as above.

Keep a second admin on the repository so the site does not depend on one person.

## The config file
```yaml
backend: {name: github, repo: JoelTW/Monte-Vista-Elementary-PTA, branch: main}
publish_mode: editorial_workflow     # Save makes a draft pull request
media_folder: assets/images          # where uploaded pictures go in the repo
public_folder: /assets/images        # the address the site uses for them
collections:
- name: site_content
  files:
  - name: home                       # must match the key used in preview.js
    label: Home page text
    file: _data/home.yml             # the data file this form edits
    fields: [ ... ]
```

| Menu | Entry | Data file |
|---|---|---|
| Pages | Home page | `_data/home.yml` |
| Pages | About, Events, Get Involved, Give, Yearbook, Contact | `_data/about.yml`, `events.yml`, `get_involved.yml`, `give.yml`, `yearbook.yml`, `contact.yml` |
| Pages | Get to know your PTA | `_data/team.yml` |
| System settings | Site settings | `_data/site.yml` |
| System settings | Event categories | `_data/event_categories.yml` |

Not in the editor on purpose: the menu (`_data/nav.yml`), events (they come from Google Calendar) and styling (`assets/css/styles.css`).

## How pages are built
Every page except Home is a list of **sections** in its own data file. A section has `columns`, and a column has `blocks`. The page file (for example `about.html`) is only `{% include sections.html sections=site.data.about.sections %}`, so adding a section needs no template change.

- `_includes/sections.html` draws the sections, `column.html` draws a column's box, and `block.html` draws each block type. `button.html` and `link-url.html` are helpers.
- Block types: heading, paragraph, link_paragraph, note, email_note, email_link, chips, steps, tips, buttons, image, placeholder, placeholder_grid, role_cards, form, team, contact_details, calendar, upcoming, social_feed.
- Button and link addresses: `/path` gets the site prefix, `#name` stays on the page, full addresses are used as written, and `@join`, `@donate`, `@spirit`, `@school`, `@facebook`, `@instagram` use the links in `_data/site.yml`.
- In small print, `[email]` and `[yearbook_email]` are replaced with the addresses in `_data/site.yml`.
- The Events page also has a `banner` (the big headline at the top). `_layouts/page.html` reads it when a page sets `banner: events` in its front matter.

**Adding a new block type**
1. Add a `{% when "name" %}` branch to `_includes/block.html` that draws it.
2. Add the type, with its fields, to the `types:` list in `admin/config.yml`.
3. Add a `case 'name':` to `renderBlock` in `admin/preview.js`.
4. Build the site and compare a page before and after, so nothing else changes.

**Adding a new page:** create the data file with a `sections:` list, make a page file that includes it, and add a `files:` entry for it in `admin/config.yml` (copy the About page entry), plus its name in the list at the bottom of `admin/preview.js`.

## Field types used
Each field has a `name` (must match the key in the data file exactly), a `label` (what the editor sees) and a `widget`.

| Widget | Shows as | Example |
|---|---|---|
| `string` | one-line box | `{name: email, label: PTA email, widget: string}` |
| `text` | multi-line box | `{name: intro, label: Introduction, widget: text}` |
| `number` | number box | `{name: months_ahead, label: Months to show, widget: number, value_type: int}` |
| `boolean` | on/off switch | `{name: open, label: Open position, widget: boolean}` |
| `image` | picture picker | `{name: photo, label: Photo, widget: image}` |
| `select` | dropdown | `{name: color, label: Colour, widget: select, options: [pink, sky]}` |
| `object` | a group of fields | has its own `fields:` |
| `list` | repeatable items | `fields:` for a list of groups, or `field:` for a list of plain values |

`hint:` adds help text under a label.

## Common changes
**Change the words or buttons on a page:** open the page in the editor and edit the block. To do it in the file, edit the matching entry under `sections:` in `_data/<page>.yml`.

**Change a label or hint:** edit `label:` or `hint:`. Nothing else changes.

**Add a whole new editable file:** add an entry under `files:` with `name`, `label`, `file` and `fields`.

**Hide something from editors:** delete its field from `admin/config.yml`. The value stays in the data file.

## The preview
`admin/preview.js` draws the home page and every sections page using the site's own stylesheet, so editors see roughly how it will look. Forms, the calendar, the team grid and the social links show a note instead of the real thing. System settings show the form only. A preview is an approximation: after a design change, check that it still matches the real site.

## Rules that save time
- Names are exact. A typo in `name:` creates a blank field that saves into the wrong key.
- Indentation matters in YAML. Use two spaces, never tabs.
- Config changes apply once they are on `main`; reload the editor afterwards.
- Never put passwords, keys or member data in any of these files. The repository is public.

## Testing a config change locally
1. Run the site: `BUNDLE_PATH=vendor/bundle bundle exec jekyll serve --baseurl "" --port 4001`.
2. Open http://127.0.0.1:4001/admin/ in Chrome, click **Work with Local Repository**, and choose the `jekyll-site` folder.
3. Edits save to your files only. Check them with `git diff`, then discard with `git checkout -- _data` if they were just a test.

## Known limits
- Saving a form rewrites its whole data file, so comments inside `_data/*.yml` files can be lost. Keep explanations in these docs, not in the data files.
- The editor script is loaded from unpkg at a pinned version (see `admin/index.html`). Update the version number on purpose, after testing.
- Photos are not shrunk automatically. Ask editors to upload photos of about 1,500 pixels wide or less.
- The old Pages CMS config is `.pages.yml`. It can be deleted once Sveltia is in use.
