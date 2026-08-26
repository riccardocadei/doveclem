# Clem Groovebox

A 16-step drum machine built around five voice memos. Four synthesised drum
voices (kick, snare, hat, clap) plus the five recordings as playable samples —
each with speed, start-point, chop-length and reverse controls, so a spoken
phrase can be turned into a rhythmic part.

Everything is client-side: no build step, no dependencies, no network calls at
runtime. The drums are generated with the Web Audio API; the voices are decoded
once into memory and triggered by a look-ahead scheduler, so timing does not
drift the way `setInterval` playback does.

```
index.html                 the whole app (markup, styles, audio engine)
manifest.webmanifest       PWA metadata — name, icons, standalone display
sw.js                      service worker, precaches every asset for offline use
audio/*.m4a                the five recordings
icons/*.png                home-screen and maskable icons
```

## Run it locally

A service worker needs a real origin, so open it over HTTP rather than as a
`file://` path:

```sh
cd app
python3 -m http.server 8000
# then open http://localhost:8000
```

## Put it online (GitHub Pages, free, permanent)

```sh
cd app
git init -b main
git add -A
git commit -m "Clem Groovebox"
git remote add origin https://github.com/<your-username>/clem.git
git push -u origin main
```

Then on GitHub: **Settings → Pages → Source: Deploy from a branch → main / (root) → Save.**
After a minute the app is live at `https://<your-username>.github.io/clem/`.

Note that GitHub Pages sites are publicly readable — anyone with the URL can
play the recordings. For a private deployment, Cloudflare Pages plus Cloudflare
Access restricts the site to your own email on the free tier.

## Install it on the iPhone

1. Open the URL in **Safari** (not Chrome — only Safari can install to the home screen on iOS).
2. Tap **Share → Add to Home Screen → Add**.
3. Launch it from the new icon.

It opens full-screen with no browser chrome, gets its own card in the app
switcher, and works with no connection once the service worker has cached the
assets. It never expires — that seven-day limit applies to Xcode free-signed
native builds, not to home-screen web apps.

**If you hear nothing**, check the ringer switch. iOS routes Web Audio through
the ringer channel unless the page claims the playback audio session, which this
app does on launch (`navigator.audioSession`); on older iOS versions the switch
still wins, so flip it off silent.

## Playing it

| Control | What it does |
| --- | --- |
| Track chips | Tap to select a track for editing and hear it immediately |
| Step row | Tap to toggle a step; drag across to paint several |
| Play / Space | Start and stop the sequencer |
| BPM ± | Tempo, 50–200 |
| Swing | Pushes every off-beat 16th late for a shuffled feel |
| Speed | Playback rate, 0.4×–2.2× — changes pitch along with tempo |
| Start | Where in the clip the trigger begins, for picking out one word |
| Chop | Cuts playback to 1, 2, 4 or 8 steps — the main way to make speech rhythmic |
| Reverse | Plays the sample backwards |
| Talk / Chop / Rush | Starting patterns, from sparse and swung to 132 BPM |
| Keys 1–9 | Trigger the nine tracks from a keyboard |

Patterns live in memory only, so they reset when the app is closed.

## Changing the sounds

Drop new `.m4a` or `.mp3` files into `audio/`, then update the `CLIPS` array near
the top of the `<script>` block in `index.html` (each entry needs `label`,
`short`, `dur`, `peaks` for the waveform, and `url`) and add the filenames to
`ASSETS` in `sw.js`. Bump `CACHE` in `sw.js` — `clem-v1` to `clem-v2` — so
installed copies pick up the change instead of serving the old cache.
