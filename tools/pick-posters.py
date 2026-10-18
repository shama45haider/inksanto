#!/usr/bin/env python3
"""
Poster frame picker.

The first pass grabbed a frame a fixed fifth of the way into each clip, which
often landed on a hand, a paper towel or a black lead-in. This scores several
candidate frames per clip and keeps the one where the tattoo actually sits in
the middle of the shot.

Score per frame:
  * reject frames that are nearly black or blown out
  * measure edge energy inside the centre box - tattoo linework is the
    highest-contrast thing in these clips
  * prefer the centre over the edges, so a piece filling the frame beats a
    busy background

    python tools/pick-posters.py        # serves on 4174

Then open http://localhost:4174/_pick.html and it writes the winners over
assets/video/work-NN.jpg.
"""

import base64
import http.server
import pathlib
import socketserver

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIDEO = ROOT / "assets" / "video"
PORT = 4174

PAGE = """<!doctype html>
<meta charset="utf-8"><title>poster picker</title>
<style>body{font:13px monospace;background:#111;color:#eee;padding:16px}
b{color:#5f8}i{color:#f66;font-style:normal}</style>
<div id="log">scoring…</div>
<script>
const clips = %s;
const log = document.getElementById('log');
const line = t => log.innerHTML += '<br>' + t;

// Edge energy inside the centre box, ignoring the outer margin.
function score(ctx, w, h) {
  const mx = Math.round(w * 0.2), my = Math.round(h * 0.2);
  const bw = w - mx * 2, bh = h - my * 2;
  const d = ctx.getImageData(mx, my, bw, bh).data;
  let sum = 0, edge = 0, n = 0;
  const lum = i => 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
  for (let y = 0; y < bh; y += 2) {
    for (let x = 0; x < bw - 2; x += 2) {
      const i = (y * bw + x) * 4;
      const l = lum(i);
      sum += l; n++;
      edge += Math.abs(l - lum(i + 8));
      if (y + 2 < bh) edge += Math.abs(l - lum(i + bw * 8));
    }
  }
  const mean = sum / n;
  // Too dark or too blown out to be a usable poster.
  if (mean < 42 || mean > 212) return { ok: false, mean, energy: 0 };
  return { ok: true, mean, energy: edge / n };
}

async function pick(name) {
  const v = document.createElement('video');
  v.muted = true; v.playsInline = true; v.preload = 'auto';
  v.src = 'assets/video/' + name + '.mov';
  document.body.appendChild(v);
  await new Promise((res, rej) => {
    v.addEventListener('loadedmetadata', res, { once: true });
    v.addEventListener('error', () => rej(new Error('load')), { once: true });
    setTimeout(() => rej(new Error('timeout')), 20000);
  });

  const c = document.createElement('canvas');
  c.width = v.videoWidth; c.height = v.videoHeight;
  const ctx = c.getContext('2d', { willReadFrequently: true });

  let best = null;
  const STEPS = 9;
  for (let i = 0; i < STEPS; i++) {
    const t = v.duration * (0.12 + (0.76 * i) / (STEPS - 1));
    await new Promise((res, rej) => {
      v.addEventListener('seeked', res, { once: true });
      setTimeout(() => rej(new Error('seek')), 15000);
      v.currentTime = t;
    });
    await new Promise(r => setTimeout(r, 120));
    ctx.drawImage(v, 0, 0);
    const s = score(ctx, c.width, c.height);
    if (s.ok && (!best || s.energy > best.energy)) {
      best = { t, energy: s.energy, mean: s.mean, data: c.toDataURL('image/jpeg', 0.86) };
    }
  }
  v.remove();
  if (!best) return 'no usable frame';
  const r = await fetch('/save?name=' + name + '.jpg', { method: 'POST', body: best.data });
  return 'picked ' + best.t.toFixed(1) + 's  energy ' + best.energy.toFixed(1) +
         '  mean ' + best.mean.toFixed(0) + '  -> ' + (await r.text());
}

(async () => {
  log.innerHTML = 'scoring ' + clips.length + ' clips…';
  for (const name of clips) {
    try { line(name + ': <b>' + await pick(name) + '</b>'); }
    catch (e) { line(name + ': <i>FAILED ' + e.message + '</i>'); }
  }
  line('<b>DONE</b>');
  window.__done = true;
})();
</script>
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/_pick.html"):
            names = sorted(p.stem for p in VIDEO.glob("*.mov"))
            body = (PAGE % repr(names).replace("'", '"')).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/save"):
            self.send_error(404)
            return
        name = pathlib.Path(self.path.split("name=", 1)[1]).name
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
        b64 = raw.split(",", 1)[1] if "," in raw else raw
        out = VIDEO / name
        out.write_bytes(base64.b64decode(b64))
        msg = ("saved %.0f KB" % (out.stat().st_size / 1024)).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)
        print("wrote", out.name)


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("picker on http://localhost:%d/_pick.html" % PORT)
        httpd.serve_forever()
