#!/usr/bin/env python3
"""
generate-start-here.py — bhapstar
-------------------------------------------------------------
Writes start-here.html: a guided path through the articles, in the order
someone new to all of this should read them.

    python generate-start-here.py

Why this page exists, and why it is not articles.html:

  articles.html is the shelf. Everything, newest first, which is what a
  returning reader wants. This page is the reading list: fewer choices, in
  a deliberate order, for someone who has just found the site and does not
  yet know which end to pick up.

Where the order comes from:

  Two optional fields on any article entry in site-data.json.

      "stage":      one of plan, capture, process, gear
      "stageOrder": an integer, low numbers first within that stage

  An article with no "stage" simply does not appear here. That is the
  intended way to keep something off the path without hiding it from the
  site: it still gets a page, still appears on articles.html, still goes in
  the feed. Nothing needs a "stageOrder"; entries without one fall to the
  end of their stage, newest first.

  Because the stages are their own field rather than a reuse of
  "category", an article can sit under Gear on the shelf and under Capture
  on the path. The Seestar tour is the obvious case.

Routes (the "what are you shooting with?" pills at the top):

      "paths": ["camera", "smartscope", "rig"]

  A list, because most articles are not tied to one kind of kit. The
  balcony piece is about a location rather than a camera, so it belongs to
  three routes at once; the phone Milky Way guide belongs to exactly one.

  Valid values are the keys in ROUTES below. An article with no "paths"
  is treated as belonging to all of them, which is the safe default: it
  keeps showing rather than quietly vanishing when somebody picks a route.

  The filter is progressive enhancement. The page ships with every article
  in the HTML and no route selected, so crawlers and anyone without JS get
  the full list.

The page is fully generated, so editing start-here.html by hand will be
overwritten on the next build. Change the copy in STAGES below, or the
stage fields in site-data.json.
"""

import json
import os
from datetime import datetime
from html import escape as esc

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT = "start-here.html"
ARTICLE_DIR = "articles"

PAGE_TITLE = "Start Here"
PAGE_DESC = ("A guided path through astrophotography, from finding your way "
             "around the night sky to processing your first deep-sky image. "
             "Written for anyone starting out, with no equipment assumed.")

SUBTITLE = "New to all of this? Read in this order."

INTRO = (
    "If you have just found this site, this page is the place to begin. "
    "Everything below is arranged in the order the work actually happens: "
    "you plan a night, you capture what you can, and then you process what "
    "you caught. You do not need a telescope to start. The first few pieces "
    "assume nothing more than your eyes and a phone."
)

# Stage key -> (heading, standfirst). Order here is the order on the page.
# The headings carry no leading number: the number is rendered separately so
# that a stage emptied by a route filter does not leave a gap in the count.
STAGES = [
    ("plan", "Plan the night",
     "Half of a good image is decided before anything is switched on. "
     "Knowing what is up, how dark your sky really is, and where to point."),
    ("capture", "Capture the image",
     "From a phone on a wall to a rig running itself all night. Start with "
     "whatever you already own."),
    ("process", "Process what you caught",
     "The part that surprises most people. A finished image is built from "
     "hundreds of frames, and some of those frames are not photographs at all."),
    ("gear", "The gear behind it",
     "What I actually use, and why. Useful once you know what you want a "
     "piece of kit to do for you."),
]

# Route key -> pill label. Order here is the order of the pills, which runs
# from least equipment to most.
ROUTES = [
    ("phone", "A phone"),
    ("camera", "A camera and lens"),
    ("smartscope", "A smart telescope"),
    ("rig", "A full rig"),
]
ROUTE_KEYS = [key for key, _ in ROUTES]

# The chooser is rendered immediately after this stage. Planning is the same
# job whatever you own, so the pills sit below it rather than above: the
# reader gets the common ground first, then chooses. Anything before the
# chooser is exempt from filtering, which the script works out from document
# position rather than from a second list that could drift out of step.
CHOOSER_AFTER = "plan"

ROUTE_PROMPT = "What are you shooting with?"
ROUTE_HELP = ("Optional. Everything above applies whatever you own. From here "
              "the path splits by kit, so pick one and the rest trims to "
              "suit. Nothing is more than a click away.")

# A closing line shown at the end of the path, for routes that stop somewhere
# short of the whole thing. Keyed by route. The {route:key} token becomes a
# button that switches to that route, so the reader does not have to scroll
# back up to the pills. Any route with no entry here simply gets nothing.
ROUTE_NOTES = {
    "phone": ("That is the whole phone path. A phone will get you the Milky "
              "Way arching over a horizon, and on a dark night it will get "
              "you more of it than you expect. What it will not get you is "
              "deep sky: the faint nebulae and galaxies need longer "
              "exposures than a handset will give you. When you are ready "
              "for that, {route:camera} picks up exactly where this one "
              "stops."),
}
ROUTE_NOTE_LINKS = {
    "camera": "the camera and lens route",
    "smartscope": "the smart telescope route",
    "rig": "the full rig route",
    "phone": "the phone route",
}

# Appended to the end of a stage, for stages that lead somewhere else.
STAGE_FOOTERS = {
    "gear": ('<a class="sh-more" href="/gear.html">'
             'Every piece of gear I use <span aria-hidden="true">&#8594;</span></a>'),
}


def sort_key(entry):
    """stageOrder first, then newest, so a partly ordered stage still reads well."""
    order = entry.get("stageOrder")
    order = order if isinstance(order, int) else 999
    try:
        date = datetime.strptime(entry.get("date", ""), "%d-%m-%Y")
    except (TypeError, ValueError):
        date = datetime.min
    return (order, -date.toordinal())


def load_articles():
    with open(DATA, "r", encoding="utf-8") as f:
        items = json.load(f)

    by_stage = {key: [] for key, _, _ in STAGES}
    for entry in items:
        if not isinstance(entry, dict) or entry.get("section") != "article":
            continue
        if not entry.get("slug") or entry.get("hidden"):
            continue
        stage = entry.get("stage")
        if stage in by_stage:
            by_stage[stage].append(entry)

    for key in by_stage:
        by_stage[key].sort(key=sort_key)
    return by_stage


def card_paths(entry):
    """Which routes an article belongs to.

    An entry with no "paths", or one listing a key that is not a real route,
    falls back to every route. Failing open means a typo in site-data.json
    shows an extra card rather than silently losing one.
    """
    raw = entry.get("paths")
    if not isinstance(raw, list):
        return ROUTE_KEYS
    keys = [p for p in raw if p in ROUTE_KEYS]
    return keys or ROUTE_KEYS


def build_card(entry, number):
    """One step on the path. Numbered, because the order is the whole point."""
    meta_bits = [b for b in (entry.get("category"), entry.get("readTime")) if b]
    sep = ' <span aria-hidden="true">&middot;</span> '
    meta = ""
    if meta_bits:
        meta = ('<span class="sh-meta">'
                + sep.join(esc(b) for b in meta_bits) + "</span>")

    paths = " ".join(card_paths(entry))

    return (
        f'          <a class="sh-card" data-paths="{esc(paths)}" '
        f'href="/{ARTICLE_DIR}/{esc(entry.get("slug", ""))}.html">\n'
        f'            <span class="sh-num" aria-hidden="true">{number}</span>\n'
        f'            <span class="sh-text">\n'
        f'              <span class="sh-title">{esc(entry.get("title", ""))}</span>\n'
        f'              <span class="sh-desc">{esc(entry.get("desc", "")[:150])}</span>\n'
        f'              {meta}\n'
        f'            </span>\n'
        f'          </a>\n'
    )


def build_stages(by_stage, chooser=""):
    out = []
    number = 0
    placed = False
    for key, heading, standfirst in STAGES:
        entries = by_stage.get(key, [])
        footer = STAGE_FOOTERS.get(key, "")
        # A stage with nothing in it and nowhere to point is left out rather
        # than rendered as an empty heading.
        if not entries and not footer:
            continue

        number += 1
        cards = "".join(build_card(e, i)
                        for i, e in enumerate(entries, start=1))
        footer_html = f'          {footer}\n' if footer else ""
        out.append(
            f'      <section class="sh-stage" data-stage="{esc(key)}">\n'
            f'        <h2 class="sh-stage-title">'
            f'<span class="sh-stage-num" aria-hidden="true">{number}.</span> '
            f'{esc(heading)}</h2>\n'
            f'        <p class="sh-stage-lede">{esc(standfirst)}</p>\n'
            f'        <div class="sh-list">\n'
            f'{cards}{footer_html}'
            f'        </div>\n'
            f'      </section>\n'
        )

        if chooser and key == CHOOSER_AFTER:
            out.append(chooser)
            placed = True

    # If the anchor stage produced nothing, the chooser still has to appear.
    # Above everything is the safe fallback: it never sits under a stage it
    # is supposed to control.
    if chooser and not placed:
        out.insert(0, chooser)

    return "".join(out)


def build_route_notes():
    """Per-route closing lines. All are in the HTML and hidden; the script
    reveals the one matching the active route, and none of them when the
    whole path is showing."""
    out = []
    for key, _ in ROUTES:
        text = ROUTE_NOTES.get(key)
        if not text:
            continue

        body = ""
        rest = esc(text)
        while "{route:" in rest:
            before, _, after = rest.partition("{route:")
            target, _, rest = after.partition("}")
            label = ROUTE_NOTE_LINKS.get(target, "that route")
            body += before + (
                f'<button type="button" class="sh-route-jump" '
                f'data-goto="{esc(target)}">{esc(label)}</button>'
            )
        body += rest

        out.append(
            f'      <p class="sh-route-note" data-note="{esc(key)}" hidden>'
            f'{body}</p>\n'
        )
    return "".join(out)


def build_chooser():
    """The route pills. No option is preselected, so the default view is the
    whole path; 'Show everything' is the way back rather than the start."""
    pills = "".join(
        f'          <button type="button" class="filter-pill sh-route" '
        f'data-route="{esc(key)}" aria-pressed="false">{esc(label)}</button>\n'
        for key, label in ROUTES
    )
    return (
        f'      <div class="sh-chooser" id="shChooser" hidden>\n'
        f'        <p class="sh-chooser-q">{esc(ROUTE_PROMPT)}</p>\n'
        f'        <div class="filter-pills" role="group" '
        f'aria-label="{esc(ROUTE_PROMPT)}">\n'
        f'{pills}'
        f'          <button type="button" class="filter-pill sh-route sh-route-all active" '
        f'data-route="all" aria-pressed="true">Show everything</button>\n'
        f'        </div>\n'
        f'        <p class="sh-chooser-help">{esc(ROUTE_HELP)}</p>\n'
        f'      </div>\n'
    )


def build_json_ld(by_stage):
    """An ItemList of the path, in path order, so the sequence is legible."""
    elements = []
    position = 1
    for key, _, _ in STAGES:
        for entry in by_stage.get(key, []):
            elements.append({
                "@type": "ListItem",
                "position": position,
                "url": f"{DOMAIN}/{ARTICLE_DIR}/{entry.get('slug', '')}.html",
                "name": entry.get("title", ""),
            })
            position += 1

    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Start Here: a guided path through astrophotography",
        "description": PAGE_DESC,
        "url": f"{DOMAIN}/{OUT}",
        "numberOfItems": len(elements),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "itemListElement": elements,
    }
    return json.dumps(schema, ensure_ascii=False)


CSS = ""   # moved to /styles.css (PAGE: Start Here)

SCRIPT = """
(function () {
  var chooser = document.getElementById('shChooser');
  if (!chooser) return;

  var pills  = Array.prototype.slice.call(chooser.querySelectorAll('.sh-route'));
  var stages = Array.prototype.slice.call(document.querySelectorAll('.sh-stage'));
  var notes  = Array.prototype.slice.call(document.querySelectorAll('.sh-route-note'));
  if (!pills.length || !stages.length) return;

  // Stages above the chooser are common to every route and are left alone.
  // Position in the document decides this, so moving the chooser in the
  // generator is all it takes to change what the pills govern.
  var FOLLOWING = window.Node ? window.Node.DOCUMENT_POSITION_FOLLOWING : 4;
  function governed(el) {
    return !!(chooser.compareDocumentPosition(el) & FOLLOWING);
  }
  var filterable = stages.filter(governed);

  // Only reveal the control once we know the script is running, so no-JS
  // readers get the full path rather than a set of dead buttons.
  chooser.hidden = false;

  var KEY = 'bhapstar:startHereRoute';
  var FADE = 180;   // must match the CSS transition duration
  var current = 'all';
  var token = 0;    // guards against a second pill tapped mid-transition

  var still = false;
  try {
    still = window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) {}

  // Show or hide cards, stages and notes for a route, and renumber whatever
  // is left so the path still reads 1, 2, 3 with no gaps.
  function commit(route) {
    var stageNumber = 0;

    stages.forEach(function (stage) {
      var cards = Array.prototype.slice.call(stage.querySelectorAll('.sh-card'));
      var governs = filterable.indexOf(stage) !== -1;
      var shown = 0;

      cards.forEach(function (card) {
        var paths = (card.getAttribute('data-paths') || '').split(/\\s+/);
        var match = route === 'all' || !governs ||
                    paths.indexOf(route) !== -1;
        card.hidden = !match;
        if (match) {
          shown += 1;
          var num = card.querySelector('.sh-num');
          if (num) num.textContent = shown;
        }
      });

      // A stage with nothing left in it collapses entirely, footer included.
      var empty = shown === 0;
      stage.hidden = empty;
      if (empty) return;

      stageNumber += 1;
      var label = stage.querySelector('.sh-stage-num');
      if (label) label.textContent = stageNumber + '.';
    });

    notes.forEach(function (note) {
      note.hidden = note.getAttribute('data-note') !== route;
    });

    pills.forEach(function (pill) {
      var on = pill.getAttribute('data-route') === route;
      pill.classList.toggle('active', on);
      pill.setAttribute('aria-pressed', on ? 'true' : 'false');
    });

    current = route;

    try {
      if (route === 'all') sessionStorage.removeItem(KEY);
      else sessionStorage.setItem(KEY, route);
    } catch (e) { /* private mode, not worth caring about */ }
  }

  function fading() {
    return filterable.concat(notes.filter(function (n) { return !n.hidden; }));
  }

  function apply(route, animate) {
    if (route === current) return;

    if (!animate || still) { commit(route); return; }

    var mine = ++token;
    var out = fading();
    out.forEach(function (el) { el.classList.add('sh-swapping'); });

    window.setTimeout(function () {
      if (mine !== token) return;   // a newer choice took over
      commit(route);
      // Clear on everything, including the note that has just appeared.
      filterable.forEach(function (el) { el.classList.remove('sh-swapping'); });
      notes.forEach(function (el) { el.classList.remove('sh-swapping'); });
    }, FADE);
  }

  pills.forEach(function (pill) {
    pill.addEventListener('click', function () {
      var route = pill.getAttribute('data-route');
      // Tapping the active route a second time clears it.
      apply(pill.classList.contains('active') ? 'all' : route, true);
    });
  });

  // "follow the camera and lens route" inside a closing note.
  document.addEventListener('click', function (ev) {
    var jump = ev.target.closest && ev.target.closest('.sh-route-jump');
    if (!jump) return;
    apply(jump.getAttribute('data-goto'), true);
    chooser.scrollIntoView({ behavior: still ? 'auto' : 'smooth',
                             block: 'start' });
  });

  var saved = null;
  try { saved = sessionStorage.getItem(KEY); } catch (e) {}
  var valid = pills.some(function (p) { return p.getAttribute('data-route') === saved; });
  if (saved && valid) apply(saved, false);   // no animation on first paint
})();
"""


OUTRO = (
    '      <section class="sh-outro">\n'
    '        <p>That is the path. When you want the full list rather than a '
    'route through it, <a href="/articles.html">every article lives here</a>, '
    'newest first, and the <a href="/gallery.html">gallery</a> has the images '
    'these guides were written from.</p>\n'
    '        <p>If you would rather hear when something new goes up, there is '
    'a monthly newsletter you can join from the <a href="/index.html">home '
    'page</a>.</p>\n'
    '      </section>\n'
)


def build_page(by_stage):
    page_url = f"{DOMAIN}/{OUT}"
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{esc(PAGE_TITLE)} — Bhapstar Astrophotography</title>
  <link rel="icon" href="/images/icons/favicon-32.png" sizes="32x32" type="image/png" />
  <link rel="apple-touch-icon" href="/images/icons/apple-touch-icon.png" />
  <meta name="theme-color" content="#050414" />
  <link rel="canonical" href="{esc(page_url)}" />
  <link rel="alternate" type="application/rss+xml" title="Fragments of the Universe" href="/feed.xml" />
  <meta name="description" content="{esc(PAGE_DESC)}" />
  <meta name="author" content="Bhapinder Singh" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta property="og:description" content="{esc(PAGE_DESC)}" />
  <meta property="og:url" content="{esc(page_url)}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta name="twitter:description" content="{esc(PAGE_DESC)}" />
  <link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>
  <link rel="stylesheet" href="/styles.css" />

  <!-- Page CSS lives in /styles.css under "PAGE: Start Here". -->

  <script type="application/ld+json">
{build_json_ld(by_stage)}
  </script>
</head>
<body class="page-start-here">

<!-- ── Header (injected by partials.js) ── -->
<div id="siteHeader"></div>

<main>
  <section class="section">
    <div class="wrap">

      <div class="section-head gallery-head sh-header">
        <div class="gallery-topline">
          <h1>{esc(PAGE_TITLE)}</h1>
        </div>
        <p class="sh-subtitle">{esc(SUBTITLE)}</p>
        <p class="sh-intro">{esc(INTRO)}</p>
      </div>

{build_stages(by_stage, build_chooser())}
{build_route_notes()}
{OUTRO}
    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

  <script src="/partials/partials.js"></script>
  <script>{SCRIPT}</script>
</body>
</html>
'''


def main():
    by_stage = load_articles()
    total = sum(len(v) for v in by_stage.values())

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build_page(by_stage))

    bits = ", ".join(f"{k}: {len(by_stage.get(k, []))}" for k, _, _ in STAGES)
    print(f"✓ {OUT}  ({total} articles on the path — {bits})")

    # A stage that has emptied out is worth knowing about, since the page
    # silently drops it rather than rendering a bare heading.
    for key, heading, _ in STAGES:
        if not by_stage.get(key) and key not in STAGE_FOOTERS:
            print(f"  ! stage '{key}' ({heading}) is empty and was omitted")


if __name__ == "__main__":
    main()
