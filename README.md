# Youth Time Revival (YTR)

A bilingual (English / Kinyarwanda) Django website for the Youth Time Revival youth
ministry. This is a full, database-backed rebuild of the `ytr.html` static prototype:
same look, same instant client-side language toggle, but every piece of content —
articles, devotions, podcasts, videos, books, FAQs, the About page, the contact
form — is now editable from the Django admin, with a role-based accounts system
and a submit → review → publish workflow for Authors and Admins.

## Tech stack

- Python 3.11+, Django 5.2
- Server-rendered Django templates (no separate SPA/DRF frontend)
- Tailwind CSS, built via the standalone Tailwind CLI (`npm`), theme tokens lifted
  straight from the prototype (`tailwind.config.js`)
- SQLite for local dev; set `DATABASE_URL` to point at Postgres in staging/prod
- Django's built-in auth (User + a one-to-one Profile with a `role`) for accounts —
  no custom user model, no django-allauth
- Django admin as the CMS/power-user fallback for every content model
- Pillow for image uploads (article covers, podcast/book covers, author avatars)
- `django-environ` for settings, split into `config/settings/{base,dev,prod}.py`

## Project layout

```
apps/
  core/          SiteSettings (singleton), Gathering, ReviewableContent abstract
                 base, shared icon library, sitewide search
  accounts/      Profile (role: admin/author/member), Bookmark, RSVP, Testimony,
                 PrayerRequest, registration/login views
  dashboard/     Role-gated dashboard: admin/author/member screens, the review
                 queues, and the toggle-bookmark/toggle-rsvp actions
  devotions/     Devotion (reviewable)
  articles/      Author (byline), Article (reviewable)
  podcasts/      PodcastSeries (curated), Episode (reviewable)
  videos/        VideoSeries (curated), Video (reviewable)
  library/       Book (curated)
  about/         SevenMountain, BeliefPoint, CallTimelineEntry (curated)
  faq/           FAQ (curated)
  engagement/    NewsletterSubscriber, ContactMessage (+ contact/subscribe forms)
config/          settings package, root urls.py, wsgi/asgi
templates/       base.html + one template per page, shared partials (nav, footer,
                 cards), plus templates/dashboard/ and templates/accounts/
static/
  css/input.css  Tailwind source (compiles to static/css/dist.css)
  js/site.js     language toggle, mobile menu, hero embers, tabs, FAQ marquee,
                 devotion image download, search overlay — plain JS, no jQuery
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS/Linux

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env           # Windows
# cp .env.example .env           # macOS/Linux
# edit .env and set a real SECRET_KEY (use a generated value of 50+ characters)

# 4. Install Tailwind CLI and build CSS
npm install
npm run build:css                # one-off build -> static/css/dist.css
# npm run watch:css               # rebuild on save, while developing

# 5. Set up the database
python manage.py migrate
python manage.py seed_demo_content    # loads sample content + demo accounts
python manage.py createsuperuser      # your first Admin login

# 6. Run it
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the site, `http://127.0.0.1:8000/dashboard/`
for the role-based dashboard (redirects to your role's screen after login), and
`http://127.0.0.1:8000/admin/` for the Django admin power-user fallback.

`manage.py` defaults to `config.settings.dev`. Deployment (`wsgi.py`/`asgi.py`)
defaults to `config.settings.prod`, which requires `ALLOWED_HOSTS` to be set via
the environment, requires a strong non-placeholder `SECRET_KEY`, and turns on
the standard HTTPS/HSTS hardening. See [docs/security.md](docs/security.md) for
the required production environment and reverse-proxy/media policies.

## Accounts, roles, and the review workflow

Three roles, stored on `accounts.Profile.role`: **admin**, **author**, **member**.

- **Sign up** (`/accounts/register/`) creates a `User` with `is_active=False` and
  a `member` Profile. Django's auth backend already refuses to log in an inactive
  user, so no custom auth backend is needed — the registration view just shows a
  clear "pending admin approval" message instead of silently redirecting.
- **Admins** approve or reject sign-ups from the dashboard's Pending sign-ups
  queue. Approve sets `is_active=True`. **Reject deletes the account** (the
  simpler of the two options the spec allowed — there's no "rejected" user state
  to manage separately).
- Promoting a Member to Author (or back) is an Admin-only action in the
  dashboard's User management screen — there's no self-service option, and the
  role dropdown only offers Member/Author (promoting to Admin isn't exposed
  there; do that via Django admin if you ever need to).
- The first Admin comes from `createsuperuser`: a `post_save` signal on `User`
  gives every superuser an `admin` Profile automatically, and every other new
  user a `member` Profile.

**Content review** (`core.ReviewableContent`, an abstract base with
`status`/`submitted_by`/`reviewed_by`/`review_note`/`submitted_at`/`reviewed_at`/
`published_at`) is applied to `Article`, `Devotion`, `Episode`, and `Video`.
FAQ, Book, SevenMountain, BeliefPoint, Gathering, and SiteSettings stay
Admin-only/curated, per spec — none of them seemed to genuinely need an Author
submission flow, so nothing was added there.

- Authors create/edit their own drafts, then "Submit for review" (`status`
  → `pending`). They can't set `published` themselves, and can't edit again
  once it's pending or published (only while `draft` or `rejected`).
- Admins review everything pending in one queue, can edit before deciding, and
  either Approve (→ `published`, `published_at=now`) or Reject (requires a
  `review_note`, which the Author sees on their own dashboard so they can fix it
  and resubmit).
- **Every public-facing view filters `status=published`** — home, article
  list/detail, devotion pages, podcast episodes, videos. Draft/pending/rejected
  content is never reachable from the public site, including by guessing a
  detail-page URL (404s instead of leaking a draft).

**Member features**: Bookmark an article from its detail page, RSVP to the next
gathering from the homepage (both just require being logged in — not gated to
the `member` role specifically, since an Author or Admin browsing the public
site should be able to save an article too), and submit Testimonies/Prayer
requests from the member dashboard. Approved testimonies are just marked
approved for now — no public testimonies page was built (flagging that as a
"if you want it" rather than building it unasked). Prayer requests are private:
visible only to the submitting member and Admins, with a simple "mark reviewed"
action and no rejection flow, since it's pastoral care, not content.

**Role gating**: `apps/dashboard/access.py` has both a `role_required(*roles)`
decorator (what the dashboard's function-based views actually use) and an
equivalent `RoleRequiredMixin` class, per the spec's either/or. Anonymous users
get redirected to login as usual; a logged-in user with the wrong role gets a
hard 403, never a silent redirect — a Member can't reach `/dashboard/admin/` by
guessing the URL.

**Demo accounts** (created by `seed_demo_content`, password `demo-pass-123` for
all): `author_demo` (Author, with one draft and one already-published article
so both dashboard states are visible), `member_demo` (Member, with a pending
testimony and a pending prayer request already submitted), and `pending_demo`
(an unapproved sign-up, so the Admin queue has something to show immediately).

## Bilingual content

Every content model stores English and Kinyarwanda copy in separate fields
(`title_en` / `title_rw`, `body_en` / `body_rw`, etc.) — written independently by
the author, never machine-translated. Templates render **both** language versions
into the page at once, each wrapped in `.i18n-en` / `.i18n-rw` (or `.i18nb-en` /
`.i18nb-rw` for block-level content). `static/js/site.js` toggles which one is
visible by flipping a `lang-rw` class on `<body>` and remembering the choice in
`localStorage` — there's no page reload and no `/en/` vs `/rw/` URL split, so the
switch stays instant while still working with plain server-rendered HTML.

## Content editing

Everything editable lives in Django admin (and, for the four reviewable types,
in the dashboard's Author/Admin screens too):

- **Core** → Site settings (contact email/phone/address, social links, mission/vision
  copy) and Gatherings (the "add to calendar" flyer on the homepage)
- **Devotions** → mark one `is_featured` to make it "Today's Devotion"; the rest
  form the paginated archive
- **Articles** → Authors (bylines) and Articles (icon+color or an uploaded cover
  image, verse callout, featured flag)
- **Podcasts** → Podcast series (curated) with inline Episodes (reviewable)
- **Videos** → Video series (curated) with inline Videos (reviewable; mark one
  `is_featured` for the homepage feature slot)
- **Library** → Books
- **About** → Seven Mountains, Belief points, Call timeline entries
- **FAQ** → questions, with one optionally marked `is_highlighted` for the
  "Most Asked" card
- **Engagement** → Newsletter subscribers and Contact messages (both are written
  here automatically by the public contact page's forms)

## Search

`/search/?q=...` is a small JSON endpoint (`icontains` over titles/questions
across Article, Devotion, and FAQ — published content only) that the search
overlay in `site.js` calls — results link to real page URLs, no client-side
content switching.

## Tests

```bash
python manage.py test
```

49 tests covering: model behavior (slug generation, singleton `SiteSettings`,
related articles), that key pages return 200 (home, article list) and 404
correctly (unknown or draft article slugs), that the contact/subscribe forms
persist to the database and trigger an email, and the accounts/dashboard system
— inactive users can't log in, role gating returns 403 (not a silent redirect)
for the wrong role, the full submit → approve → published-on-the-public-site
pipeline, sign-up approve/reject, and the bookmark toggle.

The dev settings swap in a fast (insecure) password hasher automatically when
running under `manage.py test`, so the suite runs in under a second instead of
~20s of real PBKDF2 hashing — never active outside test runs.

## Known gaps / things to plug in before launch

- `.env.example` ships with a placeholder `CONTACT_FALLBACK_EMAIL`; set the real
  ministry inbox and SMTP credentials before going live (the console email
  backend just prints emails to the terminal until then).
- Cover images, podcast cover art, and author avatars all default to the
  icon+color tile from the prototype until real images are uploaded through
  the admin.
- No audio/video hosting is bundled — `Episode.audio_url`/`audio_file` and
  `Video.youtube_url`/`video_file` are there for you to point at real files or
  YouTube links.
- No public testimonies page (see above) — easy to add later if wanted.
