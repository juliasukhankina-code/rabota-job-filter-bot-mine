# Telegram job filter bot

Scans a Telegram folder of vacancy channels/groups once a day, filters
vacancies in two stages (cheap keyword match, then an LLM fit-score call
against your profile), and sends matches to your own Telegram Saved Messages
("Избранное"). Runs for free on a daily schedule via GitHub Actions.

## How it works

1. You put the Telegram channels/groups you want scanned into one Telegram
   folder (the folder name is config — no separate channel list to maintain).
2. Every message from the last `LOOKBACK_HOURS` gets a cheap keyword
   pre-filter (`KEYWORDS` in `.env`), plus built-in filters that skip resumes,
   weekly digests, and auto-generated "we found N vacancies" catalog posts —
   all before anything costs an LLM call.
3. Whatever survives goes to an LLM (via Timeweb AI) with the full contents
   of `profile.md` as context, and gets a yes/no fit judgment plus a short
   comment.
4. Matches get sent to your own Saved Messages as one daily digest.

There's no web UI, no database, no separate channel config — the Telegram
folder and `profile.md` are the only two things you maintain day to day.

## Easiest way to set this up: use an AI coding agent

You don't need to know how to code to get this running. Clone the repo,
open the folder in **Claude Code** or **Codex** (or any similar coding
agent), and tell it: *"follow the README and set this bot up for me."* It
can do almost all of the setup below on its own.

**The agent can do for you:**
- clone the repo, create the virtualenv, install dependencies
- write `.env`, run the session-string script
- write/edit `profile.md` based on you describing your background and
  what you're looking for out loud
- create the GitHub repo, push your secrets, wire up deployment
- test it end to end and show you the result

**Only you can do these few things** (a handful of minutes, no coding
involved):
- log into [my.telegram.org](https://my.telegram.org) with your own phone
  number and create an API app (step 1 below)
- type in the one-time login code Telegram texts to your phone when the
  agent generates the session string (step 4) — this is a security step,
  the agent genuinely cannot see it for you
- create an Timeweb AI account and add a few dollars of credit (step 2) —
  a payment step, not something to hand to an agent
- approve one browser login for GitHub (step 7) — one click

Everything else below is exactly what the agent will do for you — it's
here so you know what's happening, not because you have to type it
yourself.

## Setup

### 1. Telegram API credentials

Go to [my.telegram.org](https://my.telegram.org) → log in with your phone
number → **API development tools** → create an application (any name).
You'll get an `api_id` and `api_hash`.

> If the form errors out with a generic "ERROR" on creation, it's usually
> because the app's **Short name** contains "bot" — Telegram reserves that
> for BotFather bots. Use a short name without "bot" in it.

### 2. Timeweb AI API key

Go to [api.timeweb.ai](https://api.timeweb.ai) → sign up → add a few dollars
of credit → **Keys** → create a key. `gemini/gemini-3.1-flash-lite` (the
default model here) is cheap enough that a few dollars lasts a long time.

### 3. Group your vacancy channels into a Telegram folder

In Telegram: create a folder, add the channels/groups you want scanned to
it. Note the folder's exact name — that's your `FOLDER_NAME`.

### 4. Local setup + generate a session string

This folder is already prepared on this computer. Do not recreate `.env` from
`.env.example`, because that would overwrite your settings. The dependencies
are in the ignored `.packages` folder.

Fill in `TG_API_ID`, `TG_API_HASH`, `TIMEWEB_API_KEY`, `FOLDER_NAME`,
`KEYWORDS` in `.env`. Then create the Telegram session using this Windows command in the VS Code terminal:

```powershell
$env:PYTHONPATH = "$PWD\.packages"; & "C:\Users\y.lemekhova\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\generate_session_code.py
```

Enter your phone number and the code delivered in the already logged-in Telegram app. The helper saves the session string into .env automatically. Never share the session string or login code.

### 5. Write your profile

Edit `profile.md` — this is the only place that defines what counts as a
fit. See the template comments in the file for guidance, including an
optional "hard-gap screening" pattern if you find the bot letting through
too many title-matches-but-actually-wrong-role vacancies.

### 6. Test locally

```powershell
$env:PYTHONPATH = "$PWD\.packages"; & "C:\Users\y.lemekhova\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\main.py
```

Check your Telegram Saved Messages for the result (or `No matching
vacancies found` in the terminal if nothing matched in the lookback window).

### 7. Deploy: GitHub Actions

Create a **private** repository on GitHub. In the repository, open
**Settings → Secrets and variables → Actions** and add these repository
secrets using the matching values from `.env`:

- `TG_API_ID`
- `TG_API_HASH`
- `TG_SESSION_STRING`
- `TIMEWEB_API_KEY`
- `FOLDER_NAME`
- `KEYWORDS`
- `LOOKBACK_HOURS`

The GitHub Actions workflow uses Gemini 3.1 Flash Lite directly. To change the
model for scheduled scans, update `TIMEWEB_MODEL` in `.github/workflows/daily.yml`.
Never upload `.env` or paste its contents into a chat. Then push the project
to the repository. The included workflow scans daily at 06:00 Moscow time;
you can also start a scan manually from **Actions → Daily vacancy scan → Run
workflow**. To see the result, check Telegram Saved Messages and the workflow
run page.

Every run checks out the repo fresh and installs dependencies — a
`git push` to `main` *is* the deploy, there's no separate build step.

## Notes

- **No push notifications**: messages sent to your own Saved Messages via
  the API don't trigger a phone notification — you check manually, or rely
  on the daily cadence. A real push would require a separate bot via
  BotFather sending to you instead of (or in addition to) Saved Messages.
- **Errors get reported to you too**: if the script crashes, it posts the
  error (truncated) to Saved Messages before failing the GitHub Actions run,
  so you don't have to go check logs to notice something broke.
- If you change `.env` values later, re-run the `gh secret set` loop above —
  GitHub Secrets don't update themselves. If you add a new required env var,
  add it as a Secret *and* reference it in `daily.yml`'s `env:` block before
  relying on it — a var referenced in the workflow but missing from Secrets
  becomes an *empty string* at runtime, not unset, which can silently break
  a `os.environ.get(KEY, default)` fallback in `main.py`.


