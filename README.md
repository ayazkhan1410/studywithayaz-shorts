# studywithayaz-shorts

Rendered Shorts for the **Study with Ayaz** channel, hosted here so the posting
automation (vidIQ) can download them by public link.

- `videos/` — finished MP4s, named `YYYY-MM-DD-HHMM-<slug>.mp4` (publish time, Pakistan time)
- `pipeline/` — the production template used by the daily automation:
  - `tts.py` — female voice-over (Kokoro af_heart, speed 1.15; "Ayaz" forced to ɐjˈɑːz)
  - `index.html` — animated scenes + the assistant presenter (look D) + word captions; `render(t)` draws time t
  - `render.py` — renders frames with Playwright into one H.264 encode, lip-sync from the voice
  - `audio2.py` — original energetic music + satisfying SFX (clicks, pops, counting ticks, cha-ching), mixed under the voice
