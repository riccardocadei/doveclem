# Dov’è Clem

A 16-step drum machine built around voice memos. Eight synthesised voices — five
drums, a bass arp, a chord stab and a lead you write note by note — plus a
swappable pack of recordings, each with speed, start-point, chop-length and
reverse controls, so a spoken phrase can be played as a rhythmic part.

The name is an homage to *Dov’è Liana?*, the record the sound comes from — and
the reason the opening screen is an italo sunset. The packs are the point: it
started with Clementina, but any voice works, so the app is not named after one
person.

Everything is client-side: no build step, no dependencies, no runtime network
calls. The drums, bass and chords are generated with the Web Audio API; the
voices are decoded once into memory and triggered by a look-ahead scheduler, so
timing does not drift the way `setInterval` playback does.

```
index.html                 the whole app (markup, styles, audio engine)
manifest.webmanifest       PWA metadata — name, icons, standalone display
sw.js                      service worker: network-first shell, cached audio
audio/<pack>/*.m4a         one folder per voice pack
icons/*.png                home-screen and maskable icons
```

## Adding a voice pack

This is deliberately a two-step change, because packs are the thing most likely
to grow. Waveforms and durations are measured from the decoded audio at runtime,
so there is nothing to precompute.

1. Drop the recordings into a new folder, e.g. `audio/nonni/`. Use plain ASCII
   filenames — no spaces, accents or curly apostrophes.
2. Add an entry to the `PACKS` array near the top of the `<script>` block in
   `index.html`:

```js
const PACKS = [
  { id:'clem', name:'Clem', clips:[ /* … */ ] },
  { id:'nonni', name:'Nonni', clips:[
      { label:'Ma che dici',  short:'Che dici', url:'audio/nonni/01-ma-che-dici.m4a' },
      { label:'Vieni a cena', short:'Cena',     url:'audio/nonni/02-vieni-a-cena.m4a' }
  ]}
];
```

`label` is the full name shown in the Pattern and Track headers; `short` is what
fits on the mixer chip, so keep it under about ten characters. A pack can hold
any number of clips — the mixer grid grows to fit.

Then bump `CACHE` in `sw.js` (`doveclem-v5` → `doveclem-v6`) so installed copies pick up
the new `index.html`. The audio itself needs no `sw.js` change: new files are
cached the first time they play.

Switching packs from the picker keeps your drum pattern and reloads the voices,
so a groove you like carries across to different people's recordings.

## Run it locally

A service worker needs a real origin, so serve it rather than opening the file:

```sh
cd app
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy

It is live at https://www.riccardocadei.com/doveclem/ from the `main` branch of
`riccardocadei/doveclem` via GitHub Pages (Settings → Pages → main / root). Push to
`main` and it redeploys. HTTPS enforcement is on, which the service worker needs.

Pages sites are publicly readable — anyone with the URL can play the recordings.
For a private deployment, Cloudflare Pages plus Cloudflare Access restricts the
site to your own email on the free tier.

## Install it on the iPhone

1. Open the URL in **Safari**. Chrome and Firefox on iOS cannot install to the
   home screen — every iOS browser is WebKit, but only Safari offers the option.
2. Tap **Share → Add to Home Screen → Add**.
3. Launch it from the new icon.

It opens full-screen with no browser chrome, gets its own card in the app
switcher, and works offline once cached. It never expires — the seven-day limit
applies to Xcode free-signed native builds, not to home-screen web apps.

**If you hear nothing**, check the ringer switch. iOS routes Web Audio through
the ringer channel unless the page claims the playback audio session, which this
app does on launch (`navigator.audioSession`); on older iOS the switch still wins.

## Playing it

**Mixer** shows every track at once. Each chip has 16 dots for its pattern, the
tall bright dot is the playhead, and a chip tints as it fires — so you can see
what is making the sound. Tap a chip to select and hear it; the bar down its
right edge mutes.

| Control | What it does |
| --- | --- |
| Play / Space | Start and stop the sequencer |
| BPM ± | Tempo, 50–200 |
| Swing | Pushes every off-beat 16th late for a shuffled feel |
| Echo | Dotted-eighth feedback delay, re-synced when the tempo changes |
| Key | Root note for Bass, Stab and Lead |
| Progression | Four-bar chord move the Bass and Stab follow; **Hold** stays on the root |
| Pattern | Tap steps to toggle, drag to paint; Clear track empties this one |
| Pattern (Lead) | Eight rows of the minor scale — tap a row to write that note, tap it again to erase |
| Level | Per-track volume |
| Track → Echo | How much of that track feeds the delay |
| Arp / Chord | Bass walks the intervals one per hit; Stab plays them together |
| Speed | Playback rate, 0.4×–2.2× — changes pitch along with tempo |
| Start | Where in the clip the trigger begins, for picking out one word |
| Chop | Cuts playback to 1, 2, 4 or 8 steps — the main way to make speech rhythmic |
| Forward / Reverse | Sample direction |
| Keys 1–9 | Trigger the first nine tracks from a keyboard |

### Tracks

Kick, Clap, Snare, Hat (closed), Hat (open), Bass arp, Chord stab, Lead, then one
track per clip in the current pack.

Bass advances through its interval set one note per hit, so `Oct` gives the
octave-jumping pulse italo-disco is built on; Stab plays the same intervals as a
chord. Both follow the current chord: pick a **Progression** and they move
through it, one chord per bar, raising the third on the major chords so the
harmony stays in key.

**Lead** is the melody, two detuned sawtooths straight into the delay. Select it
and the Pattern strip becomes eight rows — one per degree of the natural minor
scale from the Key, root rows tinted so you can find the octave. Tap a row to
place a note, drag to draw a line, tap a lit cell again to erase. The lead stays
in the key's scale rather than transposing with the chords, which is what lets a
tune stay recognisable while the harmony moves under it.

### Grooves

- **Italo** — 120 BPM, four-on-the-floor, off-beat open hat, claps on 2 and 4,
  octave bass on eighths, chord stabs on the off-beats, echo on.
- **Talk** — 84 BPM, swung and sparse, voices playing in full.
- **Chop** — 96 BPM, voices sliced to two steps.
- **Rush** — 132 BPM, sixteenth hats and bass, everything chopped to one step.

The four below are melodic. They are written from italo-disco idioms — the minor
four-bar turnaround, octave bass, off-beat open hat, dotted-eighth echo — not
transcribed from any particular record.

- **Sunset** — 118 BPM, i–VI–III–VII, an eight-note lead arching up to the octave.
- **Riviera** — 126 BPM, i–VII–VI–VII, sixteenth bass under a descending lead.
- **Notturno** — 104 BPM, i–iv–VI–V, slow and sparse, five notes in the bar.
- **Corsa** — 134 BPM, i–VI–III–VII, sixteenth everything and a running lead.

Patterns live in memory only, so they reset when the app is closed.
