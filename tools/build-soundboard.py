#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build doveclem-soundboard.html — the single-file Claude Artifact build.

Same app as app/index.html, but every clip is inlined as base64 (an artifact has
no origin to fetch from) and the service worker is dropped (nothing to install).
The app itself still has no build step: this only exists because the artifact
sandbox blocks external hosts.

    python3 app/tools/build-soundboard.py
"""
import base64, io, json, os, re, sys

# the project root, two levels above app/tools
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC  = os.path.join(ROOT, 'app', 'index.html')
# build/ is outside the repo on purpose: this file is 1.2 MB and regenerable,
# which makes it the one thing here that does not need saving
OUT  = os.path.join(ROOT, 'build', 'doveclem-soundboard.html')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

src = io.open(SRC, encoding='utf-8').read()

# The clips. PACKS is readable JS rather than JSON now, so this rewrites each
# url in place instead of parsing the array and printing it back — which also
# means adding a field to a clip cannot break the build.
def inline(path):
    """base64 of a file under app/, and a running total of what we embedded."""
    raw = io.open(os.path.join(ROOT, 'app', path), 'rb').read()
    sizes.append(len(raw))
    return base64.b64encode(raw).decode('ascii')

sizes = []
n_clips = [0]
def clip_url(m):
    n_clips[0] += 1
    return "b64:'%s'" % inline(m.group(1))

src, n = re.subn(r"url:'([^']+)'", clip_url, src)
if not n:
    sys.exit('could not find any clip urls in app/index.html')
print('%-8s %d clips' % ('packs', n_clips[0]))

# the drum kits go in the same way — an artifact has no origin to fetch from
km = re.search(r'^(const KITS = \[.*?\n\];)$', src, re.M | re.S)
if not km:
    sys.exit('could not find the KITS array in app/index.html')
kits_src = km.group(1)
tm_takes = re.search(r'^const TAKES = (\d+);$', src, re.M)
takes = int(tm_takes.group(1)) if tm_takes else 1
for kid in re.findall(r"id:'(\w+)'", kits_src):
    d = os.path.join(ROOT, 'app', 'audio', 'kit', kid)
    if not os.path.isdir(d):
        continue
    b64 = {}
    # one entry per take, keyed the way loadKit asks for it
    for name in ('kick', 'snare', 'clap', 'hat', 'ohat'):
        for k in range(1, takes + 1):
            f = '%s-%d' % (name, k)
            if os.path.exists(os.path.join(d, f + '.m4a')):
                b64[f] = inline(os.path.join('audio', 'kit', kid, f + '.m4a'))
    if b64:
        kits_src = kits_src.replace("id:'%s'," % kid,
                                    "id:'%s', b64:%s," % (kid, json.dumps(b64)), 1)
        print('%-8s %d drum sounds' % (kid, len(b64)))
src = src[:km.start(1)] + kits_src + src[km.end(1):]

# and the recorded instruments
tm = re.search(r'^(const TIMBRES = \[.*?\n\];)$', src, re.M | re.S)
if not tm:
    sys.exit('could not find the TIMBRES array in app/index.html')
tb_src = tm.group(1)
for tid, notes in re.findall(r"id:'(\w+)',[^}]*?notes:\[([^\]]*)\]", tb_src):
    b64 = {}
    for nn in [x.strip() for x in notes.split(',') if x.strip()]:
        f = os.path.join(ROOT, 'app', 'audio', 'instr', tid, nn + '.m4a')
        if os.path.exists(f):
            b64[nn] = inline(os.path.join('audio', 'instr', tid, nn + '.m4a'))
    if b64:
        tb_src = tb_src.replace("id:'%s'," % tid,
                                "id:'%s', b64:%s," % (tid, json.dumps(b64)), 1)
        print('%-8s %d instrument notes' % (tid, len(b64)))
src = src[:tm.start(1)] + tb_src + src[tm.end(1):]

# the electric bass, which is not a timbre and so is not in that array
bm = re.search(r'^const BASS_NOTES = \[([^\]]*)\];$', src, re.M)
if not bm:
    sys.exit('could not find BASS_NOTES in app/index.html')
bass = {}
for nn in [x.strip() for x in bm.group(1).split(',') if x.strip()]:
    f = os.path.join(ROOT, 'app', 'audio', 'instr', 'bass', nn + '.m4a')
    if os.path.exists(f):
        bass[nn] = inline(os.path.join('audio', 'instr', 'bass', nn + '.m4a'))
if bass:
    before = src
    src = src.replace('const BASS_B64 = null;',
                      'const BASS_B64 = %s;' % json.dumps(bass), 1)
    if src == before:
        sys.exit('could not find the BASS_B64 placeholder in app/index.html')
    print('%-8s %d bass notes' % ('bass', len(bass)))

total = sum(sizes)

# artifact shell: no doctype/head/body of our own, no service worker
body = src[src.index('<body>') + len('<body>'):src.rindex('</body>')].strip('\n')
body = re.sub(r"\n<script>\s*if \('serviceWorker' in navigator\).*?</script>", '', body, flags=re.S)
if 'serviceWorker' in body:
    sys.exit('service worker registration still present')

out = u'<title>Dov’è Clem</title>\n' + body + '\n'
io.open(OUT, 'w', encoding='utf-8').write(out)
print('audio %.0f KB -> %s, %.0f KB' % (total / 1024., os.path.basename(OUT), len(out) / 1024.))
