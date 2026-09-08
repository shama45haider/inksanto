/* =========================================================================
   INK BY SANTOS — site.js
   No dependencies. Every behaviour is opt-in via a data attribute, and every
   motion path checks prefers-reduced-motion before it runs.
   ========================================================================= */

(() => {
  "use strict";

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(pointer: fine)").matches;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const clamp = (n, a, b) => Math.min(Math.max(n, a), b);

  /* ------------------------------------------------------------- curtain */

  function curtain() {
    const el = $(".curtain");
    if (!el) return;

    // Lifting is handled in CSS. Same-origin navigation drops it again.
    if (reduced) return;
    document.addEventListener("click", (e) => {
      const a = e.target.closest("a");
      if (!a) return;
      const href = a.getAttribute("href");
      if (
        !href ||
        href.startsWith("#") ||
        href.startsWith("mailto:") ||
        href.startsWith("tel:") ||
        a.target === "_blank" ||
        a.hasAttribute("download") ||
        e.metaKey ||
        e.ctrlKey ||
        e.shiftKey ||
        e.altKey ||
        new URL(a.href, location.href).origin !== location.origin
      ) {
        return;
      }
      e.preventDefault();
      el.classList.add("is-closing");
      setTimeout(() => (location.href = a.href), 500);
    });

    // Coming back via bfcache must not leave the curtain down.
    window.addEventListener("pageshow", (e) => {
      if (e.persisted) el.classList.remove("is-closing");
    });
  }

  /* -------------------------------------------------------------- reveal */

  function reveal() {
    const items = $$("[data-reveal]");
    if (!items.length) return;
    if (reduced || !("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.08 }
    );
    items.forEach((el) => io.observe(el));
  }

  /* ------------------------------------------------- headline line split */

  /* Splits a heading into visual lines and masks each one so it can rise
     independently. Runs after fonts settle, otherwise the measured line
     breaks belong to the fallback face. */
  function splitLines() {
    const targets = $$("[data-split]");
    if (!targets.length || reduced) return;

    targets.forEach((el) => {
      if (el.dataset.splitDone) return;
      const words = el.textContent.trim().split(/\s+/);
      el.textContent = "";
      const spans = words.map((w, i) => {
        const s = document.createElement("span");
        s.textContent = w + (i < words.length - 1 ? " " : "");
        el.appendChild(s);
        return s;
      });

      const lines = [];
      let top = null;
      spans.forEach((s) => {
        const t = Math.round(s.offsetTop);
        if (top === null || Math.abs(t - top) > 4) {
          lines.push([]);
          top = t;
        }
        lines[lines.length - 1].push(s.textContent);
      });

      el.textContent = "";
      lines.forEach((words, i) => {
        const line = document.createElement("span");
        line.className = "line";
        const inner = document.createElement("i");
        inner.textContent = words.join("");
        inner.style.setProperty("--l", i);
        line.appendChild(inner);
        el.appendChild(line);
      });
      el.dataset.splitDone = "1";
    });

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -15% 0px", threshold: 0.15 }
    );
    targets.forEach((el) => io.observe(el));
  }

  /* -------------------------------------------------- header + progress */

  function header() {
    const bar = $(".masthead");
    if (!bar) return;
    const progress = $(".progress");
    let last = window.scrollY;
    let ticking = false;

    const update = () => {
      const y = window.scrollY;
      bar.classList.toggle("is-top", y < 24);
      if (y > 140 && y > last + 4) bar.classList.add("is-hidden");
      else if (y < last - 4) bar.classList.remove("is-hidden");
      last = y;

      if (progress) {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.setProperty("--p", max > 0 ? clamp(y / max, 0, 1) : 0);
      }
      ticking = false;
    };

    update();
    window.addEventListener(
      "scroll",
      () => {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(update);
      },
      { passive: true }
    );
  }

  /* -------------------------------------------------------------- drawer */

  function drawer() {
    const btn = $(".burger");
    const panel = $(".drawer");
    if (!btn || !panel) return;

    const setOpen = (open) => {
      btn.setAttribute("aria-expanded", String(open));
      panel.classList.toggle("is-open", open);
      document.body.style.overflow = open ? "hidden" : "";
      if (open) $(".drawer__link", panel)?.focus({ preventScroll: true });
    };

    btn.addEventListener("click", () =>
      setOpen(btn.getAttribute("aria-expanded") !== "true")
    );
    panel.addEventListener("click", (e) => {
      if (e.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && panel.classList.contains("is-open")) {
        setOpen(false);
        btn.focus();
      }
    });
  }

  /* -------------------------------------------------------------- cursor */

  function cursor() {
    if (!fine || reduced) return;
    const wrap = document.createElement("div");
    wrap.className = "cursor";
    wrap.innerHTML =
      '<div class="cursor__ring"><span></span></div><div class="cursor__dot"></div>';
    document.body.appendChild(wrap);

    const ring = $(".cursor__ring", wrap);
    const dot = $(".cursor__dot", wrap);
    const label = $("span", ring);
    let mx = innerWidth / 2;
    let my = innerHeight / 2;
    let rx = mx;
    let ry = my;

    addEventListener(
      "pointermove",
      (e) => {
        mx = e.clientX;
        my = e.clientY;
        dot.style.transform = `translate(${mx}px, ${my}px)`;

        const hit = e.target.closest("[data-cursor], a, button");
        const text = hit?.dataset?.cursor;
        wrap.classList.toggle("is-active", Boolean(text));
        label.textContent = text || "";
      },
      { passive: true }
    );

    const loop = () => {
      rx += (mx - rx) * 0.16;
      ry += (my - ry) * 0.16;
      ring.style.transform = `translate(${rx}px, ${ry}px)`;
      requestAnimationFrame(loop);
    };
    loop();
  }

  /* ------------------------------------------------------------ magnetic */

  function magnetic() {
    if (!fine || reduced) return;
    $$("[data-magnet]").forEach((el) => {
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        const dx = (e.clientX - (r.left + r.width / 2)) / r.width;
        const dy = (e.clientY - (r.top + r.height / 2)) / r.height;
        el.style.transform = `translate(${dx * 9}px, ${dy * 6}px)`;
      });
      el.addEventListener("pointerleave", () => {
        el.style.transform = "";
      });
    });
  }

  /* -------------------------------------------------------- hero parallax */

  function parallax() {
    const layers = $$("[data-parallax]");
    if (!layers.length || reduced) return;
    let ticking = false;
    const update = () => {
      const y = window.scrollY;
      layers.forEach((el) => {
        const rate = parseFloat(el.dataset.parallax) || 0.06;
        el.style.transform = `translate3d(0, ${(-y * rate).toFixed(2)}px, 0)`;
      });
      ticking = false;
    };
    addEventListener(
      "scroll",
      () => {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(update);
      },
      { passive: true }
    );
  }

  /* ---------------------------------------------------------------- video */

  /* Clips carry their source in data-src and only fetch it once they are on
     screen — eleven portrait videos is far too much to load up front. Muted
     is required for autoplay, and every clip keeps a poster so the artwork
     still shows if the browser cannot decode the codec. */
  function video() {
    const clips = $$("video[data-src]");
    if (!clips.length) return;

    const start = (v) => {
      if (!v.src) v.src = v.dataset.src;
      const done = () => v.classList.add("is-playing");
      if (v.readyState >= 2) done();
      else v.addEventListener("loadeddata", done, { once: true });
      const play = v.play();
      if (play && play.catch) play.catch(() => {});
    };

    if (reduced || !("IntersectionObserver" in window)) {
      // Leave the posters in place; no autoplay when motion is unwelcome.
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const v = entry.target;
          if (entry.isIntersecting) start(v);
          else if (!v.paused) v.pause();
        });
      },
      { rootMargin: "150px 0px", threshold: 0.2 }
    );
    clips.forEach((v) => io.observe(v));

    // Sound toggles, where offered.
    $$("[data-sound]").forEach((btn) => {
      const target = $(btn.dataset.sound);
      if (!target) return;
      btn.addEventListener("click", () => {
        target.muted = !target.muted;
        btn.textContent = target.muted ? "\u266b" : "\u25cf";
        btn.setAttribute(
          "aria-label",
          target.muted ? "Unmute clip" : "Mute clip"
        );
        if (!target.muted && target.paused) target.play().catch(() => {});
      });
    });
  }

  /* ------------------------------------------------------------- gallery */

  function gallery() {
    const grid = $("[data-gallery]");
    if (!grid) return;
    const tiles = $$(".tile", grid);
    const chips = $$("[data-filter]");

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const want = chip.dataset.filter;
        chips.forEach((c) =>
          c.setAttribute("aria-pressed", String(c === chip))
        );
        tiles.forEach((tile) => {
          const tags = (tile.dataset.tags || "").split(/\s+/);
          tile.classList.toggle(
            "is-muted",
            want !== "all" && !tags.includes(want)
          );
        });
      });
    });

    lightbox(tiles);
  }

  function lightbox(tiles) {
    const box = $(".lightbox");
    if (!box || !tiles.length) return;
    const vid = $(".lightbox__stage video", box);
    const title = $(".lightbox__title", box);
    const tags = $(".lightbox__tags", box);
    const count = $("[data-lb-count]", box);
    let index = 0;
    let opener = null;

    const show = (i) => {
      index = (i + tiles.length) % tiles.length;
      const tile = tiles[index];

      if (vid) {
        vid.pause();
        vid.removeAttribute("src");
        vid.poster = tile.dataset.poster || "";
        vid.src = tile.dataset.video || "";
        vid.load();
        const go = vid.play();
        if (go && go.catch) go.catch(() => {});
      }

      title.textContent = tile.dataset.title || "";
      tags.textContent = tile.dataset.meta || "";
      if (count)
        count.textContent = `${String(index + 1).padStart(2, "0")} / ${String(
          tiles.length
        ).padStart(2, "0")}`;
    };

    const open = (i, from) => {
      opener = from || null;
      show(i);
      box.classList.add("is-open");
      box.removeAttribute("aria-hidden");
      document.body.style.overflow = "hidden";
      $(".lightbox__close", box)?.focus({ preventScroll: true });
    };

    const close = () => {
      box.classList.remove("is-open");
      box.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
      if (vid) {
        vid.pause();
        vid.removeAttribute("src");
        vid.load();
      }
      opener?.focus({ preventScroll: true });
    };

    tiles.forEach((tile, i) =>
      tile.addEventListener("click", () => open(i, tile))
    );
    $(".lightbox__close", box)?.addEventListener("click", close);
    $(".lightbox__nav--prev", box)?.addEventListener("click", () => show(index - 1));
    $(".lightbox__nav--next", box)?.addEventListener("click", () => show(index + 1));
    box.addEventListener("click", (e) => {
      if (e.target === box || e.target.classList.contains("lightbox__stage"))
        close();
    });

    document.addEventListener("keydown", (e) => {
      if (!box.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") show(index - 1);
      if (e.key === "ArrowRight") show(index + 1);
      if (e.key === "Tab") {
        // Keep focus inside the dialog while it is open.
        const focusables = $$(
          "button, [href], input, [tabindex]:not([tabindex='-1'])",
          box
        ).filter((el) => el.offsetParent !== null);
        if (!focusables.length) return;
        const first = focusables[0];
        const lastEl = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          lastEl.focus();
        } else if (!e.shiftKey && document.activeElement === lastEl) {
          e.preventDefault();
          first.focus();
        }
      }
    });
  }

  /* ----------------------------------------------------------- aftercare */

  function aftercare() {
    const phases = $$(".phase");
    const links = $$(".care__rail a");
    const bar = $(".care__progress");
    if (!phases.length) return;

    if ("IntersectionObserver" in window && links.length) {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            const id = entry.target.id;
            links.forEach((a) =>
              a.classList.toggle("is-active", a.getAttribute("href") === `#${id}`)
            );
          });
        },
        { rootMargin: "-30% 0px -58% 0px" }
      );
      phases.forEach((p) => io.observe(p));
    }

    if (bar) {
      const zone = $(".care");
      let ticking = false;
      const update = () => {
        const r = zone.getBoundingClientRect();
        const total = r.height - window.innerHeight;
        const done = total > 0 ? clamp(-r.top / total, 0, 1) : 0;
        bar.style.setProperty("--cp", done);
        ticking = false;
      };
      update();
      addEventListener(
        "scroll",
        () => {
          if (ticking) return;
          ticking = true;
          requestAnimationFrame(update);
        },
        { passive: true }
      );
    }
  }

  /* ----------------------------------------------------------- signature */

  /* The autograph is hidden with clip-path, which zeroes its intersection
     rect — so the observer watches the unclipped wrapper instead. */
  function signature() {
    const block = $(".sign-off");
    if (!block) return;

    $$(".signature path", block).forEach((p, i) => {
      p.style.setProperty("--len", Math.ceil(p.getTotalLength()));
      p.style.setProperty("--s", i);
    });

    if (reduced) {
      block.classList.add("is-in");
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          block.classList.add("is-in");
          io.disconnect();
        });
      },
      { threshold: 0.35 }
    );
    io.observe(block);
  }

  /* ---------------------------------------------------------------- form */

  /* No backend here. The form composes a well-formed enquiry and hands it to
     the visitor's mail client. Swap the handler for a real endpoint later. */
  function bookingForm() {
    const form = $("[data-booking]");
    if (!form) return;
    const status = $("[data-booking-status]", form);

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const to = form.dataset.booking;
      const lines = [];
      for (const [key, value] of data.entries()) {
        if (!value) continue;
        lines.push(`${key.replace(/_/g, " ").toUpperCase()}: ${value}`);
      }
      const subject = `Booking enquiry — ${data.get("name") || "no name"}`;
      const href = `mailto:${to}?subject=${encodeURIComponent(
        subject
      )}&body=${encodeURIComponent(lines.join("\n\n"))}`;

      if (status) {
        status.hidden = false;
        status.textContent =
          "Opening your mail client — if nothing happens, send the same details to " +
          to;
      }
      window.location.href = href;
    });
  }

  /* --------------------------------------------------------------- print */

  function printSheet() {
    $$("[data-print]").forEach((btn) =>
      btn.addEventListener("click", () => window.print())
    );
  }

  /* ----------------------------------------------------------------- go */

  const boot = () => {
    curtain();
    header();
    drawer();
    reveal();
    cursor();
    magnetic();
    parallax();
    gallery();
    video();
    aftercare();
    signature();
    bookingForm();
    printSheet();

    if (document.fonts?.ready) {
      document.fonts.ready.then(splitLines);
    } else {
      splitLines();
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
