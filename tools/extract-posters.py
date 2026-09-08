#!/usr/bin/env python3
"""
Poster extractor.

There is no ffmpeg on this machine, so poster frames are grabbed with the
browser instead: a page decodes each clip, seeks into it, draws a frame to a
canvas and POSTs the JPEG back here to be written to disk.

    python tools/extract-posters.py        # serves on 4174 until stopped

Open http://localhost:4174/_poster.html in a browser and it does the rest.
Posters land next to the clips as assets/video/work-NN.jpg.
"""

import base64
import http.server
import pathlib
import socketserver

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIDEO = ROOT / "assets" / "video"
PORT = 4174

PAGE = """<!doctype html>
<meta charset="utf-8"><title>poster extraction</title>
<style>body{font:14px monospace;background:#111;color:#eee;padding:20px}
video{display:none}b{color:#4f8}i{color:#f66;font-style:normal}</style>
<div id="log">starting…</div>
<script>
const clips = %s;
const log = document.getElementById('log');
const line = (t) => { log.innerHTML += '<br>' + t; };

async function grab(name) {
  const v = document.createElement('video');
  v.muted = true; v.playsInline = true; v.preload = 'auto';
  v.src = 'assets/video/' + name + '.mov';
  document.body.appendChild(v);

  await new Promise((res, rej) => {
    v.addEventListener('loadedmetadata', res, { once: true });
    v.addEventListener('error', () => rej(new Error('load')), { once: true });
    setTimeout(() => rej(new Error('timeout')), 20000);
  });

  // A fifth of the way in - past any black lead-in.
  const t = Math.min(Math.max(v.duration * 0.2, 0.5), 8);
  await new Promise((res, rej) => {
    v.addEventListener('seeked', res, { once: true });
    setTimeout(() => rej(new Error('seek timeout')), 20000);
    v.currentTime = t;
  });
  await new Promise(r => setTimeout(r, 350));

  const c = document.createElement('canvas');
  c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext('2d').drawImage(v, 0, 0);
  const data = c.toDataURL('image/jpeg', 0.82);

  const r = await fetch('/save?name=' + name + '.jpg', { method: 'POST', body: data });
  v.remove();
  return v.videoWidth + 'x' + v.videoHeight + ' @' + t.toFixed(1) + 's -> ' + (await r.text());
}

(async () => {
  log.innerHTML = 'extracting ' + clips.length + ' posters…';
  for (const name of clips) {
    try { line(name + ': <b>' + await grab(name) + '</b>'); }
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
        if self.path.startswith("/_poster.html"):
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
        name = self.path.split("name=", 1)[1]
        name = pathlib.Path(name).name  # no traversal
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        b64 = raw.split(",", 1)[1] if "," in raw else raw
        out = VIDEO / name
        out.write_bytes(base64.b64decode(b64))
        msg = ("saved %.0f KB" % (out.stat().st_size / 1024)).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)
        print("wrote", out.name, msg.decode())


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("poster server on http://localhost:%d/_poster.html" % PORT)
        httpd.serve_forever()
