# Ink by Santos

A four-page static site for a custom tattoo studio. No build step, no
dependencies, no framework — open `index.html` and it runs.

```
index.html        Home — hero clip, statement, selected work, process, booking
gallery.html      The Work — 11 clips, filterable, with a video lightbox
about.html        About — bio, background, autograph, studio particulars
aftercare.html    Aftercare — 5 healing phases, red flags, FAQ, printable
assets/css/site.css       One stylesheet, sectioned and commented
assets/js/site.js         One script, vanilla, every behaviour opt-in
assets/img/               Logo, icon and social card
assets/video/             The clips and their poster frames
tools/extract-posters.py  Regenerates poster frames from the clips
```

## The design

Print-shop discipline carrying punk texture, layered on the same elements
rather than alternating between them.

- **Palette** — ink `#0a0a0b`, bone `#efeae0`, blood `#c8102e`. Sections
  declare `.pane--ink`, `.pane--bone` or `.pane--blood` and every component
  reads `--fg` / `--bg` / `--rule` from that, so panes invert cleanly.
- **Type** — Big Shoulders Display (condensed industrial), Spectral (editorial
  serif body), Monsieur La Doulaise + Italianno (the cursive), Space Mono
  (print marks and labels).
- **Texture** — animated xerox grain, halftone dot fields, torn-paper pane
  dividers, and a red plate deliberately out of register on the headline
  (`.mis`).

## Motion

Every animation checks `prefers-reduced-motion` and turns itself off.

| Where | What |
| --- | --- |
| Headlines | Rise out of a mask, line by line |
| Scroll | Blocks fade and lift, staggered by `--d` |
| Header | Hides going down, returns going up, with a scroll-progress hairline |
| Tickers | Counter-rotating marquees, paused on hover |
| Clips | Load and play only while on screen, pause when they leave |
| Gallery | Red vignette rises on hover; corner ticks extend |
| About | Autograph wipes in at pen speed, flourish draws underneath |
| Aftercare | Sticky rail tracks the phase you are reading; progress bar at the foot |
| Navigation | Curtain drops between pages |

Three things worth knowing before editing:

1. **Never hide a scroll-revealed element with `clip-path`.** A clipped element
   reports a zero-area intersection rect, so its IntersectionObserver never
   fires and the reveal deadlocks. Use opacity and transform, or clip a
   *wrapper* and observe the wrapper (see `.sign-off`).
2. **The load curtain lifts in CSS, not JS.** If it depended on a script, a
   blocked or failed script would leave a black sheet over the whole site.
3. **Clips must stay `muted`** or browsers will refuse to autoplay them.

## The video, and one thing you should fix

The clips are the originals straight off the phone: **HEVC (h265) inside a
QuickTime `.mov` container.** That plays on Safari, iOS, and Chrome on machines
that have an HEVC decoder — but **Firefox cannot play HEVC at all**, and plenty
of Windows Chrome installs can't either. Those visitors get the poster frame
and no motion.

Every clip therefore ships with a real poster frame extracted from the video
itself, so the artwork is always visible even when playback fails.

To fix it properly, convert to H.264 MP4 once you have
[ffmpeg](https://ffmpeg.org/download.html):

```bash
for f in assets/video/*.mov; do ffmpeg -i "$f" -c:v libx264 -crf 23 -preset slow -c:a aac -b:a 128k -movflags +faststart "${f%.mov}.mp4"; done
```

Then point the markup at the new files:

```bash
sed -i 's/\.mov"/.mp4"/g' index.html gallery.html about.html
```

That also shrinks the download — the clips are 27 MB as they stand.

### Poster frames

If you replace a clip, regenerate its poster:

```bash
python tools/extract-posters.py
```

Then open <http://localhost:4174/_poster.html>. It decodes each clip in the
browser, grabs a frame a fifth of the way in, and writes
`assets/video/work-NN.jpg`.

## Still to swap

Fictional placeholders that are live on the site right now:

| Placeholder | Where |
| --- | --- |
| `studio@inkbysantos.com` | Footer, booking form `data-booking`, aftercare CTA |
| `+1 (312) 555-0148` | Footer (555 numbers are reserved for fiction) |
| `1147 N. Ashland Ave…` | Footer, JSON-LD in `index.html` |
| `IL #BA-0000000` | Footer, about page |
| `Q4 2026 open`, `2–6 weeks` | Hero meta row |
| `$180 / hour`, `$150` deposit | Booking fineprint, about particulars |
| Instagram / Flash shop `href="#"` | Footer of all four pages |
| Background dates and bio | `about.html` |

**Name mismatch:** the logo reads *SANTOCHRISSSSS*, the site text says *Ink by
Santos*. Pick one and make them agree.

The aftercare content is real, general guidance for a healthy adult, and says
so — it carries a "not medical advice" note and a see-a-doctor list. Replace
the instructions if yours differ; keep the red-flags section.

## The booking form

There is no backend. On submit it composes the enquiry and hands it to the
visitor's mail client via `mailto:`. To wire a real endpoint, replace the
`bookingForm()` handler in `assets/js/site.js` with a `fetch()` to your form
service — the field names are already sensible.

## Running it locally

```bash
python -m http.server 4173
```

Then open <http://localhost:4173>.

## Deploying

Pushing to `main` triggers `.github/workflows/static.yml`, which publishes the
whole repository to GitHub Pages at
<https://shama45haider.github.io/inksanto/>. Every asset path is relative, so
the `/inksanto/` subpath needs no configuration.

```bash
git push
```
