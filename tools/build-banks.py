#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cut the sampled instrument banks and the folk kit out of FreePats archives.

Everything this fetches is CC0, the same as the accordion and the guitar that
were already here, so nothing in app/audio/ carries an attribution condition.
The archives are tens of megabytes and the app needs a couple of hundred
kilobytes of them, so this is a build tool and not a dependency: it runs once,
writes m4a into app/audio/, and the result is what ships.

Bitrate: 160k, not the 96k this started at. Ninety-six is plenty for a phone
recording of somebody talking, which is what the voice packs are and why
trim-clips.py stays there; it is not plenty for a plucked nylon string or for a
tambourine playing every step of a tarantella, where what it smears is exactly
the transient that makes the instrument recognisable. It costs about half a
megabyte across every bank here.

Three things come out of it.

  bass   a fingered Yamaha RBX electric bass, seven notes E1 to D#2. The bank
         is one octave because that is what was sampled; index.html folds any
         note above D#2+4 down an octave rather than stretching a bass string
         past where a bassist would have moved hand position anyway.

  brass  Synth Brass 2, which is a DX7 BRASS 7 through Dexed. This is the
         italo-disco stab, and it is the one sound this app could not fake:
         an FM brass patch is six operators, not two oscillators and a filter.

  organ  setBfree's Hammond emulation, ten notes every major third from C3 to
         C6. Five sine drawbars is what an organ is on paper and it is not what
         one sounds like: the tonewheels leak into each other, the drawbars are
         not pure, and the Leslie moves. The samples carry all three, and the
         slow swell in them is a real rotor rather than the one LFO the
         synthesised version had. Two and a bit seconds is the longest hold
         `playFor` will ever ask for.

  folk   three takes per drum slot instead of one. This is the fix for the
         thing score.html has been reporting since the folk kit landed —
         normalised correlation put the recorded kit at 0.4 to 1.0 hit to hit
         against the machine kit's 0.13 to 0.32, because a one-shot played
         twice is the same waveform twice and no amount of rate jitter moves
         a normalised correlation. Round robin moves it; jitter never could.

         Each take is peak-matched to the single file it replaces, so the gains
         measured into KITS.folk.slots stay valid and variety is the only
         thing that changed.

    python3 app/tools/build-banks.py            # write
    python3 app/tools/build-banks.py --dry-run  # just the table
"""
import array, math, os, shutil, subprocess, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
AUDIO = os.path.join(ROOT, 'app', 'audio')
CACHE = os.path.join(tempfile.gettempdir(), 'doveclem-freepats')
BITRATE = '160k'   # see the note under "Bitrate" in the docstring
SR = 48000

SRC = {
    'bass':  ('https://github.com/freepats/electric-bass-YR/releases/download/'
              '2019-09-30/FingerBassYR-SFZ+FLAC-20190930.7z',
              'FingerBassYR SFZ+FLAC-20190930'),
    'brass': ('https://github.com/freepats/synth-brass-2/releases/download/'
              '2024-06-10/SynthBrass2-SFZ+FLAC-20240610.7z',
              'SynthBrass2 SFZ+FLAC-20240610'),
    'world': ('https://github.com/freepats/world-percussion/releases/download/'
              '2020-09-05/WorldPercussion-SFZ+FLAC-20200905.7z',
              'WorldPercussion SFZ+FLAC-20200905'),
    # This one is not on GitHub and is a tar.xz rather than a 7z; fetch() reads
    # the extension off the URL rather than assuming.
    'organ': ('https://freepats.zenvoid.org/Organ/DrawbarOrganEmulation/'
              'DrawbarOrganEmulation-SFZ-20190712.tar.xz',
              'DrawbarOrganEmulation-SFZ-20190712'),
    # The guitar and the accordion were cut by hand before this script existed,
    # which meant they were the two banks it could not re-encode. They are here
    # now so every sampled instrument comes from one place at one bitrate.
    'chit':  ('https://github.com/freepats/spanish-classical-guitar/releases/'
              'download/v1.0.0/SpanishClassicalGuitar-20190618.zip',
              'SpanishClassicalGuitar-20190618'),
    'fisa':  ('https://github.com/freepats/button-accordion-HN/releases/'
              'download/2024-03-29/ButtonAccordionHN-SFZ%2BFLAC-20240329.7z',
              'Button Accordion HN SFZ+FLAC-20240329'),
}

# midi -> file in the bass bank. Every two semitones: the bank is chromatic, but
# a whole tone of stretch is inaudible on a bass and halves what we ship.
BASS = {28:'E', 30:'F#', 32:'G#', 34:'A#', 36:'C', 38:'D', 39:'D#'}
# midi -> file. The bank's own keycentres, which is where it is not stretched.
BRASS = {42:'F#2', 48:'C3', 54:'F#3', 60:'C4', 66:'F#4', 72:'C5', 78:'F#5'}
# Every major third, which is what was recorded, so nothing stretches more than
# two semitones. That matters more here than on the other banks: the Leslie is
# inside the recording, so a rate change is also a rotor-speed change, and three
# notes of a chord swirling at three different speeds is not a chord.
ORGAN = {48:'C3', 52:'E3', 56:'G#3', 60:'C4', 64:'E4', 68:'G#4',
         72:'C5', 76:'E5', 80:'G#5', 84:'C6'}
# Eleven notes, A1 to B5: the only bank that reaches low enough to play the bass.
CHIT = {33:'A1', 38:'D2', 43:'G2', 48:'C3', 52:'E3', 57:'A3',
        62:'D4', 67:'G4', 72:'C5', 77:'F5', 83:'B5'}
# The bank's own eight, so nothing is stretched more than two semitones.
FISA = {59:'B3', 62:'D4', 66:'F#4', 69:'A4', 72:'C5', 76:'E5', 79:'G5', 83:'B5'}

# slot -> (folder, the pool the SFZ round-robins over, peak dBFS and length of
# the single file being replaced). TAKES of the pool are chosen by measurement,
# not by list order: three consecutive strikes of the same cajon are three very
# similar recordings, and picking the first three off the top was how the first
# version of this ended up moving the number far less than it could have.
# Peak and length both come from the file already in app/audio, so round robin
# is the only variable that moves — a longer shaker take would read as a
# different mix, not as a second hand.
TAKES = 3
KIT = {
    'kick':  ('CajonFlamenco', ['101', '102', '216', '201', '214', '104', '219',
                                '105', '103', '221', '202'],      0.00, 0.384),  # bass tone
    'snare': ('CajonFlamenco', ['106', '107', '109', '110', '115', '203', '206',
                                '205', '212', '111', '204'],     -0.10, 0.299),  # slap
    'clap':  ('HandClap',      ['01_02', '01_03', '01_05', '01_06', '01_07',
                                '01_08', '01_09', '02_02', '02_05'], -0.30, 0.320),
    'hat':   ('EggShaker',     ['fast_02', 'fast_03', 'fast_04', 'fast_06',
                                'fast_07', 'fast_08', 'fast_09'], -7.75, 0.128),
    'ohat':  ('Tambourine',    ['01_01', '02_01', '03_01', '04_01', '05',
                                '06', '07', '08'],               -0.82, 0.341),
}

def sh(args):
    return subprocess.run(args, capture_output=True, check=True).stdout

def fetch():
    os.makedirs(CACHE, exist_ok=True)
    for key, (url, folder) in SRC.items():
        out = os.path.join(CACHE, folder)
        if os.path.isdir(out):
            continue
        ext = ('.tar.xz' if url.endswith('.tar.xz')
               else '.zip' if url.endswith('.zip') else '.7z')
        arc = os.path.join(CACHE, key + ext)
        if not os.path.exists(arc):
            print('fetching %s ...' % key)
            urllib.request.urlretrieve(url, arc)
        if ext == '.tar.xz':
            sh(['tar', 'xJf', arc, '-C', CACHE])
        elif ext == '.zip':
            # this one has no top folder of its own, so give it the one we expect
            sh(['unzip', '-q', '-o', arc, '-d', out])
        else:
            sh(['7zz', 'x', '-y', '-o' + CACHE, arc])

def find(folder, *parts):
    """The archives disagree about extension and about layout: some keep their
    samples in a `samples/` folder, the accordion keeps them at the top and
    prefixes every filename with the instrument's name."""
    root = os.path.join(CACHE, SRC[folder][1])
    stems = [os.path.join(root, 'samples', *parts), os.path.join(root, *parts)]
    if folder == 'fisa':
        stems.append(os.path.join(root, 'Button Accordion HN ' + parts[-1]))
    for base in stems:
        for ext in ('.flac', '.wav'):
            if os.path.exists(base + ext):
                return base + ext
    raise SystemExit('missing sample: ' + stems[0])

def pcm(path):
    raw = sh(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR),
              '-f', 's16le', '-'])
    a = array.array('h'); a.frombytes(raw)
    return a

def peak_db(a):
    p = max(abs(x) for x in a) / 32768.0 if len(a) else 0.0
    return 20 * math.log10(p) if p > 0 else -99.0

def onset(a, thresh_db=-42.0):
    """Where the strike is. A percussion recording has room in front of it."""
    pk = max(abs(x) for x in a) / 32768.0
    if pk <= 0:
        return 0
    lim = pk * 10 ** (thresh_db / 20) * 32768
    for i in range(0, len(a) - 240, 240):
        if max(abs(x) for x in a[i:i + 240:4]) >= lim:
            return max(0, i - 240)          # 5 ms of run-up, no clicked onset
    return 0

def corr(a, b):
    """Normalised correlation at the best alignment within a few milliseconds.

    The same measure score.html uses hit to hit, and the reason it is the one
    that matters: it ignores gain, so it cannot be fooled by the rate and level
    jitter the engine already applies. 1.0 is the same recording twice."""
    n = min(len(a), len(b), 6000)
    best = 0.0
    for lag in range(-96, 97, 12):
        x = a[max(0, lag):max(0, lag) + n]
        y = b[max(0, -lag):max(0, -lag) + n]
        m = min(len(x), len(y))
        if m < 1000:
            continue
        num = sum(float(x[i]) * y[i] for i in range(0, m, 3))
        da = math.sqrt(sum(float(x[i]) ** 2 for i in range(0, m, 3)))
        db = math.sqrt(sum(float(y[i]) ** 2 for i in range(0, m, 3)))
        if da and db:
            best = max(best, abs(num) / (da * db))
    return best


def pick_takes(pool, want):
    """The `want` takes that sound least like each other.

    Greedy: keep the loudest as the anchor, then repeatedly add whichever
    candidate correlates least with the ones already chosen. Exhaustive would
    be eleven-choose-three and no better — the spread between the best triple
    and a good one is inside the noise, and this runs in seconds."""
    cut = {}
    for stem, a in pool:
        st = onset(a)
        cut[stem] = a[st:st + 8000]
    chosen = [pool[0][0]]
    while len(chosen) < want:
        rest = [s for s, _ in pool if s not in chosen]
        if not rest:
            break
        worst = {s: max(corr(cut[s], cut[c]) for c in chosen) for s in rest}
        chosen.append(min(rest, key=lambda s: worst[s]))
    return chosen


def write(src, dst, start, dur, gain_db, dry):
    if dry:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    af = 'volume=%.2fdB,afade=t=out:st=%.3f:d=0.008' % (gain_db, max(0, dur - 0.008))
    sh(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ss', '%.4f' % start,
        '-t', '%.4f' % dur, '-af', af, '-ac', '1', '-ar', str(SR),
        '-c:a', 'aac', '-b:a', BITRATE, dst])

def main(dry):
    fetch()
    rows = []

    # ---- the pitched banks ----
    for name, table, folder, sub, hold in (
            ('bass',  BASS,  'bass',  ('finger',), 1.30),
            ('brass', BRASS, 'brass', (),          1.80),
            ('organo', ORGAN, 'organ', (),         2.20),
            ('chit',   CHIT,  'chit',  (),         1.80),
            ('fisa',   FISA,  'fisa',  (),         1.50)):
        for midi, stem in sorted(table.items()):
            src = find(folder, *(sub + (stem,)))
            a = pcm(src)
            dur = min(hold, len(a) / float(SR))
            dst = os.path.join(AUDIO, 'instr', name, '%d.m4a' % midi)
            write(src, dst, 0.0, dur, 0.0, dry)
            rows.append((name + '/' + str(midi), stem, dur, peak_db(a)))

    # ---- the folk kit, three takes a slot ----
    for slot, (folder, pool, want_db, want_len) in KIT.items():
        loaded = [(stem, pcm(find('world', folder, stem))) for stem in pool]
        takes = pick_takes(loaded, TAKES)
        for n, stem in enumerate(takes, 1):
            src = find('world', folder, stem)
            a = dict(loaded)[stem]
            st = onset(a) / float(SR)
            dur = min(want_len, len(a) / float(SR) - st)
            # match the file it replaces, so the measured slot gains still hold
            gain = want_db - peak_db(a)
            dst = os.path.join(AUDIO, 'kit', 'folk', '%s-%d.m4a' % (slot, n))
            write(src, dst, st, dur, gain, dry)
            rows.append(('folk/%s-%d' % (slot, n), stem, dur, want_db))

    print('%-16s %-12s %7s %8s' % ('out', 'from', 'sec', 'peak dB'))
    for r in rows:
        print('%-16s %-12s %7.3f %8.2f' % r)
    print('\n%d files %s' % (len(rows), 'listed (dry run)' if dry else 'written'))

    if not dry:
        for slot in KIT:
            old = os.path.join(AUDIO, 'kit', 'folk', slot + '.m4a')
            if os.path.exists(old):
                os.remove(old)
                print('removed superseded ' + os.path.relpath(old, ROOT))

if __name__ == '__main__':
    main('--dry-run' in sys.argv)
