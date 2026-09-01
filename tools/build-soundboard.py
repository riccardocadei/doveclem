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

m = re.search(r'^const PACKS = (\[.*?\n\]);$', src, re.M | re.S)
if not m:
    sys.exit('could not find the PACKS array in app/index.html')
packs = json.loads(m.group(1))

total = 0
for pack in packs:
    for clip in pack['clips']:
        path = os.path.join(ROOT, 'app', clip.pop('url'))
        raw = io.open(path, 'rb').read()
        total += len(raw)
        clip['b64'] = base64.b64encode(raw).decode('ascii')
    print('%-8s %d clips' % (pack['id'], len(pack['clips'])))

inlined = 'const PACKS = ' + json.dumps(packs, ensure_ascii=True) + ';'
src = src[:m.start()] + inlined + src[m.end():]

# the drum kits go in the same way — an artifact has no origin to fetch from
km = re.search(r'^(const KITS = \[.*?\n\];)$', src, re.M | re.S)
if not km:
    sys.exit('could not find the KITS array in app/index.html')
kits_src = km.group(1)
for kid in re.findall(r"id:'(\w+)'", kits_src):
    d = os.path.join(ROOT, 'app', 'audio', 'kit', kid)
    if not os.path.isdir(d):
        continue
    b64 = {}
    for name in ('kick', 'snare', 'clap', 'hat', 'ohat'):
        f = os.path.join(d, name + '.m4a')
        if os.path.exists(f):
            raw = io.open(f, 'rb').read()
            total += len(raw)
            b64[name] = base64.b64encode(raw).decode('ascii')
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
    for n in [x.strip() for x in notes.split(',') if x.strip()]:
        f = os.path.join(ROOT, 'app', 'audio', 'instr', tid, n + '.m4a')
        if os.path.exists(f):
            raw = io.open(f, 'rb').read()
            total += len(raw)
            b64[n] = base64.b64encode(raw).decode('ascii')
    if b64:
        tb_src = tb_src.replace("id:'%s'," % tid,
                                "id:'%s', b64:%s," % (tid, json.dumps(b64)), 1)
        print('%-8s %d instrument notes' % (tid, len(b64)))
src = src[:tm.start(1)] + tb_src + src[tm.end(1):]

# artifact shell: no doctype/head/body of our own, no service worker
body = src[src.index('<body>') + len('<body>'):src.rindex('</body>')].strip('\n')
body = re.sub(r"\n<script>\s*if \('serviceWorker' in navigator\).*?</script>", '', body, flags=re.S)
if 'serviceWorker' in body:
    sys.exit('service worker registration still present')

out = u'<title>Dov’è Clem</title>\n' + body + '\n'
io.open(OUT, 'w', encoding='utf-8').write(out)
print('audio %.0f KB -> %s, %.0f KB' % (total / 1024., os.path.basename(OUT), len(out) / 1024.))
