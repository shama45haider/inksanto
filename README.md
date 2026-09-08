# Ink by Santos

A four-page static site for a custom tattoo studio. No build step, no
dependencies, no framework — open `index.html` and it runs.

```
index.html        Home — hero, statement, selected work, process, booking
gallery.html      The Work — filterable grid of 12 plates + lightbox
about.html        About — bio, timeline, autograph, studio particulars
aftercare.html    Aftercare — 5 healing phases, red flags, FAQ, printable
assets/css/site.css   One stylesheet, sectioned and commented
assets/js/site.js     One script, vanilla, every behaviour opt-in
assets/img/           Placeholder flash plates (SVG)
tools/flash-generator.py  Regenerates every plate in assets/img
```

## The design

Print-shop discipline carrying punk texture, layered on the same elements
rather than alternating between them.

- **Palette** — ink `#0a0a0b`, bone `#efeae0`, blood `#c8102e`. Nothing else.
  Sections declare `.pane--ink`, `.pane--bone` or `.pane--blood` and every
  component reads `--fg` / `--bg` / `--rule` from that, so panes invert cleanly.
- **Type** — Big Shoulders Display (condensed industrial), Spectral (editorial
  serif body), Monsieur La Doulaise + Italianno (the cursive), Space Mono
  (print marks and labels).
- **Texture** — animated xerox grain, halftone dot fields, torn-paper pane
  dividers, printer's registration crosshairs, and a red plate that is
  deliberately 2px out of register on the headline (`.mis`).

## Motion

Every animation checks `prefers-reduced-motion` and turns itself off.

| Where | What |
| --- | --- |
| Hero plate | Pointer wipes the finished ink away to expose the red stencil beneath. Sweeps itself once on first view so nobody has to guess it is interactive. |
| Headlines | Rise out of a mask, line by line |
| Scroll | Blocks fade and lift, staggered by `--d` |
| Header | Hides going down, returns going up, with a scroll-progress hairline |
| Tickers | Counter-rotating marquees, paused on hover |
| Gallery | Red vignette rises on hover; corner ticks extend |
| About | Autograph wipes in at pen speed, flourish draws underneath |
| Aftercare | Sticky rail tracks the phase you are reading; progress bar at the foot |
| Navigation | Curtain drops between pages |

Two things worth knowing if you edit the CSS:

1. **Never hide a scroll-revealed element with `clip-path`.** A clipped element
   reports a zero-area intersection rect, so its IntersectionObserver never
   fires and the reveal deadlocks. Use opacity and transform, or clip a
   *wrapper* and observe the wrapper (see `.sign-off`).
2. **The load curtain lifts in CSS, not JS.** If it depended on a script, a
   blocked or failed script would leave a black sheet over the whole site.

## Swap these before going live

All fictional. Search and replace across the four HTML files:

| Placeholder | Where |
| --- | --- |
| `studio@inkbysantos.com` | Footer, booking form `data-booking`, aftercare CTA |
| `+1 (312) 555-0148` / `+13125550148` | Footer (555 numbers are reserved for fiction) |
| `1147 N. Ashland Ave…` | Footer, JSON-LD in `index.html` |
| `IL #BA-0000000` | Footer, about page |
| `Est. 2016`, `Q4 2026 open`, `2–6 weeks` | Hero eyebrow and meta row |
| `$180 / hour`, `$150` deposit | Home booking fineprint, about particulars |
| Instagram / Flash shop `href="#"` | Footer of all four pages |
| Bio, timeline entries, studio copy | `about.html` |

The aftercare content is real, general guidance for a healthy adult, and it
says so — it carries a "not medical advice" note and a see-a-doctor list.
Replace it with your own instructions if yours differ; keep the red-flags
section.

### Images

The 12 plates are generated placeholders — guilloché ornaments with hand-built
figures, printed with registration marks and an off-register red pass. Drop
your photographs into `assets/img/` using the same file names
(`flash-01.svg` → `flash-01.jpg`, updating the `src` and `data-full`
attributes in `gallery.html`) and everything else keeps working.

To regenerate or tweak the placeholders:

```bash
python tools/flash-generator.py
```

## The booking form

There is no backend. On submit it composes the enquiry and hands it to the
visitor's mail client via `mailto:`. To wire a real endpoint, replace the
`bookingForm()` handler in `assets/js/site.js` with a `fetch()` to your form
service — the field names are already sensible.

## Running it locally

```bash
python -m http.server 4173
```

Then open <http://localhost:4173>. Opening the files directly with `file://`
works too, but a server is closer to production.

## Deploying to GitHub Pages

Every asset path is relative, so the site works from a project subpath like
`/inksanto/` with no configuration.

```bash
git push -u origin main
```

Then in the repository: **Settings → Pages → Build and deployment → Source:
Deploy from a branch → `main` / `/ (root)`**.
