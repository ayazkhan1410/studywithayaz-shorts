# studywithayaz-shorts

Rendered Shorts for the **Study with Ayaz** channel, hosted here so the posting
automation (vidIQ) can download them by public link.

- `videos/YYYY-MM-DD/HHMM-<slug>.mp4` — finished MP4s, one folder per publish date, file named by publish time (Pakistan time)
- `pipeline/` — the production template used by the daily automation:
  - `tts.py` — female voice-over (Kokoro af_heart, speed 1.15; "Ayaz" forced to ɐjˈɑːz)
  - `index.html` — animated scenes + the assistant presenter (look D) + word captions; `render(t)` draws time t
  - `render.py` — renders frames with Playwright into one H.264 encode, lip-sync from the voice; `render(t)` may be async so embedded `<video>` screen recordings are seeked frame-accurately (use all-intra VP8 webm clips)
  - `audio2.py` — original energetic music + satisfying SFX (clicks, pops, counting ticks, cha-ching), mixed under the voice; set `"drop"` (seconds) in `timing.json` to place the beat drop

## Schedule
Two Shorts a day: the user's own videos at 7 PM, and an automated one at 10 PM (Pakistan time), the channel's most active hour according to vidIQ subscriber activity.
