# 🍸 Tip Tracker

A personal shift and tip-tracker for the service industry. Built for myself
to log shifts, hours, tips, and the position I worked, then see weekly
breakdowns by role. Speakeasy-themed dark UI, mobile-friendly, accessible
from any device.

## Features

- **Per-shift logging** — day, hours, tips, note, and position worked
- **Position breakdown** — Serving / Bartending / Other (with custom label)
- **Automatic weekly rollover** — uses ISO weeks (Monday → Sunday)
- **Sunday-night summary popup** — totals per position + a grand total,
  shown automatically on Sunday evenings
- **Past-week history** — most recent 4 by default, "Show all" toggle for
  longer-range review (e.g. "what did I make in March?")
- **Speakeasy aesthetic** — warm dark gradient background, brass/gold
  accents, Cormorant Garamond serif title, DM Mono for numbers
- **Personal-link access gate** — app refuses to load without a personal
  URL token, keeping data private even on a public hosting URL
- **Persistent across devices** — data lives in a private GitHub Gist, so
  the laptop, phone, and any other device see the same shifts

## Tech stack

- **[Streamlit](https://streamlit.io)** — UI framework
- **GitHub Gist** — data backend (read/write via the Gists API)
- **Streamlit Community Cloud** — hosting
- Python 3.12

## Live app

Deployed on Streamlit Community Cloud. URL is gated behind a personal
token; without the `?k=...` query param the app shows only a "private
tracker" page.
