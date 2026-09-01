#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trim the dead air off every clip in app/audio/, reading from records/.

The empty space at the head and tail of a phone voice memo is not digital
silence — it is room tone sitting 25 to 35 dB under the speech. A single
threshold either keeps all of it or eats the soft consonant a word starts on,
so this uses a two-threshold gate: find where the speech certainly is (HI),
then walk outwards to where it certainly is not (LO), and pad from there.

records/ is the archive and is never written to, so this is reversible: delete
app/audio/<pack> and run build again.

The map of source to destination is clips.json, which sits beside this file and
is used unless another one is named. It used to be a required argument that the
usage lines here forgot to mention, so following them gave an IndexError rather
than a table.

    python3 app/tools/trim-clips.py            # write
    python3 app/tools/trim-clips.py --dry-run  # just the table
"""
import array, io, math, os, subprocess, sys

SR, HOP = 48000, 480               # 10 ms analysis window
HI_DB = -20.0                      # relative to the clip's own peak
LO_IN, LO_OUT = -33.0, -45.0       # a tail fades; an onset does not
PAD_IN, PAD_OUT = 0.040, 0.250     # and it needs more room after it
FADE = 0.008                       # no click where we cut into room tone
BITRATE = '96k'

HERE = os.path.dirname(os.path.abspath(__file__))
# the project root, two levels above app/tools — records/ and app/ live there
ROOT = os.path.dirname(os.path.dirname(HERE))

def pcm(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1',
                          '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    a = array.array('h'); a.frombytes(raw)
    return a

def envelope(a):
    out = []
    for i in range(0, len(a) - HOP + 1, HOP):
        m = 0
        for j in range(i, i + HOP, 4):
            v = abs(a[j])
            if v > m: m = v
        out.append(m / 32768.0)
    return out

def bounds(env):
    """Where the speech is, in seconds."""
    pk = max(env) if env else 0.0
    if pk <= 0: return None
    hi = pk * 10 ** (HI_DB / 20)
    lo_in, lo_out = pk * 10 ** (LO_IN / 20), pk * 10 ** (LO_OUT / 20)
    loud = [i for i, v in enumerate(env) if v >= hi]
    if not loud: return None
    i, j = loud[0], loud[-1]
    while i > 0 and env[i - 1] >= lo_in: i -= 1       # back out to the onset
    while j < len(env) - 1 and env[j + 1] >= lo_out: j += 1
    n = len(env) * HOP / float(SR)
    return max(0.0, i * HOP / float(SR) - PAD_IN), min(n, (j + 1) * HOP / float(SR) + PAD_OUT)

def cut(src, dst, a, b):
    d = b - a
    af = 'afade=t=in:st=0:d=%.3f,afade=t=out:st=%.3f:d=%.3f' % (FADE, max(0, d - FADE), FADE)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ss', '%.3f' % a,
                    '-t', '%.3f' % d, '-af', af, '-ac', '1', '-ar', str(SR),
                    '-c:a', 'aac', '-b:a', BITRATE, dst], check=True)

def main(pairs, dry):
    print('%-34s %7s %7s %7s %7s' % ('clip', 'was', 'head', 'tail', 'now'))
    saved = 0.0
    for src, dst in pairs:
        a = pcm(src)
        dur = len(a) / float(SR)
        bd = bounds(envelope(a))
        if not bd:
            print('%-34s %7.2f %7s %7s %7s  (silent, left alone)'
                  % (os.path.basename(dst)[:34], dur, '-', '-', '-'))
            continue
        i, j = bd
        if not dry: cut(src, dst, i, j)
        saved += dur - (j - i)
        print('%-34s %7.2f %7.2f %7.2f %7.2f' % (os.path.basename(dst)[:34], dur, i, dur - j, j - i))
    print('\n%.2f s of dead air removed across %d clips%s'
          % (saved, len(pairs), ' (dry run, nothing written)' if dry else ''))

if __name__ == '__main__':
    import json
    named = [a for a in sys.argv[1:] if not a.startswith('--')]
    mapfile = named[0] if named else os.path.join(HERE, 'clips.json')
    pairs = json.load(io.open(mapfile, encoding='utf-8'))
    main([(os.path.join(ROOT, s), os.path.join(ROOT, d)) for s, d in pairs],
         '--dry-run' in sys.argv)
