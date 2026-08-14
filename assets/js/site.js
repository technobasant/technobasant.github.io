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

    Array.prototype.forEach.call(blocks, function (block, blockIndex) {
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
          // A named region is a landmark, and a tutorial with nine bash blocks
          // was minting nine landmarks all called "bash code, scrollable" —
          // axe's landmark-unique, and useless in a landmark list. Prefer the
          // filename, which is already unique and meaningful; fall back to the
          // language plus the block's position in the article.
          pre.setAttribute(
            "aria-label",
            (block.getAttribute("data-file") ||
              (lang ? lang + " code" : "Code") + " block " + (blockIndex + 1)) +
              ", scrollable"
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

  /* ── 7 · Writing catalog ────────────────────────────────────────────────
   * JSON index + combobox. The form never navigates: action is an in-page
   * hash, submit is cancelled, and results render into a listbox while the
   * catalog below is filtered. Cached copies of site.js are busted via ?v=.
   */
  (function writingCatalog() {
    var form = document.getElementById("writing-find");
    var catalog = document.getElementById("writing-catalog");
    var dataEl = document.getElementById("writing-index-data");
    if (!form || !catalog) return;

    var input = document.getElementById("writing-q");
    var suggest = document.getElementById("writing-suggest");
    var status = document.getElementById("writing-status");
    var empty = document.getElementById("writing-empty");
    var note = document.getElementById("writing-catalog-note");
    var title = document.getElementById("writing-catalog-title");
    var page = document.querySelector(".page--writing");
    var lead = document.querySelector("[data-catalog-lead]");
    var list = document.getElementById("writing-results");
    var typeInputs = form.querySelectorAll('input[name="type"]');
    var topicLinks = catalog.querySelectorAll("[data-filter-topic]");
    var seriesLinks = catalog.querySelectorAll("[data-filter-series]");
    var clears = document.querySelectorAll("[data-writing-clear]");
    var items = catalog.querySelectorAll("[data-catalog-item]");
    var active = -1;
    var ranked = [];
    var index = [];

    try {
      index = dataEl ? JSON.parse(dataEl.textContent) : [];
    } catch (err) {
      index = [];
    }

    if (!index.length) {
      Array.prototype.forEach.call(items, function (el) {
        index.push({
          id: el.getAttribute("data-id") || "",
          url: (el.querySelector("a[href]") || {}).getAttribute("href") || "",
          title: (el.querySelector(".post-card__title") || el).textContent.trim(),
          kind: el.getAttribute("data-kind") || "",
          label: el.getAttribute("data-kind") || "Writing",
          tags: (el.getAttribute("data-tags") || "").split(/\s+/),
          series: el.getAttribute("data-series") || "",
          blurb: (el.querySelector(".post-card__desc, .case-card__hook") || {}).textContent || "",
          text: (el.getAttribute("data-search") || "") + " " + (el.textContent || "")
        });
      });
    }

    var byId = {};
    Array.prototype.forEach.call(items, function (el, i) {
      var id = el.getAttribute("data-id") || "";
      var row = el.closest("li") || el;
      row.setAttribute("data-origin", String(i));
      if (id) byId[id] = { el: el, row: row };
    });

    var STOP = {
      a: 1, an: 1, and: 1, as: 1, at: 1, by: 1, for: 1, from: 1, in: 1,
      into: 1, of: 1, on: 1, or: 1, the: 1, to: 1, with: 1, your: 1
    };
    var ALIASES = {
      pg: ["postgres", "postgresql", "pgbackrest"],
      postgres: ["postgresql", "pgbackrest", "pg"],
      postgresql: ["postgres", "pgbackrest", "pg"],
      pgbackrest: ["postgres", "postgresql", "backup", "tls"],
      backup: ["pgbackrest", "postgres", "replica"],
      wg: ["wireguard", "vpn", "wgeasy"],
      wireguard: ["vpn", "wg", "wgeasy"],
      vpn: ["wireguard", "wg"],
      scylla: ["scylladb", "nodetool", "sstable", "cassandra"],
      scylladb: ["scylla", "nodetool", "sstable"],
      rustdesk: ["hbbs", "hbbr", "relay", "remote"],
      stalwart: ["mail", "smtp", "imap", "mx", "mailbox"],
      mail: ["stalwart", "mailbox", "smtp"],
      vagrant: ["qemu", "amd64", "vmnet", "apple"],
      qemu: ["vagrant", "amd64", "vmnet"],
      amd64: ["vagrant", "qemu", "x86"],
      failover: ["ha", "replica", "primary", "cluster"],
      ansible: ["rhel", "pgbackrest", "playbook"]
    };
    var TAG_EXPAND = {
      postgres: "postgresql postgres pg pgbackrest backup replica wal tls ansible rhel",
      "self-hosted": "vpn wireguard rustdesk stalwart mail mailbox vps docker relay mx smtp",
      "distributed-databases": "scylla scylladb mongodb redis mysql galera failover ha replica cluster",
      "ai-agents": "agent rag llm model provenance",
      "data-quality": "contract schema lineage replay",
      "iceberg-lakehouse": "iceberg lakehouse spark",
      "observability-slo": "slo prometheus grafana"
    };

    function fold(s) {
      return String(s || "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
    }

    function dist(a, b) {
      if (a === b) return 0;
      if (!a) return b.length;
      if (!b) return a.length;
      var prev = [];
      var j;
      for (j = 0; j <= b.length; j++) prev[j] = j;
      for (var i = 1; i <= a.length; i++) {
        var cur = [i];
        for (j = 1; j <= b.length; j++) {
          var cost = a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1;
          var ins = cur[j - 1] + 1;
          var del = prev[j] + 1;
          var sub = prev[j - 1] + cost;
          cur[j] = ins < del ? (ins < sub ? ins : sub) : del < sub ? del : sub;
        }
        prev = cur;
      }
      return prev[b.length];
    }

    function tokenHits(hay, compactHay, token) {
      if (!token) return 0;
      if (hay.indexOf(token) !== -1) return 24 + Math.min(token.length, 10);
      if (compactHay.indexOf(token) !== -1) return 20;
      var words = hay.split(" ");
      var allow = token.length >= 6 ? 2 : token.length >= 4 ? 1 : 0;
      var best = 0;
      for (var i = 0; i < words.length; i++) {
        var w = words[i];
        if (!w) continue;
        if (w.indexOf(token) !== -1) best = Math.max(best, 18);
        else if (token.length >= 4 && w.length >= 4 && token.indexOf(w) !== -1) best = Math.max(best, 14);
        else if (allow && Math.abs(w.length - token.length) <= allow && dist(w, token) <= allow) {
          best = Math.max(best, 12);
        }
      }
      return best;
    }

    function hayOf(doc) {
      if (doc._hay) return doc._hay;
      var tags = doc.tags || [];
      var extra = "";
      for (var i = 0; i < tags.length; i++) {
        if (TAG_EXPAND[tags[i]]) extra += " " + TAG_EXPAND[tags[i]];
      }
      doc._hay = fold([doc.title, doc.blurb, doc.kind, doc.label, doc.series, tags.join(" "), doc.text, extra].join(" "));
      return doc._hay;
    }

    function queryScore(hay, q) {
      var folded = fold(q);
      if (!folded) return 1;
      var compactHay = hay.replace(/ /g, "");
      var compactQ = folded.replace(/ /g, "");
      var score = 0;
      if (hay.indexOf(folded) !== -1) score += 80;
      else if (compactQ.length >= 4 && compactHay.indexOf(compactQ) !== -1) score += 55;
      var raw = folded.split(" ");
      var toks = [];
      for (var t = 0; t < raw.length; t++) {
        if (raw[t] && raw[t].length > 1 && !STOP[raw[t]]) toks.push(raw[t]);
      }
      if (!toks.length) toks = raw.filter(Boolean);
      var hits = 0;
      for (var i = 0; i < toks.length; i++) {
        var token = toks[i];
        var s = tokenHits(hay, compactHay, token);
        if (!s && ALIASES[token]) {
          for (var k = 0; k < ALIASES[token].length && !s; k++) {
            s = Math.floor(tokenHits(hay, compactHay, ALIASES[token][k]) * 0.85);
          }
        }
        if (s) hits += 1;
        score += s;
      }
      if (!hits) return 0;
      if (toks.length > 1 && hits < toks.length) {
        if (compactQ.length >= 5 && compactHay.indexOf(compactQ) !== -1) score += 20;
        else if (hits < Math.ceil(toks.length / 2)) return 0;
        else score -= (toks.length - hits) * 6;
      }
      return score;
    }

    function kindMatches(kind, type) {
      if (!type || type === "all") return true;
      if (type === "essay") return kind === "essay" || kind === "note";
      return kind === type;
    }

    function stateFromForm() {
      var typeEl = form.querySelector('input[name="type"]:checked');
      return {
        q: (input && input.value ? input.value : "").trim(),
        type: typeEl ? typeEl.value : "all",
        topic: form.getAttribute("data-topic") || "",
        series: form.getAttribute("data-series") || ""
      };
    }

    function stateFromURL() {
      var p = new URLSearchParams(location.search);
      return {
        q: (p.get("q") || "").trim(),
        type: p.get("type") || "all",
        topic: p.get("topic") || "",
        series: p.get("series") || ""
      };
    }

    function applyToForm(state) {
      if (input) input.value = state.q;
      var type = state.type || "all";
      var found = false;
      Array.prototype.forEach.call(typeInputs, function (el) {
        el.checked = el.value === type;
        if (el.checked) found = true;
      });
      if (!found && typeInputs[0]) typeInputs[0].checked = true;
      form.setAttribute("data-topic", state.topic || "");
      form.setAttribute("data-series", state.series || "");
    }

    function writeURL(state) {
      var p = new URLSearchParams();
      if (state.q) p.set("q", state.q);
      if (state.type && state.type !== "all") p.set("type", state.type);
      if (state.topic) p.set("topic", state.topic);
      if (state.series) p.set("series", state.series);
      var qs = p.toString();
      var next = location.pathname + (qs ? "?" + qs : "") + (qs ? "" : location.hash);
      var cur = location.pathname + location.search + (qs ? "" : location.hash);
      if (next !== cur) history.replaceState(null, "", next);
    }

    function filtering(state) {
      return !!(state.q || (state.type && state.type !== "all") || state.topic || state.series);
    }

    function scoreDoc(doc, state) {
      if (!kindMatches(doc.kind, state.type)) return 0;
      var tags = doc.tags || [];
      if (state.topic && tags.indexOf(state.topic) === -1) return 0;
      if (state.series && doc.series !== state.series) return 0;
      if (!state.q) return 1;
      var s = queryScore(hayOf(doc), state.q);
      if (fold(doc.title).indexOf(fold(state.q)) !== -1) s += 40;
      return s;
    }

    function escapeRe(s) {
      return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function fillMarked(node, text, toks) {
      node.textContent = "";
      if (!text) return;
      if (!toks.length) {
        node.textContent = text;
        return;
      }
      var re;
      try {
        re = new RegExp("(" + toks.map(escapeRe).join("|") + ")", "ig");
      } catch (e) {
        node.textContent = text;
        return;
      }
      var parts = String(text).split(re);
      for (var i = 0; i < parts.length; i++) {
        if (!parts[i]) continue;
        if (i % 2) {
          var mark = document.createElement("mark");
          mark.textContent = parts[i];
          node.appendChild(mark);
        } else {
          node.appendChild(document.createTextNode(parts[i]));
        }
      }
    }

    function queryToks(q) {
      var folded = fold(q);
      var raw = folded.split(" ");
      var toks = [];
      for (var i = 0; i < raw.length; i++) {
        if (raw[i] && raw[i].length > 1 && !STOP[raw[i]]) toks.push(raw[i]);
      }
      return toks;
    }

    function closeSuggest() {
      if (!suggest || !input) return;
      suggest.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      active = -1;
    }

    function setActive(n) {
      var opts = suggest ? suggest.querySelectorAll("[role='option']") : [];
      if (!opts.length) {
        active = -1;
        return;
      }
      if (n < 0) n = opts.length - 1;
      if (n >= opts.length) n = 0;
      active = n;
      for (var i = 0; i < opts.length; i++) {
        var on = i === active;
        opts[i].classList.toggle("is-active", on);
        opts[i].setAttribute("aria-selected", on ? "true" : "false");
        if (on) {
          input.setAttribute("aria-activedescendant", opts[i].id);
          opts[i].scrollIntoView({ block: "nearest" });
        }
      }
    }

    function openHit(i) {
      var hit = ranked[i];
      if (hit && hit.url) location.assign(hit.url);
    }

    function renderSuggest(state, hits) {
      if (!suggest || !input) return;
      suggest.textContent = "";
      if (!state.q || !hits.length) {
        closeSuggest();
        return;
      }
      var toks = queryToks(state.q);
      var max = Math.min(hits.length, 8);
      for (var i = 0; i < max; i++) {
        var doc = hits[i];
        var opt = document.createElement("li");
        opt.id = "writing-opt-" + i;
        opt.setAttribute("role", "option");
        opt.setAttribute("aria-selected", "false");
        opt.className = "writing-suggest__hit";
        opt.setAttribute("data-index", String(i));

        var kind = document.createElement("span");
        kind.className = "writing-suggest__kind";
        kind.textContent = doc.label || doc.kind || "Writing";
        var name = document.createElement("span");
        name.className = "writing-suggest__title";
        fillMarked(name, doc.title, toks);
        var blurb = document.createElement("span");
        blurb.className = "writing-suggest__blurb";
        blurb.textContent = doc.blurb || "";

        opt.appendChild(kind);
        opt.appendChild(name);
        if (doc.blurb) opt.appendChild(blurb);
        suggest.appendChild(opt);
      }
      suggest.hidden = false;
      input.setAttribute("aria-expanded", "true");
      active = -1;
    }

    function restoreOrder() {
      if (!list) return;
      var rows = Array.prototype.slice.call(list.children);
      rows.sort(function (a, b) {
        return (+a.getAttribute("data-origin") || 0) - (+b.getAttribute("data-origin") || 0);
      });
      for (var i = 0; i < rows.length; i++) list.appendChild(rows[i]);
    }

    function paintRail(state) {
      Array.prototype.forEach.call(topicLinks, function (a) {
        var on = state.topic && a.getAttribute("data-filter-topic") === state.topic;
        if (on) a.setAttribute("aria-current", "true");
        else a.removeAttribute("aria-current");
      });
      Array.prototype.forEach.call(seriesLinks, function (a) {
        var on = state.series && a.getAttribute("data-filter-series") === state.series;
        if (on) a.setAttribute("aria-current", "true");
        else a.removeAttribute("aria-current");
      });
    }

    function paint(opts) {
      opts = opts || {};
      var state = stateFromForm();
      var live = filtering(state);
      ranked = [];
      for (var i = 0; i < index.length; i++) {
        var score = scoreDoc(index[i], state);
        if (score > 0) {
          var hit = index[i];
          hit.score = score;
          ranked.push(hit);
        }
      }
      ranked.sort(function (a, b) {
        return b.score - a.score;
      });

      var visible = {};
      for (var r = 0; r < ranked.length; r++) visible[ranked[r].id] = ranked[r];

      Array.prototype.forEach.call(items, function (el) {
        var id = el.getAttribute("data-id") || "";
        var row = el.closest("li") || el;
        var show = !!visible[id];
        row.hidden = !show;
        row.classList.toggle("is-hit", show && live && !!state.q);
      });

      if (lead) lead.hidden = !!state.q || (live && scoreDoc({
        id: lead.getAttribute("data-id"),
        kind: lead.getAttribute("data-kind"),
        tags: (lead.getAttribute("data-tags") || "").split(/\s+/),
        series: lead.getAttribute("data-series") || "",
        title: "",
        text: "",
        blurb: ""
      }, state) <= 0 && !!state.q);

      if (lead && state.q) lead.hidden = true;

      if (list && state.q) {
        for (r = 0; r < ranked.length; r++) {
          var node = byId[ranked[r].id];
          if (node && node.row && node.row.parentNode === list) list.appendChild(node.row);
        }
      } else {
        restoreOrder();
      }

      if (empty) empty.hidden = ranked.length !== 0;
      Array.prototype.forEach.call(clears, function (btn) {
        btn.hidden = !live;
      });
      if (page) page.classList.toggle("is-filtering", live);
      paintRail(state);

      var n = ranked.length;
      var total = index.length;
      if (status) {
        status.textContent = live
          ? n + (n === 1 ? " result" : " results") + (state.q ? " for “" + state.q + "”" : "") + "."
          : total + " pieces.";
      }
      if (title) title.textContent = live ? (n === 1 ? "1 result" : n + " results") : "Index";
      if (note) {
        note.textContent = live
          ? "Showing " + n + " of " + total
          : total + " pieces";
      }

      if (opts.suggest !== false) renderSuggest(state, ranked);
      writeURL(state);
    }

    function clearFilters() {
      form.setAttribute("data-topic", "");
      form.setAttribute("data-series", "");
      if (input) input.value = "";
      if (typeInputs[0]) typeInputs[0].checked = true;
      closeSuggest();
      paint({ suggest: false });
      if (input) input.focus();
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (active >= 0) {
        openHit(active);
        return;
      }
      paint({ suggest: true });
      if (ranked.length === 1) openHit(0);
    });

    if (input) {
      input.addEventListener("input", function () {
        paint({ suggest: true });
      });
      input.addEventListener("search", function () {
        paint({ suggest: true });
      });
      input.addEventListener("focus", function () {
        var state = stateFromForm();
        if (state.q) paint({ suggest: true });
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          if (suggest && suggest.hidden) paint({ suggest: true });
          setActive(active + 1);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          setActive(active - 1);
        } else if (e.key === "Enter") {
          e.preventDefault();
          if (active >= 0) openHit(active);
          else if (ranked.length === 1) openHit(0);
          else {
            closeSuggest();
            if (list) list.scrollIntoView({ block: "start" });
          }
        } else if (e.key === "Escape") {
          e.preventDefault();
          if (suggest && !suggest.hidden) closeSuggest();
          else clearFilters();
        }
      });
    }

    if (suggest) {
      suggest.addEventListener("mousedown", function (e) {
        var hit = e.target.closest("[data-index]");
        if (!hit) return;
        e.preventDefault();
        openHit(+hit.getAttribute("data-index"));
      });
    }

    Array.prototype.forEach.call(typeInputs, function (el) {
      el.addEventListener("change", function () {
        paint({ suggest: true });
      });
    });

    Array.prototype.forEach.call(topicLinks, function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var slug = a.getAttribute("data-filter-topic") || "";
        var cur = form.getAttribute("data-topic") || "";
        form.setAttribute("data-topic", cur === slug ? "" : slug);
        paint({ suggest: false });
        closeSuggest();
      });
    });

    Array.prototype.forEach.call(seriesLinks, function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var slug = a.getAttribute("data-filter-series") || "";
        var cur = form.getAttribute("data-series") || "";
        form.setAttribute("data-series", cur === slug ? "" : slug);
        paint({ suggest: false });
        closeSuggest();
      });
    });

    Array.prototype.forEach.call(clears, function (btn) {
      btn.addEventListener("click", clearFilters);
    });

    document.addEventListener("click", function (e) {
      if (!form.contains(e.target)) closeSuggest();
    });

    addEventListener("popstate", function () {
      applyToForm(stateFromURL());
      paint({ suggest: false });
    });

    addEventListener("keydown", function (e) {
      if (e.defaultPrevented || e.altKey || e.ctrlKey) return;
      var t = e.target;
      var typing =
        t &&
        (t.tagName === "INPUT" ||
          t.tagName === "TEXTAREA" ||
          t.tagName === "SELECT" ||
          t.isContentEditable);
      var slash = e.key === "/" && !e.metaKey && !typing;
      var cmdK = (e.key === "k" || e.key === "K") && e.metaKey && !typing;
      if (!slash && !cmdK) return;
      if (!input) return;
      e.preventDefault();
      input.focus();
      input.select();
    });

    applyToForm(stateFromURL());
    paint({ suggest: false });
  })();
})();
