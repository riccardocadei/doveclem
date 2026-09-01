# Dov’è Clem

A four-bar, 64-step drum machine built around voice memos. Eight synthesised voices — five
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
audio/kit/<kit>/*.m4a      one folder per drum kit
audio/instr/<id>/<midi>.m4a  recorded instruments, one file per note
tuning.html                a sample against a sine, for checking an octave
icons/*.png                home-screen and maskable icons
```

## The drums

**Macchina** is the synthesised set the app started with. **Tamburello** swaps
all five for recordings: a cajón bass tone for the kick, a cajón slap for the
snare, a hand clap, an egg shaker for the closed hat and a tambourine for the
open one.

They come from the [FreePats World Percussion](https://github.com/freepats/world-percussion)
library, which is CC0 — public domain, no attribution required. Crediting it
anyway seems right. Which recording went to which slot was decided by measuring
where each one's energy sits rather than by listening: the cajón bass tone puts
93% of itself under 250 Hz, the slap 89% in the mids, the shaker and the
tambourine 100% above 2.5 kHz. The per-slot gains then match each one's peak to
the synth drum it replaces, so switching kit changes the sound and not the
level. The whole kit is 24 KB.

A slot that fails to load quietly keeps its synthesised voice, so a bad
connection degrades the kit rather than silencing the drums.

## Why it stopped sounding like a ringtone

Every voice used to arrive dead centre, bone dry and straight into a
compressor, which is not a description of a bad synth — it is a description of
how a phone made sound in 2005. Three things were missing, and none of them is
about which notes you play:

**A room.** A convolution reverb whose impulse is generated rather than
recorded: noise decaying over 1.6 seconds, darkened, different in each ear.
Tracks feed it on a send the way they feed the delay, and how much is a
property of the voice — a clap and a chord stab go in wet, a kick and a bass
barely at all, because low things in a reverb are mud.

**A stage.** Every track has a fixed position. Kick, snare and bass stay in the
middle, where low and loud things belong; hats sit right of centre, claps and
chords left, the lead just right, the voices alternate. A mix that is entirely
mono is a mix that happened inside one speaker.

**Saturation.** A `tanh` curve across the master, which adds the harmonics a
desk adds and glues separate oscillators into one thing. It also takes the
peaks: a bar of Liana that used to clip now peaks 0.912 with nothing clipped at
all.

## Room tone

`air` is a bed of filtered noise about 48 dB down, running under everything for
as long as the app is making sound. It is not a recording of anyone's kitchen —
for the job it does, which is to stop the gaps between hits being digitally
empty, generated noise is the same thing and costs nothing. The acoustic bases
turn it on; the italo ones leave it off.

## Saving what you make

**Save** writes the whole state into this browser's `localStorage` under a name:
the pattern with its accents, every track's level, mute and echo send, the clip
trims, tempo, key, giro, instrument, filter, and whether one bar or four is
looping. The pack is stored by id, not by index, so reordering `PACKS` can never
load a pattern onto the wrong voices.

It is per browser and per device — nothing leaves the phone, and nothing is
shared between the installed app and the same site in Safari.

## Trimming the clips

A phone voice memo has dead air at both ends, and it is not digital silence —
it is room tone sitting 25 to 35 dB under the speech, so a single threshold
either keeps all of it or eats the consonant a word starts on. `trim-clips.py`
(one level up, outside the app) uses a two-threshold gate: find where the speech
certainly is, walk outwards to where it certainly is not, pad, and cut with a
short fade so there is no click where it lands in the room tone.

The two ends are not treated alike. An onset is abrupt and a tail fades, so the
tail gate sits twelve decibels lower and pads two and a half times as far. The
first version used one threshold for both and clipped the ends off two clips;
the heads are where nearly all the dead air was anyway.

It reads from `records/` and writes to `app/audio/`, so `records/` stays the
archive and the whole thing is reversible. Run `python3 app/tools/trim-clips.py
--dry-run` first: it prints what it would remove without touching anything.

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

## Measuring instead of guessing

`score.html` renders any groove through an `OfflineAudioContext` — the real
engine, the real nodes, no model of it — and prints numbers. It exists because
"does this sound less like a toy?" is not answerable by reading step arrays, and
reading step arrays was the whole of the old method. It is a development page,
not part of the app: it loads `index.html` in a hidden iframe and replaces
`Math.random` with a seeded generator, so two measurements of one groove differ
only by what actually changed in the code.

What it reports, and why each column exists:

- **somiglianza** — how alike two consecutive hits of the same velocity are,
  searching ±4 ms for the best alignment so a timing wobble cannot be mistaken
  for a timbre change. 1.000 is the same sample twice.
- **variazione picco** — how much the loudness of those same-velocity hits
  moves, as a percentage. Under 1% is a machine.
- **novità** — how much each bar differs from the one before it. Zero means
  four identical bars.
- **crest, picco, RMS, bande** — is it clipping, is it squashed, and where the
  energy sits across six bands.
- **batt/lev** — energy on the beat against energy on the off-beat eighths.
- **stereo** — correlation between the two channels. 1 is mono.

Two things it has already settled, both against what was about to be shipped:

**A compressor for the drum bus was rejected.** It had a confident comment about
how a disco kit breathes. From −14 dB to −32 dB and 3:1 to 6:1, the mix crest
moved by about a decibel, and on the synthesised kit it moved *up*: taking the
peaks off the drums let everything else through the saturation louder. It is not
in the file.

**A guessed makeup gain was 2.6 dB wrong** before the same page measured it,
which is the whole argument for the page in one line.

And one thing it says about the grooves that no amount of reading them would
have: **eleven of the sixteen score 0.07 or below on novità** — four bars that
are, to a spectrum analyser, the same bar four times. The two that score well
are the two written across all four bars instead of one bar tiled.

## Run it locally

A service worker needs a real origin, so serve it rather than opening the file:

```sh
cd app
python3 -m http.server 8000
# then open http://localhost:8000
```

## Keeping it to the family

There is a word on the door. Type it once and the phone remembers it.

**Be clear about what this is.** It is a door, not a lock. The repository is
public, so every clip also has a direct URL on `raw.githubusercontent.com` that
no password in a page can intercept, and anyone who opens the console can delete
the overlay. It stops somebody who is sent the link without the word. It stops
nobody who looks.

The larger half of the job is the `noindex, nofollow` meta on every page,
because the realistic way a stranger arrives at a small unlisted app is a search
engine, not a guess. A `robots.txt` would not have worked: the site is served
from a subdirectory of `riccardocadei.com` and crawlers only read `robots.txt` at
the domain root, which belongs to a different repository.

Real privacy would mean a private repository and hosting that can authenticate —
GitHub Pages cannot do the second (private Pages needs Enterprise), so it would
mean Cloudflare Pages with Cloudflare Access in front, which is free and would
put the audio behind the same login as the page. That is a different job from
this one.

**Changing the word.** The page holds a number, not the word, which keeps it out
of "view source" — the one thing this is actually meant to survive. It is not
cryptography and does not pretend to be: `Math.imul`-based, so it keeps working
when you test from the phone over plain http on the LAN, which `crypto.subtle`
would not. Paste this into any browser console with your word in the quotes,
lower case and no spaces, and put the result in `GATE` at the top of
`index.html`:

```js
(w=>{let a=0x811c9dc5,b=5381;for(let i=0;i<w.length;i++){const c=w.charCodeAt(i);
a=Math.imul(a^c,16777619)>>>0;b=(Math.imul(b,33)+c)>>>0}return a.toString(36)+'.'+b.toString(36)})('cicoria')
```

Changing it also logs everyone out, which is what you want: the stored value no
longer matches, so the door asks again.

The word is compared lower case and trimmed, so it survives being read out over
the phone. `score.html` and `tuning.html` are not behind the door — they are
development pages, they are `noindex` too, and gating them would add nothing
while the clips remain directly fetchable from the public repository.

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

The tracks live in three racks, each under the picker that decides what it is
played on: **Batteria** for the five drums, **Strumenti** for the bass, stab and
lead, **Voci** for the current pack's clips. It used to be one box called Mixer
with a header inside reading "Machine", which named neither the thing nor what
the picker two inches away would do to it.

Each chip carries the pattern as dots — one per beat across four bars, or one
per step in a short bar, with the ones outside the loop dimmed. The tall bright
dot is the playhead, and a chip tints as it fires, so you can see what is making
the sound. Tap a chip to select and hear it; the bar down its right edge mutes.

| Control | What it does |
| --- | --- |
| Play / Space | Start and stop the sequencer |
| BPM ± | Tempo, 50–200 |
| Filtro | One lowpass across the whole record, 200 Hz to wide open. The echo returns through it too |
| 4/4 · 3/4 · 6/8 | The metre, beside the tempo. A bar is sixteen steps in common time and twelve in the other two — but a waltz is three beats of four and 6/8 is two beats of three, which is the whole difference between them |
| 1 bar · 4 bars | How many bars go round |
| Batteria | The drums: the synthesised **Macchina**, or **Tamburello** — a real cajón, tambourine, shaker and hand claps. It sits in the header of the rack it governs |
| Strumenti | Bass, stab and lead: Synth italo, Fisarmonica, Mandolino, Rhodes, Organo |
| Bar 1–4 | Which bar the Pattern lane is showing. The playhead marks the bar it is in, so you can edit one bar while another plays |
| Key | Opens a one-octave keyboard — tap a note to set the root for Bass, Stab and Lead, and hear it |
| Giro | Four-bar chord move the Bass and Stab follow; **Fermo** stays on the root. The giro also picks the Lead's scale |
| Pattern | Tap a step to write it, tap it again to clear it, drag to paint a run or to erase one. **Hold** a written step to walk it round: normal, accent, ghost |
| Pattern (Lead) | Eight rows of the giro's scale — tap a row to write that note, tap it again to erase |
| Volume | Per-track level |
| Echo | How much of that track feeds the delay. There is no master echo switch — it is per instrument |
| More | Opens the rest of the panel — Speed and playback direction |
| Arp / Chord | Bass walks the intervals one per hit; Stab plays them together |
| Speed | Playback rate, 0.4×–2.2× — changes pitch along with tempo |
| Waveform | Drag the two handles to set where the clip starts and ends. Press anywhere and the nearer handle comes to you; arrow keys nudge, Shift+arrow finer |
| Chop | Snaps the end to 1, 2, 4 or 8 steps, or Full |
| Forward / Reverse | Sample direction — the waveform mirrors so you are still looking at what you hear |
| Cut / Overlap | Whether re-firing a voice stops the one already playing or lets them stack |
| Record | Captures whatever is playing, for as long as you leave it running. Trim the result on its wave; **Save** writes a WAV — shared on a phone, downloaded on a desktop |
| Copy bar | Puts the bar you are looking at over the other three |
| Hold a track | Solo it. Hold again to let the rest back in |
| Save | Keeps the whole state under a name, in this browser: pattern, mix, clip trims, tempo, key, giro and instrument. Saved ones appear under the presets |
| Keys 1–9 | Trigger the first nine tracks from a keyboard |

### Metre and length

Two settings, and they sit apart on purpose. The **metre** is next to the
tempo, because it belongs to the music rather than to the bar you happen to be
editing. The **bar count** is over the pattern, because that is what it is
about.

Three metres, and the lane draws each one differently:

```
4/4   B...b...b...b...    1···2···3···4···    four beats of four
3/4   B...b...b...        1···2···3···        three beats of four
6/8   B.b.b.B.b.b.        1·2·3·4·5·6·        two beats of three
```

Three-four and six-eight are both twelve sixteenths and they are not the same
bar. The gaps are the entire difference: 4+4+4 against 6+6. Getting that wrong
is easy and I did it twice before it was right — twelve steps grouped in threes
draws four dotted-eighth beats, twelve in a 4/4 grid draws a common-time bar
somebody cut short, and neither of those is 6/8.

### Four bars

The pattern is 64 steps — four bars of sixteen. It used to be one bar, which
meant the drums, the bass and the lead all repeated underneath a giro that
moved through four chords, and that mismatch is most of why a groove read as a
loop rather than a piece. Now the two line up: bar 1 sits on the first chord,
bar 4 on the fourth.

The lane shows one bar at a time, picked with the four buttons above it; the
mixer shows all sixty-four steps at once, a dot per beat, because sixty-four
dots on a mixer chip would be under two pixels each. Tiling is decided **per lane**. A lane written inside the first bar is repeated
across the rest; one that names a step beyond it is taken as authored, which is
how a pattern earns a fill or a bar that drops out. Deciding it for the whole
pattern is a trap: a single voice dropped at step 40 switched tiling off for the
drums as well, and Trastevere played one bar followed by three of silence. **Liana** is the one authored across the whole pattern — a four-bar lead,
a stab that sits out the last half bar, a fill into the top. Put it next to any
of the others and the difference is the point of the change.

### Accents

A step holds a velocity rather than a flag, because identical hits are a good
part of what makes a machine sound like one. **Hold** a written step to walk it
round — normal, accent, ghost.

This was on a plain tap at first, and that was a mistake: tapping a written step
has meant "clear it" since the first version, so the change quietly produced two
shades of lit step with no way to tell where they had come from. Tap clears,
hold accents, drag still paints and erases.

### Swing

Swing pushes the second half of every pair late. It works on the **eighths** —
steps 3, 7, 11, 15 counting from one — because that is what these patterns are
built from. An earlier version pushed only the odd sixteenths, which is the
textbook definition and was completely inaudible here: every groove that shipped
with Swing already on had nothing on an odd step at all. Sixteenths now stay
centred inside whichever eighth they belong to, so a sixteenth pattern shuffles
along instead of stacking up and crashing into the downbeat.

Full swing puts the off-beat two thirds of the way through the beat, the triplet
feel; the grooves that use it sit a little over half of that.

Swing has no button. Neither does the sidechain, and the delay has no master
switch. Three toggles whose effect was hard to hear had accumulated on one row;
swing and the sidechain are per groove now — a groove that wants a shuffle or a
pumping bass asks for one — and how much of a track reaches the delay is that
track's own Echo send.

### Four bars that are actually four bars

`score.html` measured every groove's bar-to-bar novelty and eleven of the
sixteen came back at 0.07 or under, which is a spectrum analyser saying "this is
one bar played four times". Three things fixed it, and the third one was not
what anybody expected.

**A fill.** `fill` is one bar of steps that replaces the lanes it names, on the
last bar of the pattern, every second time round — so every eight bars. It is
not baked into the pattern, because four bars cannot hold an every-other-time
event, and the transport says `· fill` while it plays. Fills never name the
kick: the kick is the thing you are filling *against*.

**`vary`.** A per-bar edit list, applied when the groove loads rather than while
it plays, so what it does lands in the lane where you can see it and change it.
`drop` silences a lane for that bar, `clear` removes named steps, `add` writes
them, `accent` and `ghost` re-weight them. Bars count from zero and the steps
inside are relative to the bar. A dance hall thins its hats to quarters in bar
three and sends the clap home; a tambourine loses two beats and then rolls.

**The clips were restarting every bar.** This was the big one. A voice lane
written as a single step inside bar one gets tiled across all four — which is
right for a chopped syllable and wrong for a sentence, because the sentence
starts again from the top every bar and gets cut off mid-word. Four grooves were
doing it. Fixing Talk alone took its novelty from 0.01 to 0.55.

Which lanes needed it was arithmetic, not taste: a clip is 1.3 to 7.2 seconds,
a bar is 1.9 to 2.9 depending on the tempo, and anything longer than its bar
cannot be retriggered every bar. Clips longer than two bars now use `once`,
which says "do not repeat this lane" in words — the only way to say it before
was to put a step number bigger than sixteen somewhere in the lane, and a phrase
that should start once per turn has no such step to place.

Across the sixteen grooves the median novelty went from 0.06 to 0.22, the worst
from 0.00 to 0.09, and nothing peaks above −0.4 dBFS.

**The bass is a line now, not a counter.** Its arpeggio degree used to come from
how many times the bass had fired since Play, so the line was a function of hit
count rather than of position: any pattern that was not a uniform division
drifted against the giro and never came back. It counts the written hits before
the current step instead, which makes it the same line every time the giro comes
round. A groove can also name its own intervals with `bassIv` — `[0,12,0,7]`,
root, octave, root, fifth, is the italo-disco bassline and two of them use it.

### No two hits the same

Accents and ghosts give a step three loudnesses, and for a long time that was
the whole of the machine's humanity: in a bar of sixteen hi-hats there were two
amplitudes, and every one of those hats was, sample for sample, the identical
waveform. It had to be. Every noise voice in the file read the same one-second
buffer of noise from sample zero, so two hats in a row were not similar, they
were the same file played twice.

Three things changed, and all three are small:

**Each hit reads the noise from a random offset.** One line. It is the largest
audible difference in this list.

**Each hit wobbles.** A few per cent on a gain, a few hertz on a filter, a few
milliseconds on a decay — `jit()`. Small enough that no single hit sounds wrong,
large enough that sixteen in a row stop sounding like one. The accordion had
this from the day it was written; the drums did not.

**Each track leans.** A snare lands 7 ms behind the grid, a clap 6, a hat 2 or 3
in front of it, and the kick and the bass do not move at all, because they are
the clock. On top of that every hit gets a wobble of a couple of milliseconds.
It is per groove, like swing, and it has no button.

None of it is guesswork. `score.html` measures how alike two consecutive hits
of the same velocity actually are, and on the synthesised kit the number went
from 0.98–1.00 to 0.13–0.32, where 1.000 means the same sound twice. On the
recorded kit it went from 0.99–1.00 to 0.41–0.99, which is honest and much less
good: a sampled one-shot has no envelope to jitter, and per-cent changes of
gain and playback rate barely decorrelate a low, short recording. The real
answer there is two or three takes per slot to alternate between, which is what
the TODO has been saying about recording our own percussion all along.

The snare, the clap and the hats were also rebuilt while this was going on — a
second head mode and a two-stage rattle on the snare, a fourth unevenly-spaced
burst on the clap, five inharmonic square partials under the cymbals, because
metal does not ring at whole-number ratios and noise through a highpass is a
"tss", not a struck thing. Those are new sounds rather than humanising, and
there is no switch to put them back.

### The in and out points

A clip is trimmed on its own waveform: drag the left handle to move where the
trigger begins, the right one to set where it stops. Press anywhere in the strip
and the nearer handle comes to the touch, so there is no thin line to hit.

The out point is stored as a **length in steps**, not as a number of seconds.
That is deliberate: it means a chopped voice stays in time when you move the
tempo, which is the whole reason chopping speech works as rhythm. Nudge the BPM
and the right handle walks with the grid. **Chop** is the same setting with
preset values — 1, 2, 4, 8 steps or Full.

A voice is monophonic by default: firing it again cuts whatever it was saying,
the way a sampler pad does. **Overlap** lets it stack on itself instead, which is
what you want when a phrase is longer than the gap between its triggers.

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

**Lead** is the melody. What it is played on is the **Strumento** picker, which
moves the Stab and the Bass with it:

| | |
| --- | --- |
| Synth italo | Detuned sawtooths straight into the delay |
| Fisarmonica | A recorded Hohner button accordion — eight notes, the rest repitched between them, never more than two semitones. The synthesised reeds remain as the fallback if the notes do not load |
| Chitarra | A recorded Spanish classical guitar — eleven notes from A1 to B5, the only sampled instrument that reaches low enough to play the bass too. Chords are strummed: the notes of one arrive as a hand crosses the strings |
| Mandolino | Karplus-Strong, the one instrument here still modelled: a burst of noise going round a loop one period long, losing its top on every pass. No CC0 mandolin exists to record from |
| Rhodes | A struck tine — a sine body under a bright partial that dies at once |
| Organo | Drawbars at whole multiples of the note, held flat, under a Leslie tremolo |

All four are levelled against each other, so changing instrument changes the
sound and not the volume. Select
it and the Pattern strip becomes eight rows — one per degree of the giro's scale
from the Key, root rows tinted so you can find the octave. Tap a row to
place a note, drag to draw a line, tap a lit cell again to erase. The lead stays
in the key's scale rather than transposing with the chords, which is what lets a
tune stay recognisable while the harmony moves under it.

### Patterns

They are called **basi** — backing tracks — rather than grooves, because a
groove is a rhythmic feel and these are more than that: each one carries the
pattern, the tempo, the key, the four-bar giro, the instrument, the mix and the
clip trims. Loading one replaces everything.

Eight per pack, ordered by how finished they sound — a structural judgement,
not a verdict on taste; reorder them freely, it is one array.

**There is no such thing as a base that does not care which voices are loaded.**
Four of these used to be shared between the packs, and a shared base can only
ever touch `v0`, whole and unchopped, because that is all any pack is
guaranteed to have — which is the weakest possible use of the one thing this
app is for. Every base belongs to a pack now. Where two packs have a base with
the same name the machine underneath is the same; what it does with the talking
is not. Clem's *Liana* states Clementina twice and lets Marco answer in the
third bar; Nonni's chops "Ho un disturbo" into the beat and drops "A Già, sta
zitto" across the break.

| | BPM | Drums | Instrument | Voices |
| --- | --- | --- | --- | --- |
| Liana | 118 | machine · folk | Synth italo | Clementina whole / Disturbo chopped |
| Balera | 126 · 112 | machine · folk | Rhodes · Fisarmonica | two long clips whole |
| Notte | 104 | machine | Organo | one whole, one chopped |
| Discoteca *(clem)* | 124 | machine | Synth italo | Theory whole under the beat |
| Campagna *(nonni)* | 92 | folk | Mandolino | the two longest, whole |
| Riviera *(clem)* | 126 | machine | Synth italo | Marco chopped |
| Coro *(clem)* | 104 | folk | Rhodes | Clementina, doubled |
| Chop *(clem)* | 96 | machine | Synth italo | four, sliced to two steps |
| Talk *(clem)* | 84 | machine | — | two, whole |
| Stornello *(nonni)* | 100 | folk | Mandolino | whole and chopped |
| Osteria *(nonni)* | 126 | folk | Fisarmonica | two long clips whole |
| Trastevere *(nonni)* | 88 | folk | Mandolino | two, whole |
| Tarantella *(nonni)* | 96 · 6/8 | folk | Fisarmonica | one, stuttered |

Five names exist in both packs with the same machine under them and different
talking on top. **Long clips are left whole** — a four-second recording running
across four bars is a vocal; the same recording cut into eighths is confetti.

Five of them were rewritten again after listening notes, and the reasons are
worth keeping:

- **Autostrada** was a carousel. 132 BPM with sixteenth hats, a sixteenth bass
  *and* a lead running over both. The lead is gone, the bass is eighths with a
  pickup into each bar, and it is eight BPM slower.
- **Coro** had no chorus in it and sat too low to hear anything. It is up a
  fourth, on an octave bass, and the voice now genuinely sings with itself —
  three copies a few cents apart and a few milliseconds late, which is the only
  way to get several people saying the same words when a track holds one clip.
- **Osteria** sounded like a pop song. A tavern has no snare drum: hands clap
  along on two and four, the tambourine rolls underneath, the accordion fills
  every gap.
- **Trastevere** read as broken because it was — hits on 1, 7, 11, 13 and 15 and
  nothing on two, so there was no pulse to be sparse against.
- **Tarantella** was not one, twice over. A tarantella is in 6/8 and the app
  could only count to sixteen, so the first version was a fast 4/4 wearing the
  name; the second had the twelve steps but grouped them in threes, which draws
  four dotted-eighth beats and is a different metre again. It is two beats of
  three eighths now: cajón on the two downbeats, tambourine on the six eighths
  with only the beats struck hard, hands on the third of each group.
- **Sanremo** never worked and is gone. **Carosone** takes its place — swung
  eighths, a walking bass, and the piano stabbing the off-beat instead of
  landing on it, over a minor giro with a major dominant, which is where that
  music lives.

**Breaks.** Liana and Carosone each lose a bar: in Liana's third the kick and
claps step out and the bass carries it alone, in Carosone's the whole rhythm
section drops and the Rhodes plays a chorus by itself. Four bars that all do
the same thing are a loop; four where one of them stops are an arrangement.

Every one of them uses accents and ghost notes — a backbeat that leans, hats
with every other sixteenth lightened. An unaccented pattern is a metronome
whatever is playing on it.

A base can declare `accent:{ kick:[0,32] }` and `ghost:{ hat:[...] }` alongside
its steps; both tile across the four bars the same way the steps do.

Patterns live in memory only, so they reset when the app is closed.
