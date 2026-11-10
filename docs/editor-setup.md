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

| Form | Data file |
|---|---|
| Home page text | `_data/home.yml` |
| Page text | `_data/pages.yml` |
| Event categories | `_data/event_categories.yml` |
| Get to know your PTA | `_data/team.yml` |
| Site settings | `_data/site.yml` |

Not in the editor on purpose: the menu (`_data/nav.yml`), events (they come from Google Calendar) and styling (`assets/css/styles.css`).

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
**Add a text box to a page**
1. Add the key to the data file, for example under `give:` in `_data/pages.yml`.
2. Use it in the page template as `{{ site.data.pages.give.the_key }}`.
3. Add a matching field under that file's `fields:` in `admin/config.yml`.

**Change a label or hint:** edit `label:` or `hint:`. Nothing else changes.

**Add a whole new editable file:** add an entry under `files:` with `name`, `label`, `file` and `fields`.

**Hide something from editors:** delete its field from `admin/config.yml`. The value stays in the data file.

## The preview
`admin/preview.js` draws the home page banner using the site's own stylesheet, so editors see roughly how it will look. Other forms show the form only. A preview can be added for more forms by registering a template with the same name as the file entry in `config.yml`. A preview is an approximation: after a design change, check that it still matches the real site.

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
