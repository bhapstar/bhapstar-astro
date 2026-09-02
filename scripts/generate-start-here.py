#!/usr/bin/env python3
"""
generate-start-here.py — bhapstar
-------------------------------------------------------------
Writes start-here.html: the page that has to convince a stranger this
hobby is within reach, and then give them one small thing to do.

    python generate-start-here.py

Why this page exists, and why it is not articles.html:

  articles.html is the shelf. Everything, newest first, which is what a
  returning reader wants. This page is for someone who has just found the
  site, probably owns a phone and nothing else, and has not yet decided
  whether any of this is for them.

  It is therefore not a reading list. It opens with something useful the
  reader can act on the same night, gives away something free before
  asking for anything, and only then offers a short route. The eighty-minute path still exists, at the bottom, collapsed,
  for the reader who is already sold.

The page has five parts:

  1. SKY      A live "what is worth looking at tonight" panel. Works out
              tonight's darkness window, the moon, and the three best
              targets for wherever the reader is. The astronomy lives in
              /tonight-core.js, shared with the full tonight.html page,
              so this page holds no maths of its own.

  2. TONIGHT  One thing to do on the next clear night with no equipment.
              Pure copy, edited in TONIGHT_STEPS below.

  3. ROUTES   Six curated routes of three articles each, chosen by where
              the reader is rather than by what they own.

  4. EXTRAS   Articles that belong to the calendar rather than to a route.
              Never filtered, and deliberately outside the staged path: a
              meteor shower is not step four of learning astrophotography,
              it is a date in December. Sits in a closed <details> so the
              page ends on two short lines rather than two full panels.

  5. FULL     Every staged article in order, inside a closed <details>.

Where the routes come from:

  ROUTES below, not site-data.json. This is deliberate. The same article
  is framed differently depending on who is reading it: the Bortle piece
  is "score your own sky" to a curious reader, "work out what your sky can
  do before you spend" to a buyer, and "what a rig will actually achieve
  here" to somebody pricing a mount. One "desc" field in site-data.json
  cannot do all three, so the route blurb lives with the route.

  Each card names a slug. The slug is looked up in site-data.json for its
  URL and read time, and a missing slug fails the build rather than
  silently dropping a card.

  The old "paths" field on article entries is no longer read. It can stay
  in site-data.json harmlessly, or be removed at leisure.

Where the full path comes from:

  Still the two optional fields on any article entry in site-data.json.

      "stage":      one of plan, capture, process, gear
      "stageOrder": an integer, low numbers first within that stage

  An article with no "stage" does not appear in the full path. That is the
  intended way to keep something off it without hiding it from the site:
  it still gets a page, still appears on articles.html, still goes in the
  feed. Nothing needs a "stageOrder"; entries without one fall to the end
  of their stage, newest first.

Tokens available in route ledes, endings and tonight steps:

      {route:key}            a button that switches to that route
      {article:slug|label}   a link to an article page
      {url:path|label}       a link to anything else on the site

The page is fully generated, so editing start-here.html by hand will be
overwritten on the next build. Change the copy below instead. Page CSS
lives in /styles.css under "PAGE: Start Here".
"""

import json
import sys
from datetime import datetime
from html import escape as esc

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT = "start-here.html"
ARTICLE_DIR = "articles"

PAGE_TITLE = "Start Here"
PAGE_DESC = ("The equipment matters less than the sky you point it at. Four "
             "galaxies taken with a telescope that fits in a shoulder bag, one "
             "thing to try tonight with nothing at all, and a short route "
             "through the rest depending on where you are.")

SUBTITLE = "The equipment matters less than the sky you point it at."

# No claim about cost here. The images directly below cost real money and
# real hours, and their captions say so, so a "costs nothing" line sitting
# on top of them reads as a bait however carefully it is qualified. That
# promise now lives in TONIGHT_LEDE, where it is the literal truth.
INTRO = ("This page is for anyone who has looked at a picture of a galaxy and "
         "wondered whether an ordinary person could take one. You can, and "
         "with less equipment than you would guess. The harder part is not the "
         "kit. It is getting under a sky dark enough to be worth the trouble, "
         "and that is the first thing this page will help you work out.")


# ------------------------------------------------------------------ 1. SKY

# The sky panel. The reader drops a pin where they will be observing from,
# says how bright their sky is, and gets tonight's darkness window, the
# moon, and every target from the gallery that is actually worth pointing
# at, ranked.
#
# All the astronomy lives in /tonight-core.js. This file emits the shell
# and the copy around it, and never calculates anything itself.
SKY_TITLE = "What is worth looking at tonight"
SKY_LEDE = ("Drop a pin where you will be observing from, whether that is "
            "your garden, a balcony or somewhere you drive out to. This "
            "works out when it actually gets dark tonight, what the moon is "
            "doing, and which objects climb high enough for long enough to "
            "be worth setting up for.")

# Where the map opens before the reader has moved the pin or saved a
# location. Dubai, because that is where most of the gallery was shot, but
# nothing on the page depends on it: the first drag replaces it.
SKY_MAP_LAT = 25.2048
SKY_MAP_LNG = 55.2708
SKY_MAP_ZOOM = 9

SKY_MAP_HELP = ("Drag the pin, or tap anywhere on the map, to set your "
                "location. Nothing is sent anywhere.")

# Leaflet from unpkg, with subresource integrity hashes taken from the
# published 1.9.4 package. OpenStreetMap tiles rather than Google, so no
# API key sits in the page source and there is no billing account behind
# it. If the tiles cannot load the rest of the panel still works, because
# the coordinates are all the astronomy needs.
LEAFLET_VERSION = "1.9.4"
LEAFLET_CSS_SRI = "sha384-sHL9NAb7lN7rfvG5lfHpm643Xkcjzp4jFvuavGOndn6pjVqS6ny56CAt3nsEVT4H"
LEAFLET_JS_SRI = "sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH"

# The Bortle number changes which targets are recommended, so a reader who
# does not know theirs will get bad advice without noticing. Checked
# against the real article list at build time.
SKY_BORTLE_ARTICLE = "bortle-scale-narrowband-filters"
SKY_BORTLE_LINK = "not sure which yours is?"

# Shown before the panel fills in, and permanently if JavaScript is off.
SKY_FALLBACK = ("Working out tonight's sky. If nothing appears here, "
                "JavaScript is switched off in your browser.")

SKY_FOOT = ("Times use your device clock. Tap any object to see one from "
            "the gallery.")


# Used for the social card, since this page now has something worth showing.
SHARE_IMAGE = "images/andromeda-galaxy-m31.webp"


# -------------------------------------------------------------- 2. TONIGHT

TONIGHT_TITLE = "Try this tonight, with nothing"
TONIGHT_LEDE = ("Before you read anything or buy anything, do these three "
                "things on the next clear night. They cost nothing at all, "
                "they take about half an hour, and they will tell you more "
                "about your sky than any article can.")

TONIGHT_STEPS = [
    ("Go outside and wait twenty minutes",
     "Your eyes need roughly twenty minutes in the dark before they work "
     "properly. Keep your phone screen off, or switch it to the dimmest red "
     "setting you have. Stars will keep appearing the whole time you wait."),
    ("Count what you can actually see",
     "Pick one patch of sky and count the stars in it. From the middle of "
     "Dubai you might get one or two. An hour into the Dubai desert you will "
     "see hundreds. Two and a half hours into the heart of the Abu Dhabi desert, "
     "you will lose count. That difference is the single "
     "biggest factor in what you will be able to photograph. If you want to "
     "know what those counted stars mean, "
     "{article:bortle-scale-narrowband-filters|the Bortle scale explains it}."),
    ("Take one photo with the phone in your pocket",
     "If you have a small phone tripod, now is the time to use it. Otherwise "
     "prop the phone against a wall or a bag so it cannot move. Use night "
     "mode, or set the shutter to ten seconds, and point it up. Most modern "
     "phones will record stars you could not see with your eyes."),
]

TONIGHT_OUT = ("That is the hobby in miniature: dark skies, patience, and a "
               "camera held still. Everything below is a way of doing more "
               "of it.")


# --------------------------------------------------------------- 3. ROUTES

ROUTE_PROMPT = "Where are you right now?"
ROUTE_HELP = ("Pick one of the buttons and read the articles on your choice, with a full list of articles available at the bottom of "
              "the page.")

GEAR_LINK = ('<a class="sh-more" href="/gear.html">Every piece of gear I use, '
             'with links to buy <span aria-hidden="true">&#8594;</span></a>')

# Order here is the order of the pills and of the blocks in the document,
# which runs from what you already have to what you are considering buying.
ROUTES = [
    {
        "key": "curious",
        "label": "Just curious",
        "heading": "Just curious",
        "lede": "You are not buying anything yet. Fair enough. These three "
                "will tell you whether the hobby suits you, and none of them "
                "assume you own a single piece of equipment.",
        "cards": [
            ("navigating-the-night-sky",
             "Navigating the Night Sky",
             "How to find Polaris, why the south has no north star, and what "
             "the celestial equator and the meridian actually are."),
            ("bortle-scale-narrowband-filters",
             "The Bortle Scale",
             "Why a city sky buries a nebula instead of dimming it, and how "
             "to score your own sky from one to nine tonight."),
            ("photograph-the-moon",
             "Photograph the Moon",
             "Bright enough for a city sky, up on half the nights of any "
             "month, and it needs no dark site and nothing that tracks."),
        ],
        "ending": "Twenty odd minutes of reading and one clear evening, and "
                  "you will have an answer, without going anywhere or buying "
                  "anything. On the few nights a month when the Moon is not "
                  "up, "
                  "{article:photograph-milky-way-phone|the phone route} is "
                  "what those nights are for. If it turns out you want more, "
                  "{route:buying} is the next question.",
    },
    {
        "key": "phone",
        "label": "I have a phone",
        "heading": "I have a phone",
        "lede": "A phone will get you the Milky Way arching over a horizon, "
                "and on a dark night it will get you more of it than you "
                "expect. Start here and spend nothing.",
        "cards": [
            ("photograph-milky-way-phone",
             "Photograph the Milky Way with Your Phone",
             "Where to look, which mode to use on an iPhone, Pixel or "
             "Samsung, and what to change if a meteor shower is on."),
            ("navigating-the-night-sky",
             "Navigating the Night Sky",
             "Knowing where things are, so you can point the phone at "
             "something on purpose rather than by accident."),
            ("how-i-plan-every-astrophotography-session-using-stellarium",
             "Planning with Stellarium",
             "Free software that tells you what is up tonight, how high it "
             "gets, and when it is highest."),
        ],
        "ending": "That is the whole phone path. What a phone will not get "
                  "you is deep sky: faint nebulae and galaxies need longer "
                  "exposures than a handset will give you. When you want "
                  "those, {route:buying} picks up where this one stops.",
    },
    {
        "key": "camera",
        "label": "I have a digital camera",
        "heading": "I have a digital camera",
        "lede": "A camera and one wide lens on a tripod will already get you "
                "the Milky Way. Add a way of tracking the sky and the same "
                "camera will reach nebulae and galaxies. This is the route "
                "with the most headroom and the steepest middle.",
        "cards": [
            ("photograph-milky-way-camera",
             "Photograph the Milky Way with a Camera",
             "One wide lens on a tripod, set to manual. The settings to use, "
             "and how long the shutter can stay open before stars trail."),
            ("imaging-from-a-city-balcony",
             "Imaging from a City Balcony",
             "Moving from the Milky Way to deep sky without leaving home, and "
             "how to work with a view of half the sky."),
            ("siril-post-processing-guide",
             "Finishing the Image in Siril",
             "Free software that turns a folder of near-black frames into a "
             "picture, and the one rule about stretching."),
        ],
        "ending": "Once you are stacking your own frames, the next thing "
                  "worth learning is "
                  "{article:calibration-frames-darks-flats-biases|calibration "
                  "frames}, which is twenty minutes of extra work per session "
                  "that quietly decides how clean the final picture looks.",
    },
    {
        "key": "smartscope",
        "label": "I have a smart telescope",
        "heading": "I have a smart telescope",
        "lede": "The box handles tracking, focus and stacking on its own, so "
                "the skill is now in choosing targets, choosing nights, and "
                "finishing the image afterwards.",
        "cards": [
            ("seestar-s30-pro-tour",
             "The Seestar S30 Pro",
             "What the box does well, and the point at which a 30mm aperture "
             "becomes the limiting factor."),
            ("imaging-from-a-city-balcony",
             "Imaging from a City Balcony",
             "A balcony takes away your view of Polaris, most of the sky, and "
             "half the night. Here is how to work with all three."),
            ("siril-post-processing-guide",
             "Finishing the Image in Siril",
             "The free route from the box's output to a picture worth "
             "printing, and the one rule about stretching."),
        ],
        "ending": "The three images at the top of this page were taken with a "
                  "Seestar S30, so this is the route they came from. When you "
                  "want more aperture than 30mm can give you, {route:rig} is "
                  "where that leads.",
    },
    {
        "key": "buying",
        "label": "Buying my first setup",
        "heading": "Buying my first setup",
        "lede": "Smart telescopes changed what a first purchase looks like. A "
                "few years ago the entry point was a mount, a scope, a camera "
                "and a laptop. Now it can be one box. Read these before you "
                "spend anything.",
        "cards": [
            ("seestar-s30-pro-tour",
             "The Seestar S30 Pro",
             "Deep sky and the Milky Way from the same 1.65kg box, and where "
             "a 30mm aperture stops."),
            ("bortle-scale-narrowband-filters",
             "The Bortle Scale",
             "Work out what your sky can do before you decide what to buy. "
             "The sky matters more than the equipment."),
            ("photograph-milky-way-phone",
             "Photograph the Milky Way with Your Phone",
             "Do this before you spend anything. It costs nothing and it will "
             "tell you whether you enjoy the standing around in the dark "
             "part."),
        ],
        "more": GEAR_LINK,
        "ending": "If you already know you want the version with no ceiling "
                  "on it, {route:rig} covers what that actually involves.",
    },
    {
        "key": "rig",
        "label": "Buying a full rig",
        "heading": "Buying a full rig",
        "lede": "A mount, a telescope, a dedicated camera and something to run "
                "it all. It is the most capable setup and the least "
                "forgiving, because every part has to work with every other "
                "part. Read all three before you order anything.",
        "cards": [
            ("main-rig-tour",
             "The Rig",
             "A tour of the setup that takes every deep-sky image on this "
             "site, and why each part was chosen over the alternatives."),
            ("asiair-astrophotography-control",
             "The ASIAir",
             "The box that ties the rest together. Plate solving, autofocus, "
             "guiding, and where the closed ecosystem bites."),
            ("bortle-scale-narrowband-filters",
             "The Bortle Scale",
             "What your sky will let a rig achieve, and what narrowband "
             "filters can and cannot buy back in a city."),
        ],
        "more": GEAR_LINK,
        "ending": "Worth saying plainly: a smart telescope will produce a good "
                  "image on your first night, and a rig probably will not. If "
                  "you have never assembled one, {route:smartscope} is a "
                  "cheaper way to find out whether you like the work.",
    },
]
ROUTE_KEYS = [r["key"] for r in ROUTES]

# Used when a {route:key} token needs a readable label inside a sentence.
ROUTE_PHRASES = {
    "curious": "the curious route",
    "phone": "the phone route",
    "camera": "the camera route",
    "smartscope": "the smart telescope route",
    "buying": "buying your first setup",
    "rig": "the full rig route",
}


# --------------------------------------------------------------- 4. EXTRAS

# Articles that do not belong to any one route and do not belong in the
# staged path either, because they are governed by the calendar rather
# than by skill. These sit below the routes, visible whatever the reader
# picked, on the grounds that somebody who has just worked out they own a
# usable camera should also be told the Geminids are in December.
#
# An entry here should have no "stage" in site-data.json, which keeps it
# out of the full path while leaving it live everywhere else on the site.

EXTRAS_SUMMARY = "Meteor showers worth planning around"
EXTRAS_NOTE = ("A few nights each year are worth planning around, and they do "
               "not care how much equipment you own. These work with a phone "
               "on a tripod just as well as with a full camera.")

EXTRAS = [
    ("photograph-a-meteor-shower",
     "Photograph a Meteor Shower",
     "Which showers are worth staying up for, why you point away from the "
     "radiant rather than at it, and why the whole trick is taking far more "
     "frames than feels sensible."),
]

# Left empty so the collapsed block reads as one summary line plus one note,
# matching the full path below it. Set it to a sentence to bring the closing
# line back.
EXTRAS_OUT = ""


# ----------------------------------------------------------------- 5. FULL

FULL_SUMMARY = "The whole thing, in order"
FULL_NOTE = ("Every article, arranged the way the work actually happens. "
             "Roughly eighty minutes end to end, so this is for when you "
             "already know you want it.")

# Stage key -> heading. Order here is the order in the full path.
STAGES = [
    ("plan", "Plan the night"),
    ("capture", "Capture the image"),
    ("process", "Process what you caught"),
    ("gear", "The gear behind it"),
]
STAGE_FOOTERS = {"gear": GEAR_LINK}

# Carries inline markup, so this one is not escaped.
VETERAN = ('Already shooting? You probably want '
           '<a href="/gallery.html">the gallery</a> or '
           '<a href="/gear.html">the gear list</a> instead. Every article '
           'lives on <a href="/articles.html">the articles page</a>, '
           'newest first.')


# ------------------------------------------------------------------ build

class BuildError(Exception):
    """A missing slug is worth failing the build for. A card that silently
    vanishes is far harder to notice than a red cross in Actions."""


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


def sort_key(entry):
    """stageOrder first, then newest, so a partly ordered stage still reads
    well."""
    order = entry.get("stageOrder")
    order = order if isinstance(order, int) else 999
    try:
        date = datetime.strptime(entry.get("date", ""), "%d-%m-%Y")
    except (TypeError, ValueError):
        date = datetime.min
    return (order, -date.toordinal())


def staged(articles):
    by_stage = {key: [] for key, _ in STAGES}
    for entry in articles.values():
        stage = entry.get("stage")
        if stage in by_stage:
            by_stage[stage].append(entry)
    for key in by_stage:
        by_stage[key].sort(key=sort_key)
    return by_stage


def article_url(slug):
    return f"/{ARTICLE_DIR}/{slug}.html"


def tokens(text, articles):
    """Expand {route:}, {article:} and {url:} inside escaped copy.

    The prose is escaped first and the markup spliced in afterwards, so the
    copy above stays plain text and an ampersand in a sentence cannot break
    the page. A brace that is not a known token is left alone.
    """
    out = ""
    rest = esc(text)
    while "{" in rest:
        before, brace, after = rest.partition("{")
        kind, colon, tail = after.partition(":")
        if kind not in ("route", "article", "url") or not colon or "}" not in tail:
            out += before + brace
            rest = after
            continue

        body, _, rest = tail.partition("}")
        out += before

        if kind == "route":
            if body not in ROUTE_KEYS:
                raise BuildError(f"unknown route '{body}' in copy")
            label = ROUTE_PHRASES.get(body, "that route")
            out += (f'<button type="button" class="sh-goto" '
                    f'data-goto="{esc(body)}">{esc(label)}</button>')
        else:
            target, _, label = body.partition("|")
            label = label or target
            if kind == "article":
                if target not in articles:
                    raise BuildError(f"unknown article slug '{target}' in copy")
                href = article_url(target)
            else:
                href = target if target.startswith("/") else "/" + target
            out += f'<a href="{esc(href)}">{label}</a>'
    return out + rest


def build_sky(articles):
    """The sky panel shell.

    Holds no astronomy. /tonight-core.js fills #shSkyOut in, so this page
    and the engine cannot drift apart.

    The map is progressive: the coordinate readout and the Bortle picker
    are plain HTML that work on their own, and Leaflet upgrades the empty
    div above them into a draggable pin if it loads. With JavaScript off,
    or tiles blocked, the reader sees SKY_FALLBACK rather than a broken
    grey box.
    """
    if SKY_BORTLE_ARTICLE not in articles:
        raise BuildError(
            f"sky panel Bortle link '{SKY_BORTLE_ARTICLE}' does not exist")

    bortle_opts = "".join(
        f'<option value="{n}"{" selected" if n == 5 else ""}>{n}{esc(t)}</option>'
        for n, t in [(1, " (pristine)"), (2, " (very dark)"), (3, " (rural)"),
                     (4, " (rural/suburban)"), (5, " (suburban)"),
                     (6, " (bright suburban)"), (7, " (suburban/urban)"),
                     (8, " (city)"), (9, " (inner city)")]
    )

    return (
        '      <section class="sh-sky" id="shSky">\n'
        f'        <h2>{esc(SKY_TITLE)}</h2>\n'
        f'        <p class="sh-sky-lede">{esc(SKY_LEDE)}</p>\n'

        '        <div class="sh-sky-map" id="shSkyMap" '
        f'data-lat="{SKY_MAP_LAT}" data-lng="{SKY_MAP_LNG}" '
        f'data-zoom="{SKY_MAP_ZOOM}" role="application" '
        'aria-label="Map for choosing your observing location"></div>\n'

        '        <div class="sh-sky-loc">\n'
        '          <p class="sh-sky-coords" id="shSkyCoords"></p>\n'
        '          <button type="button" class="btn sh-sky-geo" id="shSkyGeo">'
        'Use my location</button>\n'
        '        </div>\n'
        f'        <p class="sh-sky-map-help">{esc(SKY_MAP_HELP)}</p>\n'

        '        <div class="sh-sky-bortle">\n'
        '          <label for="shSkyBortle">How bright is your sky?</label>\n'
        f'          <select id="shSkyBortle">{bortle_opts}</select>\n'
        f'          <a href="{article_url(SKY_BORTLE_ARTICLE)}">'
        f'{esc(SKY_BORTLE_LINK)}</a>\n'
        '        </div>\n'

        '        <div class="sh-sky-datenav">\n'
        '          <button type="button" class="btn sh-sky-nav" id="shSkyPrev" '
        'aria-label="Previous night">&#8592;</button>\n'
        '          <span id="shSkyDate">Tonight</span>\n'
        '          <button type="button" class="btn sh-sky-nav" id="shSkyNext" '
        'aria-label="Next night">&#8594;</button>\n'
        '        </div>\n'

        '        <div class="sh-sky-out" id="shSkyOut" aria-live="polite">\n'
        f'          <p class="sh-sky-wait">{esc(SKY_FALLBACK)}</p>\n'
        '        </div>\n'
        f'        <p class="sh-sky-foot">{esc(SKY_FOOT)}</p>\n'
        '      </section>\n'
    )


def build_tonight(articles):
    steps = "".join(
        f'          <li class="sh-step">\n'
        f'            <span class="sh-step-b">\n'
        f'              <span class="sh-step-t">{esc(title)}</span>\n'
        f'              <span class="sh-step-d">{tokens(body, articles)}</span>\n'
        f'            </span>\n'
        f'          </li>\n'
        for title, body in TONIGHT_STEPS
    )
    return (
        '      <section class="sh-tonight">\n'
        f'        <h2>{esc(TONIGHT_TITLE)}</h2>\n'
        f'        <p class="sh-tonight-lede">{esc(TONIGHT_LEDE)}</p>\n'
        '        <ol class="sh-steps">\n'
        f'{steps}'
        '        </ol>\n'
        f'        <p class="sh-tonight-out">{esc(TONIGHT_OUT)}</p>\n'
        '      </section>\n'
    )


def build_chooser():
    """The route pills. Nothing is preselected, so a first-time reader gets
    the proof and the free step rather than a wall of choices."""
    pills = "".join(
        f'          <button type="button" class="filter-pill sh-route" '
        f'data-route="{esc(r["key"])}" aria-pressed="false">'
        f'{esc(r["label"])}</button>\n'
        for r in ROUTES
    )
    return (
        '      <div class="sh-chooser" id="shChooser" hidden>\n'
        f'        <p class="sh-chooser-q">{esc(ROUTE_PROMPT)}</p>\n'
        f'        <div class="filter-pills" role="group" '
        f'aria-label="{esc(ROUTE_PROMPT)}">\n'
        f'{pills}'
        '        </div>\n'
        f'        <p class="sh-chooser-help">{esc(ROUTE_HELP)}</p>\n'
        '      </div>\n'
    )


def build_card(slug, title, blurb, number, articles):
    entry = articles.get(slug)
    if entry is None:
        raise BuildError(f"card points at unknown article slug '{slug}'")

    title = title or entry.get("title", "")
    read = entry.get("readTime")
    desc = (f'\n              <span class="sh-desc">{esc(blurb)}</span>'
            if blurb else "")
    meta = (f'\n              <span class="sh-meta">{esc(read)}</span>'
            if read else "")

    return (
        f'          <a class="sh-card" href="{esc(article_url(slug))}">\n'
        f'            <span class="sh-num" aria-hidden="true">{number}</span>\n'
        f'            <span class="sh-text">\n'
        f'              <span class="sh-title">{esc(title)}</span>'
        f'{desc}{meta}\n'
        f'            </span>\n'
        f'          </a>\n'
    )


def build_routes(articles):
    out = []
    for route in ROUTES:
        cards = "".join(
            build_card(slug, title, blurb, i, articles)
            for i, (slug, title, blurb) in enumerate(route["cards"], start=1)
        )
        more = f'          {route["more"]}\n' if route.get("more") else ""
        ending = route.get("ending")
        ending_html = (
            f'        <p class="sh-route-end">{tokens(ending, articles)}</p>\n'
            if ending else ""
        )
        out.append(
            f'      <section class="sh-route-block" '
            f'data-block="{esc(route["key"])}" hidden>\n'
            f'        <h2 class="sh-route-head">{esc(route["heading"])}</h2>\n'
            f'        <p class="sh-route-lede">'
            f'{tokens(route["lede"], articles)}</p>\n'
            f'        <div class="sh-list">\n'
            f'{cards}{more}'
            f'        </div>\n'
            f'{ending_html}'
            f'      </section>\n'
        )
    return "".join(out)


def build_extras(articles):
    """The seasonal block.

    Deliberately not a .sh-route-block: the route script hides every one of
    those that does not match the current pill, and this has to stay on
    screen whatever the reader picked. It borrows .sh-full, the same closed
    details used by the full path below it, so a reader meets one short
    summary line rather than a full panel on the way down the page. That
    also means this needs nothing new in styles.css.
    """
    if not EXTRAS:
        return ""

    cards = "".join(
        build_card(slug, title, blurb, i, articles)
        for i, (slug, title, blurb) in enumerate(EXTRAS, start=1)
    )
    out = (f'        <p class="sh-full-note sh-extras-out">{esc(EXTRAS_OUT)}</p>\n'
           if EXTRAS_OUT else "")
    return (
        '      <details class="sh-full sh-extras">\n'
        f'        <summary>{esc(EXTRAS_SUMMARY)}</summary>\n'
        f'        <p class="sh-full-note">{tokens(EXTRAS_NOTE, articles)}</p>\n'
        '        <div class="sh-list">\n'
        f'{cards}'
        '        </div>\n'
        f'{out}'
        '      </details>\n'
    )


def build_full(by_stage, articles):
    """Every staged article, numbered straight through with no restarts, so
    the sequence reads as one path rather than four short ones."""
    blocks = []
    number = 0
    for key, heading in STAGES:
        entries = by_stage.get(key, [])
        footer = STAGE_FOOTERS.get(key, "")
        if not entries and not footer:
            continue

        cards = ""
        for entry in entries:
            number += 1
            cards += build_card(entry["slug"], entry.get("title", ""),
                                None, number, articles)
        footer_html = f'          {footer}\n' if footer else ""
        blocks.append(
            f'        <p class="sh-full-stage">{esc(heading)}</p>\n'
            f'        <div class="sh-list">\n'
            f'{cards}{footer_html}'
            f'        </div>\n'
        )

    return (
        '      <details class="sh-full">\n'
        f'        <summary>{esc(FULL_SUMMARY)}</summary>\n'
        f'        <p class="sh-full-note">{esc(FULL_NOTE)}</p>\n'
        + "".join(blocks) +
        '      </details>\n'
    ), number


def build_json_ld(by_stage):
    """An ItemList of the full path, in path order, so the sequence stays
    legible to a crawler even though the markup keeps it collapsed."""
    elements = []
    position = 1
    for key, _ in STAGES:
        for entry in by_stage.get(key, []):
            elements.append({
                "@type": "ListItem",
                "position": position,
                "url": f"{DOMAIN}{article_url(entry.get('slug', ''))}",
                "name": entry.get("title", ""),
            })
            position += 1

    return json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Start Here: a guided path through astrophotography",
        "description": PAGE_DESC,
        "url": f"{DOMAIN}/{OUT}",
        "numberOfItems": len(elements),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "itemListElement": elements,
    }, ensure_ascii=False)


SCRIPT = """
(function () {
  var chooser = document.getElementById('shChooser');
  if (!chooser) return;

  var pills  = Array.prototype.slice.call(chooser.querySelectorAll('.sh-route'));
  var blocks = Array.prototype.slice.call(document.querySelectorAll('.sh-route-block'));
  if (!pills.length || !blocks.length) return;

  // Only reveal the pills once we know the script is running, so a reader
  // without JS never sees a control that cannot do anything. Everything
  // ships in the HTML, so a crawler still gets all six routes.
  chooser.hidden = false;

  var KEY  = 'bhapstar:startHereRoute';
  var FADE = 180;   // must match the CSS transition duration
  var current = 'none';
  var token = 0;    // guards against a second pill tapped mid-transition

  var still = false;
  try {
    still = window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) {}

  function commit(route) {
    blocks.forEach(function (block) {
      block.hidden = block.getAttribute('data-block') !== route;
    });
    pills.forEach(function (pill) {
      var on = pill.getAttribute('data-route') === route;
      pill.classList.toggle('active', on);
      pill.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    current = route;
    try {
      if (route === 'none') sessionStorage.removeItem(KEY);
      else sessionStorage.setItem(KEY, route);
    } catch (e) { /* private mode, not worth caring about */ }
  }

  function apply(route, animate) {
    if (route === current) return;

    var showing = blocks.filter(function (b) { return !b.hidden; });
    if (!animate || still || !showing.length) { commit(route); return; }

    var mine = ++token;
    showing.forEach(function (b) { b.classList.add('sh-swapping'); });

    window.setTimeout(function () {
      if (mine !== token) return;   // a newer choice took over
      commit(route);
      blocks.forEach(function (b) { b.classList.remove('sh-swapping'); });
    }, FADE);
  }

  pills.forEach(function (pill) {
    pill.addEventListener('click', function () {
      // Tapping the active route a second time clears it.
      apply(pill.classList.contains('active')
              ? 'none' : pill.getAttribute('data-route'), true);
    });
  });

  // "the full rig route" inside a closing line.
  document.addEventListener('click', function (ev) {
    var jump = ev.target.closest && ev.target.closest('.sh-goto');
    if (!jump) return;
    apply(jump.getAttribute('data-goto'), true);
    chooser.scrollIntoView({ behavior: still ? 'auto' : 'smooth',
                             block: 'start' });
  });

  var saved = null;
  try { saved = sessionStorage.getItem(KEY); } catch (e) {}
  var valid = pills.some(function (p) {
    return p.getAttribute('data-route') === saved;
  });

  // First paint, no animation. With nothing saved this collapses every
  // route, so the page opens on the sky panel and the free step.
  commit(saved && valid ? saved : 'none');
})();




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
  function hoursText(h) {
    var w = Math.floor(h), m = Math.round((h - w) * 60);
    if (m === 60) { w++; m = 0; }
    return w === 0 ? m + ' min' : w + 'h' + (m ? ' ' + m + 'm' : '');
  }

  /* ── Map ─────────────────────────────────────────────
     Leaflet with OpenStreetMap tiles. No API key, so
     nothing sensitive sits in the page source. */
  var marker = null, map = null;

  function showCoords() {
    coords.textContent = state.lat.toFixed(4) + ', ' + state.lng.toFixed(4);
  }

  function moveTo(lat, lng, recentre) {
    state.lat = lat; state.lng = lng;
    showCoords();
    if (marker) marker.setLatLng([lat, lng]);
    if (map && recentre) map.setView([lat, lng], map.getZoom());
    save();
    render();
  }

  if (window.L && mapEl) {
    map = L.map(mapEl, { scrollWheelZoom: false })
           .setView([state.lat, state.lng], parseInt(mapEl.dataset.zoom, 10));

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
  function reasonFor(r) {
    var bits = [];
    if (r.bf < 0.5) bits.push('Your sky is too bright for this one. It will be a struggle.');
    else if (r.bf < 0.85) bits.push('Light pollution will cost you contrast here.');
    if (r.moonHit > 0.45) bits.push('The moon is up and bright for most of this window.');
    else if (r.moonHit > 0.2) bits.push('Some moonlight to work around.');
    if (r.maxAlt < 35) bits.push('Stays low, so expect softer stars.');
    if (!bits.length) bits.push('Good conditions for this one tonight.');
    return bits.join(' ');
  }

  function render() {
    var date = new Date();
    date.setDate(date.getDate() + state.offset);
    document.getElementById('shSkyDate').textContent = state.offset === 0
      ? 'Tonight'
      : date.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });

    var plan = C.planNight(date, state.lat, state.lng, state.bortle, MIN_ALT);

    if (!plan.dark) {
      out.innerHTML = '<p class="sh-sky-wait">The sun never drops far enough ' +
        'below the horizon on this date at this latitude, so there is no ' +
        'properly dark window.</p>';
      return;
    }

    var moonPct = Math.round(plan.moonIll * 100);
    var html =
      '<div class="sh-sky-facts">' +
        '<span><b>' + hhmm(plan.darkStart) + ' to ' + hhmm(plan.darkEnd) +
          '</b><i>Properly dark</i></span>' +
        '<span><b>' + hoursText((plan.darkEnd - plan.darkStart) / 3600000) +
          '</b><i>Dark hours</i></span>' +
        '<span><b>' + moonPct + '%</b><i>' + C.moonPhaseName(plan.moonPhase) + '</i></span>' +
        '<span><b>Bortle ' + state.bortle + '</b><i>Your sky</i></span>' +
      '</div>';

    var v;
    if (moonPct < 15 || plan.moonUpFrac < 0.15) {
      v = 'A good night. The moon is barely a factor, so faint things are on the table.';
    } else if (moonPct > 70 && plan.moonUpFrac > 0.6) {
      v = 'A bright moon for most of the night. Nebulae and star clusters will ' +
          'survive it, galaxies will not.';
    } else {
      v = 'Workable. Favour things that peak while the moon is low or already down.';
    }
    if (state.bortle >= 7) {
      v += ' From a sky this bright, a filter is doing most of the work.';
    }
    html += '<p class="sh-sky-verdict">' + v + '</p>';

    if (!plan.targets.length) {
      html += '<p class="sh-sky-wait">Nothing gets high enough for long enough ' +
              'tonight from here. Step forward a few nights and try again.</p>';
      out.innerHTML = html;
      wireMore();
      return;
    }

    var list = state.expanded ? plan.targets : plan.targets.slice(0, SHOWN);
    html += '<ol class="sh-sky-list">' + list.map(function (r) {
      return '<li>' +
        '<a class="sh-sky-name" href="/share/' + r.tg.slug + '.html">' + r.tg.n + '</a>' +
        '<span class="sh-sky-tag sh-sky-tag-' + r.tg.t + '">' + C.LABEL[r.tg.t] + '</span>' +
        '<span class="sh-sky-when">' + hhmm(r.winStart) + ' to ' + hhmm(r.winEnd) +
          ', ' + hoursText(r.hours) + ' usable, peaks at ' + Math.round(r.maxAlt) + '\u00B0</span>' +
        '<span class="sh-sky-why">' + reasonFor(r) + '</span>' +
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
      moveTo(pos.coords.latitude, pos.coords.longitude, true);
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

  showCoords();
  render();
})();
"""


def build_page(articles, by_stage):
    page_url = f"{DOMAIN}/{OUT}"
    share_url = f"{DOMAIN}/{SHARE_IMAGE}"
    full_html, _ = build_full(by_stage, articles)
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
  <meta property="og:image" content="{esc(share_url)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta name="twitter:description" content="{esc(PAGE_DESC)}" />
  <meta name="twitter:image" content="{esc(share_url)}" />
  <link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>
  <link rel="stylesheet" href="/styles.css" />

  <link rel="stylesheet" href="https://unpkg.com/leaflet@{LEAFLET_VERSION}/dist/leaflet.css" integrity="{LEAFLET_CSS_SRI}" crossorigin="" />
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

{build_sky(articles)}
{build_tonight(articles)}
{build_chooser()}
{build_routes(articles)}
{build_extras(articles)}
{full_html}
      <p class="sh-veteran">{VETERAN}</p>

    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

  <script src="https://unpkg.com/leaflet@{LEAFLET_VERSION}/dist/leaflet.js" integrity="{LEAFLET_JS_SRI}" crossorigin=""></script>
  <script src="/tonight-core.js"></script>
  <script src="/partials/partials.js"></script>
  <script>{SCRIPT}</script>
</body>
</html>
'''


def main():
    try:
        articles, _gallery = load_data()
        by_stage = staged(articles)
        html = build_page(articles, by_stage)
    except BuildError as exc:
        print(f"✗ {OUT}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    on_path = sum(len(v) for v in by_stage.values())
    print(f"✓ {OUT}  ({len(ROUTES)} routes, {len(EXTRAS)} seasonal extras, "
          f"{on_path} articles in the full path)")

    # An article that is live but on no route, no extra and not on the full
    # path is almost always an oversight rather than a decision.
    routed = {slug for r in ROUTES for slug, _, _ in r["cards"]}
    routed |= {slug for slug, _, _ in EXTRAS}
    for slug, entry in sorted(articles.items()):
        if slug not in routed and not entry.get("stage"):
            print(f"  ! '{slug}' appears nowhere on this page")

    # An extra that also carries a stage would appear twice.
    for slug, _, _ in EXTRAS:
        if articles.get(slug, {}).get("stage"):
            print(f"  ! extra '{slug}' also has a stage, so it appears twice")

    for key, heading in STAGES:
        if not by_stage.get(key) and key not in STAGE_FOOTERS:
            print(f"  ! stage '{key}' ({heading}) is empty and was omitted")


if __name__ == "__main__":
    main()
