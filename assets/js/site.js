/*
 * site.js — plain ES, no bundler, loaded with `defer`.
 *
 * Independent modules, each of which returns immediately if the elements
 * it owns are not on the page. Nothing here is required for the page to be
 * readable, navigable or themed: the no-flash theme script runs inline in the
 * head, the mobile nav is a native <dialog>, and reveals and the progress bar
 * are CSS scroll-driven animations. This file only adds affordances.
 *
 * Deliberately absent: a hand-rolled focus trap. <dialog>.showModal() gives us
 * Esc-to-close, focus containment, focus restoration, `inert` on the rest of
 * the document and a scroll lock, all from the UA, all correct.
 */
(function () {
  "use strict";

  var root = document.documentElement;

  /* ── 1 · Theme ──────────────────────────────────────────────────────────
   * The inline head script has already applied the stored theme before first
   * paint. This only handles the click.
   */
  (function theme() {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;

    var meta = document.querySelector('meta[name="theme-color"]');

    function label() {
      // Describe the ACTION, not the current state. "Dark mode" on a button is
      // ambiguous: it could mean "you are in dark mode" or "switch to it".
      var next = root.dataset.theme === "dark" ? "light" : "dark";
      btn.setAttribute("aria-label", "Switch to " + next + " theme");
      btn.setAttribute("title", "Switch to " + next + " theme");
    }

    function paintMeta() {
      if (!meta) return;
      // Read the resolved token so the browser chrome matches the page exactly.
      var bg = getComputedStyle(root).getPropertyValue("--surface-0").trim();
      if (bg) meta.setAttribute("content", bg);
    }

    btn.addEventListener("click", function () {
      var next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {
        localStorage.setItem("theme", next);
      } catch (e) {
        /* private mode / storage disabled — the toggle still works for this page */
      }
      label();
      paintMeta();
    });

    label();
    paintMeta();
  })();

  /* ── 2 · Mobile nav ─────────────────────────────────────────────────────
   * The <dialog> does the hard parts. We add backdrop-click-to-close and keep
   * aria-expanded on the trigger in sync, including when the UA closes the
   * dialog for us (Esc, or the form-method=dialog close button).
   */
  (function nav() {
    var dialog = document.querySelector("[data-nav-dialog], .nav-dialog");
    // The close button inside the drawer carries .nav-toggle too, so prefer the
    // explicit opener hook and only fall back to the first .nav-toggle.
    var toggle = document.querySelector("[data-nav-open], .nav-toggle");
    if (!dialog || !toggle || typeof dialog.showModal !== "function") return;
    var pageY = 0;

    function setExpanded(v) {
      toggle.setAttribute("aria-expanded", v ? "true" : "false");
    }

    toggle.addEventListener("click", function () {
      pageY = window.scrollY;
      dialog.showModal();
      setExpanded(true);
      // Safari and Chromium can scroll the document while moving focus into a
      // modal dialog. The drawer is fixed, so that movement is never useful.
      requestAnimationFrame(function () {
        window.scrollTo(0, pageY);
      });
    });

    // Clicking the backdrop reports the click on the <dialog> itself, because
    // the backdrop is the dialog's own pseudo-element. Anything inside the
    // padding box is real content.
    dialog.addEventListener("click", function (e) {
      if (e.target !== dialog) return;
      var box = dialog.getBoundingClientRect();
      var inside =
        e.clientX >= box.left &&
        e.clientX <= box.right &&
        e.clientY >= box.top &&
        e.clientY <= box.bottom;
      if (!inside) dialog.close();
    });

    dialog.addEventListener("close", function () {
      setExpanded(false);
      requestAnimationFrame(function () {
        window.scrollTo(0, pageY);
      });
    });

    // Close on navigation to an in-page anchor within the drawer.
    dialog.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[href]");
      if (a) dialog.close();
    });

    setExpanded(false);
  })();

  /* ── 3 · Code blocks: language label, copy button, scrollable-pre a11y ──
   * One pass over the DOM, one live region for the whole page.
   */
  (function code() {
    var blocks = document.querySelectorAll(".highlighter-rouge");
    if (!blocks.length) return;

    var live = document.createElement("div");
    live.className = "sr-live";
    live.setAttribute("role", "status");
    live.setAttribute("aria-live", "polite");
    document.body.appendChild(live);

    function copy(text) {
      if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
      }
      // Fallback for file:// and any non-secure context.
      return new Promise(function (resolve, reject) {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.cssText = "position:fixed;top:-9999px;opacity:0";
        document.body.appendChild(ta);
        ta.select();
        var ok = false;
        try {
          ok = document.execCommand("copy");
        } catch (e) {
          ok = false;
        }
        document.body.removeChild(ta);
        ok ? resolve() : reject();
      });
    }

    Array.prototype.forEach.call(blocks, function (block) {
      var pre = block.querySelector("pre");
      if (!pre) return;

      var lang = (block.className.match(/language-([\w+#-]+)/) || [])[1] || "";
      if (lang === "plaintext" || lang === "text") lang = "";

      var tools = document.createElement("div");
      tools.className = "code-tools";

      if (lang) {
        var tag = document.createElement("span");
        tag.className = "code-lang";
        tag.setAttribute("aria-hidden", "true");
        tag.textContent = lang;
        tools.appendChild(tag);
      }

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy-btn";
      btn.textContent = "Copy";
      var what = block.getAttribute("data-file") || lang || "code";
      btn.setAttribute("aria-label", "Copy " + what + " to clipboard");

      // In a console transcript Rouge marks the prompt `.gp` and the program's
      // output `.go`. Copying those back into a shell is never what anyone
      // wants, so they are dropped from the copied text — the on-screen
      // transcript stays complete.
      function payload() {
        if (!pre.querySelector(".gp")) return pre.textContent;
        var clone = pre.cloneNode(true);
        Array.prototype.forEach.call(clone.querySelectorAll(".gp, .go"), function (n) {
          n.remove();
        });
        return clone.textContent.replace(/\n{2,}/g, "\n").trim();
      }

      var timer;
      btn.addEventListener("click", function () {
        copy(payload()).then(
          function () {
            btn.textContent = "Copied";
            btn.dataset.state = "copied";
            live.textContent = what + " copied to clipboard";
            clearTimeout(timer);
            timer = setTimeout(function () {
              btn.textContent = "Copy";
              delete btn.dataset.state;
              live.textContent = "";
            }, 2000);
          },
          function () {
            live.textContent = "Copy failed — select the code and copy manually";
          }
        );
      });

      tools.appendChild(btn);
      block.appendChild(tools);

      /* ── 4 · Scrollable <pre> ─────────────────────────────────────────
       * A horizontally scrolling region that cannot be reached by keyboard is
       * a WCAG 2.1.1 failure. Add tabindex only where it actually scrolls, so
       * we do not litter the tab order with dozens of unreachable stops.
       */
      var check = function () {
        var overflows = pre.scrollWidth > pre.clientWidth + 1;
        if (overflows && !pre.hasAttribute("tabindex")) {
          pre.setAttribute("tabindex", "0");
          pre.setAttribute("role", "region");
          pre.setAttribute(
            "aria-label",
            (block.getAttribute("data-file") ||
              (lang ? lang + " code" : "Code")) + ", scrollable"
          );
        } else if (!overflows && pre.hasAttribute("tabindex")) {
          pre.removeAttribute("tabindex");
          pre.removeAttribute("role");
          pre.removeAttribute("aria-label");
        }
      };

      check();
      if ("ResizeObserver" in window) new ResizeObserver(check).observe(pre);
      // Fonts land after first paint and change the measurement.
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(check);
    });
  })();

  /* ── 4b · Scrollable data tables ────────────────────────────────────────
   * On narrow screens tables stay tables rather than becoming mislabeled card
   * stacks. When they overflow, make the scroll region keyboard reachable and
   * announce what it is; otherwise keep it out of the tab order.
   */
  (function tables() {
    var tables = document.querySelectorAll(".prose table");
    if (!tables.length) return;

    Array.prototype.forEach.call(tables, function (table, index) {
      var hint = null;
      var hintId = "table-scroll-hint-" + (index + 1);
      var originalDescribedBy = table.getAttribute("aria-describedby") || "";

      var check = function () {
        var overflows = table.scrollWidth > table.clientWidth + 1;
        if (overflows) {
          table.setAttribute("tabindex", "0");
          table.dataset.overflowing = "true";
          // Naming precedence is aria-labelledby > aria-label > <caption>. A
          // generic aria-label here would silently outrank a real caption and
          // the table would announce as "Scrollable data table 1" instead of
          // its title, so point at the caption whenever one exists.
          var caption = table.querySelector("caption");
          if (caption) {
            if (!caption.id) caption.id = "table-caption-" + (index + 1);
            table.removeAttribute("aria-label");
            table.setAttribute("aria-labelledby", caption.id);
          } else if (!table.hasAttribute("aria-label")) {
            table.setAttribute("aria-label", "Scrollable data table " + (index + 1));
          }

          if (!hint) {
            hint = document.createElement("p");
            hint.className = "table-scroll-hint";
            hint.id = hintId;
            hint.textContent = "Swipe or use arrow keys to compare every column →";
            table.insertAdjacentElement("beforebegin", hint);
          }
          hint.hidden = false;
          table.setAttribute(
            "aria-describedby",
            [originalDescribedBy, hintId].filter(Boolean).join(" ")
          );
        } else {
          table.removeAttribute("tabindex");
          delete table.dataset.overflowing;
          if (/^Scrollable data table /.test(table.getAttribute("aria-label") || "")) {
            table.removeAttribute("aria-label");
          }
          if (hint) hint.hidden = true;
          if (originalDescribedBy) {
            table.setAttribute("aria-describedby", originalDescribedBy);
          } else {
            table.removeAttribute("aria-describedby");
          }
        }
      };

      check();
      if ("ResizeObserver" in window) new ResizeObserver(check).observe(table);
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(check);
    });
  })();

  /* ── 4c · Share row "Copy link" ─────────────────────────────────────────
   * The anchor's href is the canonical URL, so with JS off it simply navigates
   * there — the correct no-JS baseline. With JS we intercept and copy instead.
   */
  (function copyLink() {
    var el = document.querySelector("[data-copy-link]");
    if (!el) return;

    var live = document.querySelector(".sr-live");
    if (!live) {
      live = document.createElement("div");
      live.className = "sr-live";
      live.setAttribute("role", "status");
      live.setAttribute("aria-live", "polite");
      document.body.appendChild(live);
    }

    var label = el.textContent;
    var timer;

    el.addEventListener("click", function (e) {
      var url = el.getAttribute("href") || location.href;
      if (!navigator.clipboard || !window.isSecureContext) return; // let it navigate
      e.preventDefault();
      navigator.clipboard.writeText(new URL(url, location.href).href).then(
        function () {
          el.textContent = "Copied";
          el.dataset.state = "copied";
          live.textContent = "Link copied to clipboard";
          clearTimeout(timer);
          timer = setTimeout(function () {
            el.textContent = label;
            delete el.dataset.state;
            live.textContent = "";
          }, 2000);
        },
        function () {
          live.textContent = "Copy failed — the address bar has the link";
        }
      );
    });
  })();

  /* ── 4c · Generic scrollable regions ────────────────────────────────────
   * Anything that scrolls horizontally must be reachable by keyboard, or the
   * content inside it is unreachable without a mouse (WCAG 2.1.1). The code
   * module does this for <pre>; the results table needs it too. tabindex is
   * added only while the element actually overflows, so we never litter the tab
   * order with stops that do not scroll.
   */
  (function scrollables() {
    var nodes = document.querySelectorAll("[data-scrollable]");
    if (!nodes.length) return;

    Array.prototype.forEach.call(nodes, function (el) {
      var label = el.getAttribute("data-scroll-label") || "Scrollable content";
      var sync = function () {
        var overflows = el.scrollWidth > el.clientWidth + 1;
        if (overflows && !el.hasAttribute("tabindex")) {
          el.setAttribute("tabindex", "0");
          el.setAttribute("role", "region");
          el.setAttribute("aria-label", label + ", scrollable");
        } else if (!overflows && el.hasAttribute("tabindex")) {
          el.removeAttribute("tabindex");
          el.removeAttribute("role");
          el.removeAttribute("aria-label");
        }
      };
      sync();
      if ("ResizeObserver" in window) new ResizeObserver(sync).observe(el);
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(sync);
    });
  })();

  /* ── 5 · TOC scroll-spy ─────────────────────────────────────────────────
   * IntersectionObserver over the headings, not a scroll listener. The
   * rootMargin pins the "current" line just below the sticky header.
   */
  (function toc() {
    var nav = document.querySelector(".toc");
    if (!nav || !("IntersectionObserver" in window)) return;

    var links = nav.querySelectorAll(".toc__link, a[href^='#']");
    if (!links.length) return;

    var map = {};
    var targets = [];
    Array.prototype.forEach.call(links, function (a) {
      var id = decodeURIComponent((a.getAttribute("href") || "").slice(1));
      if (!id) return;
      var el = document.getElementById(id);
      if (!el) return;
      map[id] = a;
      targets.push(el);
    });
    if (!targets.length) return;

    var visible = new Set();

    function paint() {
      var current = null;
      for (var i = 0; i < targets.length; i++) {
        if (visible.has(targets[i].id)) {
          current = targets[i].id;
          break;
        }
      }
      // Nothing intersecting means we are between two headings — keep the last
      // one above the fold rather than clearing the highlight.
      if (!current) {
        for (var j = targets.length - 1; j >= 0; j--) {
          if (targets[j].getBoundingClientRect().top < 120) {
            current = targets[j].id;
            break;
          }
        }
      }
      for (var id in map) {
        var on = id === current;
        map[id].classList.toggle("is-active", on);
        if (on) {
          map[id].setAttribute("aria-current", "true");
        } else {
          map[id].removeAttribute("aria-current");
        }
      }
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) visible.add(e.target.id);
          else visible.delete(e.target.id);
        });
        paint();
      },
      { rootMargin: "-" + (68 + 16) + "px 0px -70% 0px", threshold: 0 }
    );

    targets.forEach(function (t) {
      io.observe(t);
    });
    paint();
  })();

  /* ── 6 · Reading progress ───────────────────────────────────────────────
   * _progress.scss drives this entirely from `animation-timeline: scroll()`
   * where it exists. This runs only in the browsers that lack it.
   */
  (function progress() {
    var bar = document.querySelector(".progress");
    if (!bar) return;
    if (window.CSS && CSS.supports && CSS.supports("animation-timeline", "scroll()")) return;

    var ticking = false;

    function paint() {
      ticking = false;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      var p = max > 0 ? window.scrollY / max : 0;
      bar.style.setProperty("--progress", Math.min(1, Math.max(0, p)));
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(paint);
    }

    addEventListener("scroll", onScroll, { passive: true });
    addEventListener("resize", onScroll, { passive: true });
    paint();
  })();
})();
