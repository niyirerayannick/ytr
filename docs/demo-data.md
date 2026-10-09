# Demonstration data

The local database has been populated with the existing bilingual sample articles, devotions, podcasts, videos, library resources, ministry information, community requests, and demo accounts. The seed command now also creates four Morning Devotion examples:

| Slug | State | Demonstrates |
|---|---|---|
| demo-morning-live | Live for approximately 50 minutes after seeding | LIVE styling, current-session homepage/dashboard cards |
| demo-morning-upcoming | Tomorrow at 06:00 in the configured Django timezone | Upcoming session and cover art |
| demo-morning-completed | Finished | English/Kinyarwanda summary, related devotion, available recordings |
| demo-morning-draft | Draft | Administration workflow; hidden from public pages |

All four include EN/RW titles and descriptions, Scripture references, a demo speaker, and generated branded cover art. Recordings are attached only when an existing published episode/video has an actual media source. No fake audio files or meeting links are created.

## Load or refresh

```powershell
venv\Scripts\python.exe manage.py seed_demo_content --with-admin
venv\Scripts\python.exe manage.py runserver
```

Without `--with-admin`, the command creates the regular author/member/pending accounts but does not create an administrator. Fixed demo-session slugs prevent duplicates; rerunning resets their relative dates so the live and upcoming states can be demonstrated again. Existing account passwords are not reset.

The existing seed command updates sample content and SiteSettings values and recreates its demonstration gatherings. Use it against a demonstration database, not a live ministry database.

## Local accounts

| Username | Access | Initial password |
|---|---|---|
| admin_demo | Administration Command Center and Django administration | demo-pass-123 |
| author_demo | Author dashboard, draft/pending sample articles | demo-pass-123 |
| member_demo | Member dashboard | demo-pass-123 |
| pending_demo | Inactive signup awaiting approval | demo-pass-123 |

Demo administrator creation is optional and grants staff/superuser access only to a newly created `admin_demo` account. Existing accounts with that username are not elevated and their passwords are retained. These predictable credentials are for local demonstrations.

## Preview

- `/morning-devotions/`
- `/morning-devotions/demo-morning-live/`
- `/morning-devotions/demo-morning-completed/`
- `/devotions/`
- `/accounts/login/`
- `/dashboard/` (sign in using the role you want to demonstrate)

The Join Live action requires a real Google Meet URL. Set `MORNING_DEVOTION_URL` before seeding, or configure the existing SiteSettings Morning Devotion URL; the command preserves an existing configured URL when the environment variable is absent. A blank URL leaves the join action unavailable while still showing the live state.

## Verification

Regression tests verify valid bilingual records, live/completed states, public draft protection, stable session IDs on repeated runs, optional admin creation, and preservation of an existing administrator password.
