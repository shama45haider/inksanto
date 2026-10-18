# Ink by Santos

A four-page static site for a custom tattoo studio. No build step, no
dependencies, no framework — open `index.html` and it runs.

```
index.html        Home — hero clip, studio note, selected work, booking
gallery.html      The Work — 11 clips, filterable, with a video lightbox
inspiration.html  Get Inspired — 11 style references, filterable, image lightbox
about.html        About — bio, background, autograph, studio particulars
aftercare.html    Aftercare — 5 healing phases, red flags, FAQ, printable
assets/css/site.css       One stylesheet, sectioned and commented
assets/js/site.js         One script, vanilla, every behaviour opt-in
assets/img/               Logo, icon and social card
assets/img/lettering/     Lettering style references (full + thumb)
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
- **Texture** — halftone dot fields, torn-paper pane dividers, and a red
  plate deliberately out of register on the headline (`.mis`).

## Motion

Every animation checks `prefers-reduced-motion` and turns itself off.

| Where | What |
| --- | --- |
| Headlines | Rise out of a mask, line by line |
| Scroll | Blocks fade and lift, staggered by `--d` |
| Header | Hides going down, returns going up, with a scroll-progress hairline |
| Ticker | One flat marquee, paused on hover |
| Clips | Only the hero autoplays; the rest load and play on hover |
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
4. **Keep it cheap to paint.** An animated full-screen grain layer,
   `backdrop-filter` on the sticky header, `mix-blend-mode` on the hover
   washes, a rAF-driven custom cursor and eleven autoplaying HEVC clips were
   all removed after the site turned sluggish. Decoding several HEVC videos
   at once was the worst of it. Think twice before adding any of them back.

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
| Studio address | Footer says "full address sent when you book" — add a real one if you want it public |
| Instagram handle | Removed for now — send it and it goes in the footer |

**Name mismatch:** the logo reads *SANTOCHRISSSSS*, the site text says *Ink by
Santos*. Pick one and make them agree.

The aftercare content is real, general guidance for a healthy adult, and says
so — it carries a "not medical advice" note and a see-a-doctor list. Replace
the instructions if yours differ; keep the red-flags section.

## Booking

Booking is a phone call or a text to `(551) 255-5721`. There is no form and
no backend to maintain. The number appears in the booking block, the footer,
the mobile drawer and the aftercare page, plus the JSON-LD business listing.

To add Instagram, drop the handle into the footer "Elsewhere" list on all
four pages.

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

## Get Inspired

`inspiration.html` is a style picker, not a portfolio. Each tile is captioned
"Reference" and the page says in plain words that the lettering gets drawn
fresh — clients quote a number rather than assuming the sheet is finished
work.

**These images came from elsewhere.** At least two are font-vendor specimen
sheets, one carrying `expressivefonts.com` branding, and the rest are other
artists' lettering. That is fine as an in-shop reference book and riskier as
published content on a commercial site. Replacing them with your own
lettering as you build it up removes the question entirely.

The grid and the lightbox are shared with the gallery. A tile with
`data-video` plays a clip; a tile with only `data-full` shows a still. One
lightbox handles both.
