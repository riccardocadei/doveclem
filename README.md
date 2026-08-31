# Dov’è Clem

A 16-step drum machine built around voice memos. Eight synthesised voices — five
drums, a bass arp, a chord stab and a lead you write note by note — plus a
swappable pack of recordings, each with speed, start-point, chop-length and
reverse controls, so a spoken phrase can be played as a rhythmic part.

Two packs ship with it. **Clem** is the italo-disco one it started as. **Nonni**
is Roman: accordion reeds instead of saws, major and harmonic-minor scales, and
grooves built on the stornello and the tarantella rather than on a four-on-the-floor.

The name is an homage to *Dov’è Liana?*, the record the sound comes from — and
the reason it sounds the way it does. The opening screen is a plain map of the
world, in ink on paper. The packs are the point: it started with Clementina, but
any voice works, so the app is not named after one person.

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

1. Drop the recordings into a new folder, e.g. `audio/zii/`. Use plain ASCII
   filenames — no spaces, accents or curly apostrophes.
2. Add an entry to the `PACKS` array near the top of the `<script>` block in
   `index.html`:

```js
const PACKS = [
  { id:'clem',  name:'Clem',  clips:[ /* … */ ] },
  { id:'nonni', name:'Nonni', clips:[ /* … */ ] },
  { id:'zii',   name:'Zii',   clips:[
      { label:'Ma che dici',  short:'Che dici', url:'audio/zii/01-ma-che-dici.m4a' },
      { label:'Vieni a cena', short:'Cena',     url:'audio/zii/02-vieni-a-cena.m4a' }
  ]}
];
```

`label` is the full name shown in the Pattern and Track headers; `short` is what
fits on the mixer chip, so keep it under about ten characters. A pack can hold
any number of clips — the mixer grid grows to fit.

Then bump `CACHE` in `sw.js` (`doveclem-v10` → `doveclem-v11`) so installed copies pick up
the new `index.html`. The audio itself needs no `sw.js` change: new files are
cached the first time they play.

Switching packs from the picker keeps your drum pattern and reloads the voices,
so a groove you like carries across to different people's recordings.

### Grooves for a pack

A groove in the `GROOVES` array can carry `pack:'zii'`. It then appears in the
Grooves strip only while that pack is loaded, which is what you want as soon as a
preset chops a particular sentence at a particular rate — those settings mean
nothing over somebody else's recordings. A groove with no `pack` is shared: keep
it to `v0`, unchopped and at speed, and it lands on whatever is in the machine.

A groove can also carry `timbre:'fisa'` and a `prog` whose giro is in a major or
harmonic-minor mode, which is how the Nonni presets get their accordion.

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

**Mixer** shows every track at once, split into **Machine** — the synthesised
drums, bass, stab and lead — and the current pack's **voices**. Each chip has 16
dots for its pattern, the tall bright dot is the playhead, and a chip tints as it
fires, so you can see what is making the sound. Tap a chip to select and hear it;
the bar down its right edge mutes.

| Control | What it does |
| --- | --- |
| Play / Space | Start and stop the sequencer |
| BPM ± | Tempo, 50–200 |
| Swing | Pushes every off-beat 16th late for a shuffled feel |
| Echo | Dotted-eighth feedback delay, re-synced when the tempo changes |
| Suono | **Italo** plays the Stab and Lead as detuned saws; **Fisa** plays them as accordion reeds. Drums and bass are the same either way |
| Key | Opens a one-octave keyboard — tap a note to set the root for Bass, Stab and Lead, and hear it |
| Giro | Four-bar chord move the Bass and Stab follow; **Fermo** stays on the root. The giro also picks the Lead's scale |
| Pattern | Tap steps to toggle, drag to paint; Clear track empties this one |
| Pattern (Lead) | Eight rows of the giro's scale — tap a row to write that note, tap it again to erase |
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
chord. Both follow the current chord: pick a **Giro** and they move through it, one
chord per bar, raising the third on the major chords so the harmony stays in key.
The picker names the chords it will actually play in your key, so `Tramonto` in A
reads `Am · F · C · G`.

| Giro | | Mode |
| --- | --- | --- |
| Fermo | one chord | natural minor |
| Tramonto | i · VI · III · VII | natural minor |
| Onda | i · VII · VI · VII | natural minor |
| Nostalgia | i · iv · VI · V | natural minor |
| Stornello | I · IV · V · I | major |
| Osteria | I · V · V · I | major |
| Tarantella | i · i · V · i | harmonic minor |

The mode belongs to the giro rather than to a switch of its own, because the two
have to agree: a natural-minor lead over a major chord sits a minor third on top
of a major one, which sours everything. Pick a major giro and the Lead's eight
rows become major without you doing anything.

**Lead** is the melody, two detuned sawtooths straight into the delay — or, with
**Suono** on *Fisa*, three square reeds a few cents apart under a slow bellows
wobble, which is most of what makes an accordion sound like an accordion. Select
it and the Pattern strip becomes eight rows — one per degree of the giro's scale
from the Key, root rows tinted so you can find the octave. Tap a row to
place a note, drag to draw a line, tap a lit cell again to erase. The lead stays
in the key's scale rather than transposing with the chords, which is what lets a
tune stay recognisable while the harmony moves under it.

### Grooves

The strip shows the four shared grooves plus whichever four belong to the pack
you have loaded. Shared grooves only ever trigger the first voice, unchopped and
at speed, so they work with any recordings.

**Shared.** Written from italo-disco idioms — the minor four-bar turnaround,
octave bass, off-beat open hat, dotted-eighth echo — not transcribed from any
particular record.

- **Italo** — 120 BPM, four-on-the-floor, off-beat open hat, claps on 2 and 4,
  octave bass on eighths, chord stabs on the off-beats, echo on.
- **Sunset** — 118 BPM, i–VI–III–VII, an eight-note lead arching up to the octave.
- **Passeggiata** — 108 BPM, i–iv–VI–V, half-time and wide: kick on 1 and 9 only,
  three long lead notes, and the whole spoken phrase unchopped underneath.
- **Corsa** — 134 BPM, i–VI–III–VII, sixteenth everything and a running lead.

**Clem.** Cut to those five clips.

- **Talk** — 84 BPM, swung and sparse, voices playing in full.
- **Chop** — 96 BPM, four voices sliced to two steps each.
- **Riviera** — 126 BPM, i–VII–VI–VII, sixteenth bass under a descending lead.
- **Notturno** — 104 BPM, i–iv–VI–V, slow and sparse, five notes in the bar.

**Nonni.** Accordion, no delay, and the bass on 1 and 3 with the chord answering
on 2 and 4 — the left hand of a box, oom and pah.

- **Stornello** — 100 BPM, I–IV–V–I in major, oom-pah, two voices trading.
- **Tarantella** — 142 BPM, i–i–V–i in harmonic minor, sixteenth hats, off-beat
  accordion, and a stuttered voice on the downbeat.
- **Osteria** — 108 BPM, I–V–V–I, swung, with the long clip sliced underneath.
- **Trastevere** — 84 BPM, I–IV–V–I, half-time and late, the long voice slowed to
  0.9× and given the whole bar to talk.

Patterns live in memory only, so they reset when the app is closed.
