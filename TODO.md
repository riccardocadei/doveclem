# Not done yet

## Generated phrases in the pack's own voice

**Status: parked, because it cannot be free.**

The idea: a box where you type a sentence, it comes back spoken in the loaded
pack's voice, and lands in the session as another voice track — so the pack is
not capped at five or seven things somebody once said.

It is worth doing. With seven clips the expressive ceiling arrives fast and
improvisations get repetitive, which is a real limit on what the app is for.

### Why it is parked

The blocker is not difficulty, it is money, and specifically *whose*.

- **Voice cloning is a metered, paid API.** The free tiers of the services that
  do it either exclude cloning or give a few thousand characters a month.
- **A public page has unbounded usage.** "Any visitor can type a phrase" means
  strangers spending the account owner's quota. One link shared in a group chat
  empties a month in an afternoon. A password limits who can *reach* the page,
  not how much the people who do can spend.
- **Free TTS exists but is the wrong thing.** The browser's own
  `speechSynthesis` needs no backend and no key, but it is a generic system
  voice. It is not the nonni, and the nonni are the point.

So it needs a paid API key on somebody's card. That is a decision for whoever
owns the card, not something to build first and mention after.

### What is *not* the hard part

For the record, so this is not re-litigated:

- **The backend is easy and free.** A Cloudflare Worker: about thirty lines,
  holds the key as a secret, checks the password, calls the API, caches the
  result so the same sentence is never billed twice. Free tier is 100,000
  requests a day. Nothing to keep running.
- **The app side is small.** `loadPack()` already takes either `b64` or `url`,
  so a generated phrase is just another buffer. The waveform handles, Chop,
  Repeat and the mixer all work on it with no changes.

### If it goes ahead

1. Consent from the people whose voices they are. The services require you to
   hold the right to clone the voice, and here that means actually asking.
2. A key, on a paid plan, and a spending cap on the account.
3. Worker: `POST /say {text}` → password check → rate limit per session →
   cache lookup → API → store → return audio.
4. App: a "+" slot in the mixer that opens a text field, posts, and adds the
   result as a voice track for the session. Saving it into the pack for good is
   a second step and means committing the file to the repo.
5. Default password `riccardo`, held as a Worker secret, never in the page.

## Cheaper things worth doing first

- **Record your own percussion.** A CC0 cajon, tambourine, shaker and hand claps ship as the Tamburello kit now, but they are somebody else's room and somebody else's hands. The original point stands: A tambourine, hands on a table, a wooden spoon on a
  pot — six or eight one-shots on a phone. The drums are synthesised and a real
  accordion over a drum machine still sounds synthetic. Half an hour of work,
  and it is the biggest single lift left.
- **A real accordion**, if anyone in the family has one. Three recordings — a
  major chord, a minor chord, a bass note — beat any synthesis in this file.
  The engine already repitches samples, so the machinery exists.
- **Room tone.** Thirty seconds of the actual kitchen, under everything at a
  very low level. Synthesis and recordings glue together when they share a room.
- **Save and load patterns.** Everything resets when the app closes. Nothing to
  do with audio, and probably the most missed feature after ten minutes of use.
