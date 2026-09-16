#!/usr/bin/env python3
"""
generate-tonight.py — bhapstar
-------------------------------------------------------------
Writes tonight.html: the planning tool. Where you are, how dark your sky
is, and what is worth pointing at on any night, plus the meteor showers
coming up next.

    python generate-tonight.py

Why this is its own page:

  The planner used to open start-here.html. That put a map, a location
  prompt and a 1 to 9 darkness scale in front of a reader who had not yet
  been outside, and it hid a tool people come back to on every clear night
  inside a page whose name says it is for first visits. Start Here now
  links here instead, and the nav carries it as Tonight.

The page has three parts:

  1. SKY       The planner. The shell is emitted here and filled in by
               /tonight-core.js, which holds all of the astronomy.

  2. SHOWERS   The next few meteor shower peaks, each with how bright the
               moon is on the peak night and a button that moves the
               planner to that date. The table below is the same one the
               meteor shower article carries. Keep the two in step.

  3. NEXT      One short block pointing at the Stellarium article, because
               this page gives a shortlist and Stellarium is how the
               session itself gets planned.

Tokens available in copy:

      {article:slug|label}   a link to an article page
      {url:path|label}       a link to anything else on the site
      {ext:https://...|label} a link off the site, opened in a new tab

The page is fully generated, so editing tonight.html by hand will be
overwritten on the next build. Change the copy below instead. Page CSS
lives in /styles.css under "PAGE: Start Here — sky panel" (the planner
shell) and "PAGE: Tonight" (everything else).
"""

import json
import os
import re
import sys
from html import escape as esc

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT = "tonight.html"
ARTICLE_DIR = "articles"
TONIGHT_CORE = "tonight-core.js"

PAGE_TITLE = "Tonight"
PAGE_DESC = ("Work out what is worth pointing at from where you are on any "
             "night: when it gets properly dark, what the moon is doing, "
             "which objects climb high enough, and when the next meteor "
             "shower peaks.")

SUBTITLE = "What is worth pointing at from where you are, and when."

SHARE_IMAGE = "images/andromeda-galaxy-m31.webp"


# ------------------------------------------------------------------ 1. SKY

# The planner. The reader drops a pin where they will be observing from,
# says how bright their sky is, and gets the darkness window, the moon,
# and every target from the gallery that is worth pointing at, ranked.
#
# All the astronomy lives in /tonight-core.js. This file emits the shell
# and the copy around it, and never calculates anything itself. The class
# names keep their sh- prefix because the styles were written when this
# panel lived on Start Here; renaming them would touch three hundred lines
# of CSS for no visible change.
SKY_TITLE = "What is worth looking at"
SKY_LEDE = ("Drop a pin where you will be observing from, whether that is "
            "your garden, a balcony or somewhere you drive out to. This "
            "works out when it actually gets dark, what the moon is doing, "
            "and which objects climb high enough for long enough to be "
            "worth setting up for. Use the arrows to plan ahead.")

# Where the map opens before the reader has moved the pin or saved a
# location: Dubai city. The first drag or tap replaces it.
SKY_MAP_LAT = 25.2048
SKY_MAP_LNG = 55.2708

# Opens on the region rather than the city, so a reader elsewhere can find
# themselves without zooming out first. Two values because the same zoom
# covers about a third as much ground on a phone as on a laptop.
SKY_MAP_ZOOM = 5
SKY_MAP_ZOOM_NARROW = 4

SKY_MAP_HELP = ("Drag the pin, or tap anywhere on the map, to set your "
                "location. Nothing is sent anywhere.")

# The place name under the coordinates is worked out in the browser from a
# table of towns that ships with the site, so no coordinates leave the page.
SKY_PLACES_SRC = "/assets/data/places.js"

# Leaflet from unpkg, with subresource integrity hashes from the published
# 1.9.4 package. OpenStreetMap tiles, so no API key and no billing account.
LEAFLET_VERSION = "1.9.4"
LEAFLET_CSS_SRI = "sha384-sHL9NAb7lN7rfvG5lfHpm643Xkcjzp4jFvuavGOndn6pjVqS6ny56CAt3nsEVT4H"
LEAFLET_JS_SRI = "sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH"

# Worded as what the reader can see rather than as a Bortle class, because
# someone who has never heard of Bortle can still answer "can I see the
# Milky Way from here". The number is what the engine uses.
SKY_BORTLE_Q = "How dark is your night sky?"
SKY_BORTLE_DEFAULT = 5
SKY_BORTLE_SCALE = [
    (1, "1: Pristine. The Milky Way casts a shadow", "Pristine"),
    (2, "2: Truly dark. Milky Way full of detail", "Truly dark"),
    (3, "3: Rural. Milky Way clear, slight glow low down", "Rural"),
    (4, "4: Edge of town. Milky Way washed out low down", "Edge of town"),
    (5, "5: Suburban. Milky Way faint overhead at best", "Suburban"),
    (6, "6: Bright suburb. No Milky Way, sky looks grey", "Bright suburb"),
    (7, "7: Town. Only the brighter stars, sky glows all round", "Town"),
    (8, "8: City. Brightest stars and planets only", "City"),
    (9, "9: Inner city. A handful of stars at most", "Inner city"),
]

# Under the picker, for the reader who cannot answer the question yet.
SKY_BORTLE_HELP = ("Not sure? Count the stars you can see in one patch of "
                   "sky on a clear night, and "
                   "{article:bortle-scale-narrowband-filters|the Bortle "
                   "scale article} tells you what that count means.")

SKY_TIPS = {
    "dark": ("The stretch when the sun is more than 18 degrees below the "
             "horizon, so the sky is as dark as it is going to get. "
             "Twilight either side of it is still too bright for faint "
             "objects, which is why this is shorter than the time "
             "between sunset and sunrise."),
    "moon": ("How much of the moon is lit, and when it is above your "
             "horizon. A bright moon washes out faint objects much the "
             "way a city does, so what matters is not only the phase but "
             "whether it is up while the thing you want is up."),
    "sky": ("How bright your own sky is, from the picker above. It "
            "decides which objects are realistic from where you are, and "
            "it has more effect on what you can capture than any other "
            "single thing."),
    "window": ("The stretch when this object sits more than 30 degrees "
               "above the horizon and the sky is properly dark. Below "
               "that you are shooting through more atmosphere, so stars "
               "bloat and haze near the horizon softens the detail. Aim "
               "for this window rather than the whole time the object is "
               "up."),
}

SKY_FALLBACK = ("Working out tonight's sky. If nothing appears here, "
                "JavaScript is switched off in your browser.")

SKY_FOOT = ("Times use your device clock. Tap a thumbnail to see the full "
            "picture, or the name to open its gallery page. Filter and kit "
            "suggestions are a starting point, not a rule.")


# -------------------------------------------------------------- 2. SHOWERS

SHOWERS_TITLE = "Meteor showers coming up"
SHOWERS_LEDE = ("A meteor shower works with a phone on a tripod as well as "
                "with a camera. The moon matters more than anything else on "
                "the night, so each one below says how much of it is lit on "
                "the peak night.")

# How many upcoming peaks to show. The rest of the year is in the article.
SHOWERS_SHOWN = 3

# Same table as the meteor shower article. Month and first night of the
# peak are what the script counts down to; the label is what the reader
# sees. Rates are what a patient person sees by eye at a dark site.
SHOWERS = [
    ("Quadrantids", 1, 3, "3 to 4 January", "25 to 50",
     "The peak is very short, often only a few hours."),
    ("Lyrids", 4, 22, "22 to 23 April", "10 to 20",
     "Modest, but it breaks the long gap between January and August."),
    ("Eta Aquariids", 5, 5, "5 to 6 May", "20 to 40",
     "Dust from Halley's Comet. Best in the hours before dawn."),
    ("Perseids", 8, 12, "12 to 13 August", "50 to 80",
     "Warm nights and a high radiant make this the easiest one to sit "
     "through."),
    ("Orionids", 10, 21, "21 to 22 October", "10 to 20",
     "Halley's Comet again, from the other side of its orbit."),
    ("Leonids", 11, 17, "17 to 18 November", "10 to 15",
     "Quiet most years, with occasional storms decades apart."),
    ("Geminids", 12, 13, "13 to 14 December", "60 to 100",
     "The best of the year. Bright, slow, and from an asteroid rather "
     "than a comet."),
    ("Ursids", 12, 22, "22 to 23 December", "5 to 10",
     "Small, and easy to combine with the Geminids the week before."),
]

SHOWERS_MORE = ("{article:photograph-a-meteor-shower|Photograph a meteor "
                "shower} covers where to point, how many frames to take, "
                "and the settings for a phone or a camera.")


# ----------------------------------------------------------------- 3. NEXT

NEXT_TITLE = "Planning the session itself"
NEXT_TEXT = ("This page gives you a shortlist for the night. Before every "
             "session I open Stellarium to do the rest: it shows exactly "
             "when a target clears the buildings, and draws my own "
             "telescope and camera onto the sky so I know what will fit. "
             "{article:how-i-plan-every-astrophotography-session-using-"
             "stellarium|How I plan every session with Stellarium} covers "
             "the routine, starting with the free web version.")

# Carries inline markup, so this one is not escaped.
NEWCOMER = ('New to this? <a href="/start-here.html">Start Here</a> has four '
            'things to try on the next clear night, with no equipment at '
            'all.')


# ------------------------------------------------------------------ build

class BuildError(Exception):
    """A missing slug or image is worth failing the build for."""


def load_data():
    with open(DATA, "r", encoding="utf-8") as f:
        items = json.load(f)
    articles, gallery = {}, {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("slug")
        if not slug or entry.get("hidden"):
            continue
        if entry.get("section") == "article":
            articles[slug] = entry
        elif entry.get("section") == "gallery":
            gallery[slug] = entry
    return articles, gallery


def tokens(text, articles):
    """Expand {article:}, {url:} and {ext:} inside escaped copy. A brace
    that is not a known token is left alone."""
    out = ""
    rest = esc(text)
    while "{" in rest:
        before, brace, after = rest.partition("{")
        kind, colon, tail = after.partition(":")
        if kind not in ("article", "url", "ext") or not colon or "}" not in tail:
            out += before + brace
            rest = after
            continue
        body, _, rest = tail.partition("}")
        target, _, label = body.partition("|")
        label = label or target
        out += before
        if kind == "article":
            if target not in articles:
                raise BuildError(f"unknown article slug '{target}' in copy")
            out += f'<a href="/{ARTICLE_DIR}/{esc(target)}.html">{label}</a>'
        elif kind == "ext":
            out += (f'<a href="{target}" target="_blank" '
                    f'rel="noopener noreferrer">{label}</a>')
        else:
            href = target if target.startswith("/") else "/" + target
            out += f'<a href="{href}">{label}</a>'
    return out + rest


def build_sky(articles):
    """The planner shell. /tonight-core.js fills #shSkyOut in."""
    opts = "".join(
        f'<option value="{n}" data-short="{esc(short)}"'
        f'{" selected" if n == SKY_BORTLE_DEFAULT else ""}>'
        f'{esc(label)}</option>'
        for n, label, short in SKY_BORTLE_SCALE
    )
    tips = " ".join(f'data-tip-{k}="{esc(v)}"' for k, v in SKY_TIPS.items())

    return (
        f'      <section class="sh-sky" id="shSky" {tips}>\n'
        f'        <h2>{esc(SKY_TITLE)}</h2>\n'
        f'        <p class="sh-sky-lede">{esc(SKY_LEDE)}</p>\n'

        '        <div class="sh-sky-map" id="shSkyMap" '
        f'data-lat="{SKY_MAP_LAT}" data-lng="{SKY_MAP_LNG}" '
        f'data-zoom="{SKY_MAP_ZOOM}" data-zoom-narrow="{SKY_MAP_ZOOM_NARROW}" '
        f'data-places="{SKY_PLACES_SRC}" role="application" '
        'aria-label="Map for choosing your observing location"></div>\n'

        '        <div class="sh-sky-loc">\n'
        '          <p class="sh-sky-coords" id="shSkyCoords"></p>\n'
        '          <button type="button" class="btn sh-sky-geo" id="shSkyGeo">'
        'Use my location</button>\n'
        '        </div>\n'
        '        <p class="sh-sky-place" id="shSkyPlace" hidden></p>\n'
        f'        <p class="sh-sky-map-help">{esc(SKY_MAP_HELP)}</p>\n'

        '        <div class="sh-sky-bortle">\n'
        f'          <label for="shSkyBortle">{esc(SKY_BORTLE_Q)}</label>\n'
        f'          <select id="shSkyBortle">{opts}</select>\n'
        '        </div>\n'
        f'        <p class="sh-sky-bortle-help">{tokens(SKY_BORTLE_HELP, articles)}</p>\n'

        '        <div class="sh-sky-datenav">\n'
        '          <button type="button" class="btn sh-sky-nav" id="shSkyPrev" '
        'aria-label="Previous night">&#8592;</button>\n'
        '          <span class="sh-sky-datewrap">\n'
        '            <button type="button" class="sh-sky-datebtn" id="shSkyDate" '
        'aria-label="Choose a date">Tonight</button>\n'
        '            <input type="date" id="shSkyDatePick" class="sh-sky-dateinput" '
        'aria-label="Choose a date" />\n'
        '          </span>\n'
        '          <button type="button" class="btn sh-sky-nav" id="shSkyNext" '
        'aria-label="Next night">&#8594;</button>\n'
        '          <button type="button" class="btn sh-sky-today" id="shSkyToday" '
        'hidden>Tonight</button>\n'
        '        </div>\n'

        '        <div class="sh-sky-out" id="shSkyOut" aria-live="polite">\n'
        f'          <p class="sh-sky-wait">{esc(SKY_FALLBACK)}</p>\n'
        '        </div>\n'
        f'        <p class="sh-sky-foot">{esc(SKY_FOOT)}</p>\n'
        '      </section>\n'
    )


def build_showers(articles):
    """Every shower in calendar order, as plain HTML.

    That is what a reader without JavaScript and a crawler both get. The
    script then replaces the list with the next few peaks counted from
    today, with the moon for each peak night and a button that moves the
    planner to it.
    """
    data = [{"n": n, "m": m, "d": d, "p": peak, "r": rate, "w": note}
            for n, m, d, peak, rate, note in SHOWERS]
    rows = "".join(
        '          <li class="tn-shower">\n'
        '            <div class="tn-shower-main">\n'
        f'              <p class="tn-shower-name">{esc(n)}</p>\n'
        f'              <p class="tn-shower-meta">Peak {esc(peak)}. About '
        f'{esc(rate)} an hour at a dark site.</p>\n'
        f'              <p class="tn-shower-note">{esc(note)}</p>\n'
        '            </div>\n'
        '          </li>\n'
        for n, m, d, peak, rate, note in SHOWERS
    )
    return (
        '      <section class="tn-showers" id="tnShowers" '
        f'data-shown="{SHOWERS_SHOWN}" data-showers="{esc(json.dumps(data))}">\n'
        f'        <h2>{esc(SHOWERS_TITLE)}</h2>\n'
        f'        <p class="tn-lede">{esc(SHOWERS_LEDE)}</p>\n'
        '        <ol class="tn-shower-list" id="tnShowerList">\n'
        f'{rows}'
        '        </ol>\n'
        f'        <p class="tn-more">{tokens(SHOWERS_MORE, articles)}</p>\n'
        '      </section>\n'
    )


def build_next(articles):
    return (
        '      <section class="tn-next">\n'
        f'        <h2>{esc(NEXT_TITLE)}</h2>\n'
        f'        <p>{tokens(NEXT_TEXT, articles)}</p>\n'
        '      </section>\n'
    )


SHOWERS_SCRIPT = """
/* ── Meteor showers ─────────────────────────────────────────────────
   Replaces the static calendar list with the next few peaks counted
   from today. The moon figure comes from /tonight-core.js, so it is the
   same number the planner shows for that night. */
(function () {
  var box  = document.getElementById('tnShowers');
  var list = document.getElementById('tnShowerList');
  var C    = window.TonightCore;
  if (!box || !list) return;

  var data;
  try { data = JSON.parse(box.getAttribute('data-showers') || '[]'); }
  catch (e) { return; }
  if (!data.length) return;

  var shown = parseInt(box.getAttribute('data-shown'), 10) || 3;

  var today = new Date();
  today.setHours(0, 0, 0, 0);

  /* The peak night as a local evening. Late evening rather than midnight,
     so the date the reader sees is the night they would go out. */
  function nightOf(year, s) {
    return new Date(year, s.m - 1, s.d, 23, 0, 0, 0);
  }

  var next = data.map(function (s) {
    var night = nightOf(today.getFullYear(), s);
    var day = new Date(night.getFullYear(), night.getMonth(), night.getDate());
    if (day < today) night = nightOf(today.getFullYear() + 1, s);
    return { s: s, night: night };
  }).sort(function (a, b) { return a.night - b.night; }).slice(0, shown);

  function esc(v) {
    return String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function whenText(night) {
    var day = new Date(night.getFullYear(), night.getMonth(), night.getDate());
    var n = Math.round((day - today) / 86400000);
    if (n === 0) return 'Peaks tonight';
    if (n === 1) return 'Peaks tomorrow night';
    return 'In ' + n + ' days';
  }

  function moonText(night) {
    if (!C || !C.moonIllumination) return '';
    var pct = Math.round(C.moonIllumination(night).fraction * 100);
    if (pct < 30) return 'Moon ' + pct + '% lit on the peak night, so a dark sky for it.';
    return 'Moon ' + pct + '% lit on the peak night. See this night for when it is up.';
  }

  list.innerHTML = next.map(function (item, i) {
    var s = item.s;
    return '<li class="tn-shower' + (i === 0 ? ' is-next' : '') + '">' +
      '<div class="tn-shower-main">' +
        '<p class="tn-shower-name">' + esc(s.n) +
          '<span class="tn-shower-when">' + whenText(item.night) + '</span></p>' +
        '<p class="tn-shower-meta">Peak ' + esc(s.p) + '. About ' + esc(s.r) +
          ' an hour at a dark site.</p>' +
        '<p class="tn-shower-note">' + esc(s.w) + '</p>' +
        '<p class="tn-shower-moon">' + moonText(item.night) + '</p>' +
      '</div>' +
      '<button type="button" class="btn tn-shower-go" data-i="' + i + '">' +
        'See this night</button>' +
    '</li>';
  }).join('');

  list.addEventListener('click', function (ev) {
    var btn = ev.target.closest && ev.target.closest('.tn-shower-go');
    if (!btn) return;
    var item = next[parseInt(btn.getAttribute('data-i'), 10)];
    if (!item) return;
    document.dispatchEvent(new CustomEvent('tonight:goto',
                                           { detail: { date: item.night } }));
  });
})();
"""

SKY_SCRIPT = """
/* ── Sky panel ──────────────────────────────────────────────────────
   Fills the shell from build_sky() using /tonight-core.js. Holds no
   astronomy itself, so this and the engine cannot drift apart.

   The map is an upgrade, not a requirement. If Leaflet fails to load,
   or tiles are blocked, everything below it still works from the last
   saved coordinates. */
(function () {
  var sky = document.getElementById('shSky');
  var out = document.getElementById('shSkyOut');
  var C   = window.TonightCore;
  if (!sky || !out || !C) return;

  var SHOWN  = 5;
  var MIN_ALT = 30;   // degrees. Below this, stars bloat and detail drops.

  var mapEl  = document.getElementById('shSkyMap');
  var coords = document.getElementById('shSkyCoords');
  var placeEl = document.getElementById('shSkyPlace');
  var geo    = document.getElementById('shSkyGeo');
  var bortle = document.getElementById('shSkyBortle');

  var state = {
    lat: parseFloat(mapEl.dataset.lat),
    lng: parseFloat(mapEl.dataset.lng),
    bortle: parseInt(bortle.value, 10),
    offset: 0,
    expanded: false
  };

  try {
    var saved = JSON.parse(localStorage.getItem('tonight.loc') || 'null');
    if (saved && typeof saved.lat === 'number') {
      state.lat = saved.lat;
      state.lng = saved.lng;
      if (saved.bortle) { state.bortle = saved.bortle; bortle.value = saved.bortle; }
    }
  } catch (e) {}

  function save() {
    try {
      localStorage.setItem('tonight.loc', JSON.stringify({
        lat: state.lat, lng: state.lng, bortle: state.bortle
      }));
    } catch (e) {}
  }

  function hhmm(d) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  }
  /* Target names carry entities such as &amp;, so anything going into an
     attribute is escaped rather than dropped in raw. */
  function attr(v) {
    return String(v).replace(/&(?!(amp|lt|gt|quot|#\\d+);)/g, '&amp;')
                    .replace(/"/g, '&quot;');
  }

  function hoursText(h) {
    var w = Math.floor(h), m = Math.round((h - w) * 60);
    if (m === 60) { w++; m = 0; }
    return w === 0 ? m + ' min' : w + 'h' + (m ? ' ' + m + 'm' : '');
  }

  /* ── Map ─────────────────────────────────────────────
     Leaflet with OpenStreetMap tiles. No API key, so
     nothing sensitive sits in the page source. */
  var marker = null, map = null;

  /* ── Where am I, roughly ──────────────────────────────
     A pair of decimals tells you nothing about where you have put the
     pin, so the nearest town goes underneath it. The table that answers
     that is a hundred kilobytes, which is not worth loading for a reader
     who never scrolls this far, so it is fetched on first use and the
     line stays hidden until it arrives. No coordinates go anywhere. */
  var placeTimer = null, placeAsked = false;

  function regionName(cc) {
    try {
      var dn = new Intl.DisplayNames([document.documentElement.lang || 'en'],
                                     { type: 'region' });
      return dn.of(cc) || cc;
    } catch (e) { return cc; }
  }

  function paintPlace() {
    if (!placeEl || !window.NearestPlace) return;
    var hit = window.NearestPlace.find(state.lat, state.lng);
    if (!hit) { placeEl.hidden = true; placeEl.textContent = ''; return; }
    var where = hit.name + ', ' + regionName(hit.country);
    placeEl.textContent = hit.km < 25
      ? where
      : 'Near ' + where + ', about ' + Math.round(hit.km) + ' km away';
    placeEl.hidden = false;
  }

  /* Debounced, because dragging the pin fires this continuously and the
     answer only matters once the reader has let go. */
  function wantPlace() {
    if (!placeEl) return;
    clearTimeout(placeTimer);
    placeTimer = setTimeout(function () {
      if (window.NearestPlace) { paintPlace(); return; }
      if (placeAsked) return;
      placeAsked = true;
      var src = (mapEl && mapEl.dataset.places) || '';
      if (!src) return;
      var sc = document.createElement('script');
      sc.src = src;
      sc.async = true;
      sc.onload = paintPlace;
      document.head.appendChild(sc);
    }, 250);
  }

  function showCoords() {
    coords.textContent = state.lat.toFixed(4) + ', ' + state.lng.toFixed(4);
    wantPlace();
  }

  /* The opening view is deliberately wide, so a reader anywhere can see
     enough of the world to find themselves. A phone shows about a third
     of the ground a laptop does at the same zoom, hence two numbers. */
  function openZoom() {
    var wide = parseInt(mapEl.dataset.zoom, 10) || 5;
    var narrow = parseInt(mapEl.dataset.zoomNarrow, 10) || wide;
    return (mapEl.clientWidth && mapEl.clientWidth < 520) ? narrow : wide;
  }

  function moveTo(lat, lng, zoomTo) {
    state.lat = lat; state.lng = lng;
    showCoords();
    if (marker) marker.setLatLng([lat, lng]);
    if (map && zoomTo) map.setView([lat, lng], Math.max(map.getZoom(), zoomTo));
    save();
    render();
  }

  if (window.L && mapEl) {
    /* Wheel zoom is on because zooming by button is clunky on desktop.
       The cost is that a wheel scroll starting over the map zooms instead
       of moving the page, which is why the map is not full width: there
       is always margin either side to scroll past it. */
    map = L.map(mapEl, { scrollWheelZoom: true })
           .setView([state.lat, state.lng], openZoom());

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    marker = L.marker([state.lat, state.lng], { draggable: true }).addTo(map);
    marker.on('dragend', function () {
      var p = marker.getLatLng();
      moveTo(p.lat, p.lng, false);
    });
    map.on('click', function (ev) {
      moveTo(ev.latlng.lat, ev.latlng.lng, false);
    });
  } else if (mapEl) {
    mapEl.classList.add('is-off');
  }

  /* ── Rendering ───────────────────────────────────── */
  /* The "i" buttons. Copy comes from data attributes on #shSky so it
     stays in the generator rather than in this script string. */
  var TIPS = {
    dark:   sky.dataset.tipDark   || '',
    moon:   sky.dataset.tipMoon   || '',
    sky:    sky.dataset.tipSky    || '',
    window: sky.dataset.tipWindow || ''
  };

  function info(key) {
    if (!TIPS[key]) return '';
    return '<button type="button" class="sh-sky-i sh-sky-tip" aria-label="What this means" ' +
           'data-tip="' + TIPS[key].replace(/"/g, '&quot;') + '">i</button>';
  }

  /* One open tip at a time, closed by a second tap or a click elsewhere.
     Hover alone would leave this unusable on a phone. */
  /* Both selectors, so this keeps working against markup from either
     side of the change that gave the chips their own tooltips. */
  var TRIGGER = '.sh-sky-tip, .sh-sky-i';
  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest && ev.target.closest(TRIGGER);
    var open = sky.querySelector('.sh-sky-tip.is-open, .sh-sky-i.is-open');
    if (open && open !== btn) open.classList.remove('is-open');
    if (btn) { ev.preventDefault(); btn.classList.toggle('is-open'); }
  });

  /* ── Summary box furniture ────────────────────────
     Small line drawings rather than emoji, so they take the text colour,
     follow both themes and stay the same shape on every platform. */
  function svg(body) {
    return '<svg class="sh-sky-ico" viewBox="0 0 18 18" aria-hidden="true" ' +
           'fill="none" stroke="currentColor" stroke-width="1.4" ' +
           'stroke-linecap="round" stroke-linejoin="round">' + body + '</svg>';
  }

  /* Sun below a horizon: the thing the box is actually about. */
  var ICON_DARK = svg('<path d="M1.5 12.5h15"/><circle cx="9" cy="15" r="3.2"/>' +
                      '<path d="M9 7.5v1.6M4 9l1.1 1.1M14 9l-1.1 1.1"/>');

  /* Rooftops with the glow coming off them. */
  var ICON_SKY = svg('<path d="M1.5 15.5h15"/>' +
                     '<path d="M3.5 15.5v-4h3v4M8.5 15.5V8h3.5v7.5M13.5 15.5v-5.5h2.5v5.5"/>' +
                     '<path d="M2.6 5.2v1.4M5.6 3.4v1.4M9 2v1.6M12.4 3.4v1.4M15.4 5.2v1.4"/>');

  /* The moon drawn at tonight's actual phase. The lit edge is a circle
     and the terminator is an ellipse whose width is what the phase is:
     flat at a quarter, bulging one way for a crescent and the other for
     a gibbous. Mirrored for the waning half of the month. */
  function moonIcon(frac, phase) {
    var lit;
    if (frac <= 0.01) {
      lit = '';
    } else if (frac >= 0.99) {
      lit = '<circle cx="9" cy="9" r="7" fill="currentColor" stroke="none"/>';
    } else {
      var rx = (7 * Math.abs(1 - 2 * frac)).toFixed(2);
      var sweep = frac < 0.5 ? 0 : 1;
      var d = 'M9 2 A7 7 0 0 1 9 16 A' + rx + ' 7 0 0 ' + sweep + ' 9 2 Z';
      lit = '<path d="' + d + '" fill="currentColor" stroke="none"' +
            (phase < 0.5 ? '' : ' transform="rotate(180 9 9)"') + '/>';
    }
    return '<svg class="sh-sky-ico" viewBox="0 0 18 18" aria-hidden="true">' +
             '<circle cx="9" cy="9" r="7" fill="none" stroke="currentColor" ' +
               'stroke-width="1.4" stroke-opacity="0.45"/>' + lit +
           '</svg>';
  }

  function fact(icon, label, tip, value, sub) {
    return '<span>' +
             '<i>' + icon + label + info(tip) + '</i>' +
             '<b>' + value + '</b>' +
             (sub ? '<em>' + sub + '</em>' : '') +
           '</span>';
  }

  function reasonFor(r) {
    var bits = [];
    if (r.bf < 0.5) bits.push('Your sky is too bright for this one. It will be a struggle.');
    else if (r.bf < 0.85) bits.push('Light pollution will cost you contrast here.');
    if (r.moonLoad > 0.35) bits.push('The moon is up and bright through most of this window.');
    else if (r.moonLoad > 0.12) bits.push('Some moonlight to work around.');
    if (r.maxAlt < 35) bits.push('Stays low, so expect softer stars.');
    if (!bits.length) bits.push('Good conditions for this one tonight.');
    return bits.join(' ');
  }

  /* ── Thumbnail lightbox ───────────────────────────
     Reuses the .figbox styling that the article pages already carry, but
     wired here with a delegated listener, because the list is rebuilt from
     scratch on every date, location and sky change. */
  var lb = null, lbStage = null, lbCap = null;

  function lightbox(src, name) {
    if (!lb) {
      lb = document.createElement('div');
      lb.className = 'figbox';
      lb.id = 'shSkyFigbox';
      lb.hidden = true;
      lb.setAttribute('role', 'dialog');
      lb.setAttribute('aria-modal', 'true');
      lb.setAttribute('aria-label', 'Enlarged picture');
      lb.tabIndex = -1;

      var x = document.createElement('button');
      x.type = 'button';
      x.className = 'figbox-x';
      x.setAttribute('aria-label', 'Close');
      x.innerHTML = '&#215;';

      lbStage = document.createElement('div');
      lbStage.className = 'figbox-stage';

      lbCap = document.createElement('p');
      lbCap.className = 'figbox-cap';

      var hint = document.createElement('p');
      hint.className = 'figbox-hint';
      hint.textContent = 'Click anywhere to close';

      lb.appendChild(x);
      lb.appendChild(lbStage);
      lb.appendChild(lbCap);
      lb.appendChild(hint);
      document.body.appendChild(lb);

      lb.addEventListener('click', closeLightbox);
      lb.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape' || ev.key === 'Esc') { ev.preventDefault(); closeLightbox(); }
      });
    }

    lbStage.innerHTML = '';
    var img = document.createElement('img');
    img.src = src;
    img.alt = '';
    img.decoding = 'async';
    lbStage.appendChild(img);
    lbCap.innerHTML = name;

    lb.hidden = false;
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { lb.classList.add('open'); });
    });
    document.documentElement.style.overflow = 'hidden';
    lb.focus();
  }

  function closeLightbox() {
    if (!lb) return;
    lb.classList.remove('open');
    document.documentElement.style.overflow = '';
    setTimeout(function () { lb.hidden = true; lbStage.innerHTML = ''; }, 200);
  }

  out.addEventListener('click', function (ev) {
    var btn = ev.target.closest && ev.target.closest('.sh-sky-thumb');
    if (!btn || !btn.dataset.full) return;
    ev.preventDefault();
    lightbox(btn.dataset.full, btn.dataset.name || '');
  });

  /* ── Which night ─────────────────────────────────── */
  function dateFor(offset) {
    var d = new Date();
    d.setHours(12, 0, 0, 0);
    d.setDate(d.getDate() + offset);
    return d;
  }
  function isoOf(d) {
    return d.getFullYear() + '-' +
           String(d.getMonth() + 1).padStart(2, '0') + '-' +
           String(d.getDate()).padStart(2, '0');
  }

  function render() {
    var date = dateFor(state.offset);
    var label = document.getElementById('shSkyDate');
    var pick  = document.getElementById('shSkyDatePick');
    var today = document.getElementById('shSkyToday');

    label.textContent = state.offset === 0
      ? 'Tonight'
      : date.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
    if (pick) pick.value = isoOf(date);
    if (today) today.hidden = state.offset === 0;

    var plan = C.planNight(date, state.lat, state.lng, state.bortle, MIN_ALT);

    if (!plan.dark) {
      out.innerHTML = '<p class="sh-sky-wait">The sun never drops far enough ' +
        'below the horizon on this date at this latitude, so there is no ' +
        'properly dark window.</p>';
      return;
    }

    var moonPct = Math.round(plan.moonIll * 100);

    /* Each box says what it is before it says the number, and carries a
       second line that answers the question the number raises. The four
       bare figures this replaced needed the tips read before any of them
       meant anything. */
    var moonWhen;
    if (!plan.moonUpFrom) moonWhen = 'Down all night';
    else if (plan.moonUpFrac > 0.98) moonWhen = 'Up the whole night';
    else moonWhen = 'Up ' + hhmm(plan.moonUpFrom) + ' to ' + hhmm(plan.moonUpTo);

    var chosen = bortle.options[bortle.selectedIndex];
    var skyShort = (chosen && chosen.dataset.short) || '';

    var html =
      '<div class="sh-sky-facts">' +
        fact(ICON_DARK, 'Sky is properly dark', 'dark',
             hhmm(plan.darkStart) + ' to ' + hhmm(plan.darkEnd),
             hoursText((plan.darkEnd - plan.darkStart) / 3600000) + ' to work with') +
        fact(moonIcon(plan.moonIll, plan.moonPhase), 'Moon', 'moon',
             moonPct + '% lit',
             C.moonPhaseName(plan.moonPhase) + '. ' + moonWhen) +
        fact(ICON_SKY, 'Your sky', 'sky',
             'Bortle ' + state.bortle,
             skyShort) +
      '</div>';

    if (!plan.targets.length) {
      html += '<p class="sh-sky-wait">Nothing gets high enough for long enough ' +
              'tonight from here. Step forward a few nights and try again.</p>';
      out.innerHTML = html;
      wireMore();
      return;
    }

    var list = state.expanded ? plan.targets : plan.targets.slice(0, SHOWN);
    html += '<ol class="sh-sky-list">' + list.map(function (r) {
      var tg = r.tg;

      /* The thumbnail is a button, not a link. It opens the full picture
         over the page; the name beside it is the link to the gallery. Two
         different jobs, so two different controls. */
      var thumb = tg.f
        ? '<button type="button" class="sh-sky-thumb" ' +
            'data-full="/' + tg.f + '" data-name="' + attr(tg.n) + '" ' +
            'aria-label="See ' + attr(tg.n) + ' full size">' +
            '<img src="/' + C.thumbFor(tg) + '" alt="" loading="lazy" decoding="async" />' +
          '</button>'
        : '<span class="sh-sky-thumb is-empty" aria-hidden="true"></span>';

      var fk = C.filterFor(tg, state.bortle, r.moonLoad);
      var fl = C.FILTERS[fk];
      var filterChip =
        '<button type="button" class="sh-sky-chip sh-sky-chip-' + fk + ' sh-sky-tip" ' +
          'data-tip="' + attr(fl.w) + '" ' +
          'aria-label="' + attr(fl.l + '. Tap for why') + '">' +
          '<span class="sh-sky-chip-k">Filter</span>' + fl.s +
        '</button>';

      /* Every chip says why it looks the way it does, which is more use
         than one note at the end of the row explaining the colours in
         the abstract. A grey chip is the one a reader most wants an
         answer for, so it gets the most specific answer: whether the
         object is simply out of reach for that kit, or whether their
         own sky is what took it away. */
      var levels = C.kitFor(tg, state.bortle);
      var kitChips = C.KIT.map(function (slot, i) {
        var lvl = levels[i] || 0;
        var best = (tg.k && tg.k[i]) || 0;
        var ceiling = (tg.b && tg.b[i]);
        var why;

        if (!best) {
          why = slot.l + ': not worth trying. This one is too faint or too ' +
                'small for it under any sky.';
        } else if (lvl === 0) {
          why = slot.l + ': not worth trying from a Bortle ' + state.bortle +
                ' sky. It holds up to about Bortle ' + ceiling +
                ', so this needs a darker site rather than more patience.';
        } else if (lvl === 1 && state.bortle === ceiling) {
          why = slot.l + ': works, but Bortle ' + ceiling + ' is as bright as ' +
                'it takes. Expect a fight for contrast.';
        } else if (lvl === 1) {
          why = slot.l + ': works. Not where this one looks its best, but ' +
                'you will get something worth keeping.';
        } else {
          why = slot.l + ': this is where the object looks its best.';
        }

        return '<button type="button" class="sh-sky-kit-chip lvl-' + lvl +
               ' sh-sky-tip" data-tip="' + attr(why) + '" ' +
               'aria-label="' + attr(why) + '">' + slot.s + '</button>';
      }).join('');

      return '<li>' +
        '<div class="sh-sky-main">' +
          thumb +
          '<p class="sh-sky-head">' +
            '<a class="sh-sky-name" href="/share/' + tg.slug + '.html">' + tg.n + '</a>' +
            '<button type="button" class="sh-sky-tag sh-sky-tag-' + tg.t +
              ' sh-sky-tip" data-tip="' + attr(C.TYPETIP[tg.t] || '') + '" ' +
              'aria-label="' + attr(C.LABEL[tg.t] + '. Tap for what this means') + '">' +
              C.LABEL[tg.t] + '</button>' +
          '</p>' +
          '<p class="sh-sky-desc">' + tg.d + '</p>' +
          '<p class="sh-sky-why">' + reasonFor(r) + '</p>' +
          '<p class="sh-sky-gear">' +
            filterChip +
            '<span class="sh-sky-kit">' +
              '<span class="sh-sky-chip-k">Use</span>' + kitChips +
            '</span>' +
          '</p>' +
        '</div>' +
        '<div class="sh-sky-timing">' +
          '<span><b>' + hhmm(r.winStart) + ' to ' + hhmm(r.winEnd) + '</b>' +
            '<i>Worth shooting' + info('window') + '</i></span>' +
          '<span><b>' + hoursText(r.hours) + '</b>' +
            '<i>Above ' + MIN_ALT + '\\u00B0 in total</i></span>' +
          '<span><b>' + Math.round(r.maxAlt) + '\\u00B0</b><i>Highest it gets</i></span>' +
          '<span><b>' + (r.moonUpFrac < 0.02 ? 'Down' : moonPct + '% up') + '</b>' +
            '<i>Moon in that window</i></span>' +
        '</div>' +
      '</li>';
    }).join('') + '</ol>';

    if (plan.targets.length > SHOWN) {
      html += '<button type="button" class="btn sh-sky-toggle" id="shSkyMore">' +
        (state.expanded ? 'Show fewer' : 'Show all ' + plan.targets.length) + '</button>';
    }

    out.innerHTML = html;
    wireMore();
  }

  function wireMore() {
    var more = document.getElementById('shSkyMore');
    if (more) more.addEventListener('click', function () {
      state.expanded = !state.expanded;
      render();
    });
  }

  /* ── Controls ────────────────────────────────────── */
  if (geo) geo.addEventListener('click', function () {
    if (!navigator.geolocation) return;
    geo.textContent = 'Locating\u2026';
    navigator.geolocation.getCurrentPosition(function (pos) {
      geo.textContent = 'Use my location';
      /* The wide opening view exists so a reader can find themselves. If
         the browser has just told us exactly where they are, that job is
         done, so close in on it. */
      moveTo(pos.coords.latitude, pos.coords.longitude, 10);
    }, function () {
      geo.textContent = 'Use my location';
    }, { timeout: 10000 });
  });

  bortle.addEventListener('change', function () {
    state.bortle = parseInt(this.value, 10);
    save(); render();
  });

  document.getElementById('shSkyPrev').addEventListener('click', function () {
    state.offset--; render();
  });
  document.getElementById('shSkyNext').addEventListener('click', function () {
    state.offset++; render();
  });

  /* The label opens the native date picker. showPicker() is the reliable
     way to do that from a button; where it is missing, or refuses because
     the gesture was not direct enough, focusing the input still gives the
     reader a working control. */
  (function () {
    var label = document.getElementById('shSkyDate');
    var pick  = document.getElementById('shSkyDatePick');
    var today = document.getElementById('shSkyToday');
    if (!label || !pick) return;

    label.addEventListener('click', function () {
      try {
        if (typeof pick.showPicker === 'function') { pick.showPicker(); return; }
      } catch (e) {}
      pick.focus();
      pick.click();
    });

    pick.addEventListener('change', function () {
      if (!pick.value) return;
      var parts = pick.value.split('-');
      var chosen = new Date(+parts[0], +parts[1] - 1, +parts[2], 12, 0, 0, 0);
      var base = new Date(); base.setHours(12, 0, 0, 0);
      state.offset = Math.round((chosen - base) / 86400000);
      render();
    });

    if (today) today.addEventListener('click', function () {
      state.offset = 0; render();
    });
  })();

  /* Other parts of the page, such as the meteor shower list, can move
     the planner to a given night by firing a tonight:goto event with a
     Date in its detail. They never reach into this script's state. */
  document.addEventListener('tonight:goto', function (ev) {
    var when = ev.detail && ev.detail.date;
    if (!(when instanceof Date)) return;
    var chosen = new Date(when.getFullYear(), when.getMonth(), when.getDate(), 12, 0, 0, 0);
    var base = new Date(); base.setHours(12, 0, 0, 0);
    state.offset = Math.round((chosen - base) / 86400000);
    state.expanded = false;
    render();
    var still = false;
    try {
      still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (e) {}
    sky.scrollIntoView({ behavior: still ? 'auto' : 'smooth', block: 'start' });
  });

  showCoords();
  render();
})();
"""


def build_page(articles):
    page_url = f"{DOMAIN}/{OUT}"
    share_url = f"{DOMAIN}/{SHARE_IMAGE}"
    return f'''<!doctype html>
<!-- Generated by scripts/generate-tonight.py. Do not edit this file by
     hand. Every build overwrites it. Edit the copy constants in that script instead. -->
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
  <meta property="og:image" content="{esc(share_url)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta name="twitter:description" content="{esc(PAGE_DESC)}" />
  <meta name="twitter:image" content="{esc(share_url)}" />
  <link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>
  <link rel="stylesheet" href="/styles.css" />

  <link rel="stylesheet" href="https://unpkg.com/leaflet@{LEAFLET_VERSION}/dist/leaflet.css" integrity="{LEAFLET_CSS_SRI}" crossorigin="" />
  <!-- Page CSS lives in /styles.css under "PAGE: Tonight" and "PAGE: Start Here — sky panel". -->
</head>
<body class="page-tonight">

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
      </div>

{build_sky(articles)}
{build_showers(articles)}
{build_next(articles)}
      <p class="sh-veteran">{NEWCOMER}</p>

    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

  <script src="https://unpkg.com/leaflet@{LEAFLET_VERSION}/dist/leaflet.js" integrity="{LEAFLET_JS_SRI}" crossorigin=""></script>
  <script src="/tonight-core.js"></script>
  <script src="/partials/partials.js"></script>
  <script>{SKY_SCRIPT}{SHOWERS_SCRIPT}</script>
</body>
</html>
'''


def check_targets(gallery):
    """Every target in tonight-core.js must have its pictures on disk.

    The planner shows a thumbnail for each object, so a renamed or missing
    image would leave a broken picture with nothing to warn about it. This
    reads the target table straight out of the engine and checks the two
    files and the gallery slug behind each one. Returns every problem at
    once rather than one per run.
    """
    problems = []
    try:
        with open(TONIGHT_CORE, encoding="utf-8") as f:
            src = f.read()
    except OSError:
        return [f"{TONIGHT_CORE} could not be read"]

    entries = re.findall(r'slug:"([^"]+)"[^\n]*\n\s*f:"([^"]*)"', src)
    if not entries:
        return [f"no targets found in {TONIGHT_CORE}; has the table changed shape?"]

    slugs = set(gallery or ())
    for slug, image in entries:
        thumb = image.replace("images/", "images/thumbs/", 1)
        if not os.path.isfile(image):
            problems.append(f"target '{slug}': missing image {image}")
        if not os.path.isfile(thumb):
            problems.append(f"target '{slug}': missing thumbnail {thumb}")
        if slugs and slug not in slugs:
            problems.append(f"target '{slug}': no gallery entry with that slug")
    return problems


def main():
    try:
        articles, gallery = load_data()
        problems = check_targets(gallery)
        if problems:
            raise BuildError(
                "planner targets are out of step with the images on disk:\n  "
                + "\n  ".join(problems)
            )
        html = build_page(articles)
    except BuildError as exc:
        print(f"✗ {OUT}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ {OUT}  ({len(SHOWERS)} meteor showers, "
          f"next {SHOWERS_SHOWN} shown)")


if __name__ == "__main__":
    main()
