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

# The sky panel. This is the whole tool, not a preview of one: the reader
# picks where they are and gets tonight's darkness window, the moon, and
# every target from the gallery that is actually worth pointing at, ranked.
#
# All the astronomy lives in /tonight-core.js. This file emits an empty
# shell and the copy around it, and never calculates anything itself.
SKY_TITLE = "What is worth looking at tonight"
SKY_LEDE = ("Pick where you are and this works out when it actually gets "
            "dark tonight, what the moon is doing, and which objects are "
            "high enough for long enough to be worth the effort. Everything "
            "is calculated on your phone, so it keeps working out in the "
            "desert with no signal.")

# Presets a reader can tap without granting location permission. The Bortle
# numbers are the honest figure for each site rather than the flattering
# one, because the panel demotes targets using them and a wrong number here
# produces confident bad advice.
#
# These must stay in step with PRESETS in /tonight-core.js.
SKY_PRESETS = [
    ("Dubai balcony", 25.2048, 55.2708, 8),
    ("Al Qudra",      24.8000, 55.3300, 6),
    ("Al Quaa",       23.5333, 55.4833, 2),
]

# Shown before the panel fills in, and permanently if JavaScript is off.
SKY_FALLBACK = ("Working out tonight's sky. If nothing appears here, "
                "JavaScript is switched off in your browser.")

SKY_ADVANCED = "Somewhere else, or a fussier horizon"

SKY_ALT_HELP = ("Below about 30 degrees you are shooting through a lot more "
                "air, so stars bloat and detail drops. Lower this if you are "
                "willing to take that hit.")

SKY_FOOT = ("Times use your device clock. Tap any object to see one taken "
            "from this part of the world.")


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


def build_sky():
    """The sky panel shell.

    Holds no astronomy. /tonight-core.js fills #shSkyOut in, so this page
    and the engine can never disagree about tonight.

    Degrades to SKY_FALLBACK with JavaScript off, which is why the copy
    around it never promises anything the shell alone cannot deliver.
    """
    pills = "".join(
        f'          <button type="button" class="filter-pill sh-sky-pill" '
        f'data-lat="{lat}" data-lng="{lng}" data-bortle="{b}" '
        f'aria-pressed="false">{esc(name)}</button>\n'
        for name, lat, lng, b in SKY_PRESETS
    )
    bortle_opts = "".join(
        f'<option value="{n}">{n}{esc(t)}</option>'
        for n, t in [(2, " (very dark)"), (3, " (rural)"), (5, " (suburban)"),
                     (6, " (bright suburban)"), (8, " (city)")]
    )
    return (
        '      <section class="sh-sky" id="shSky">\n'
        f'        <h2>{esc(SKY_TITLE)}</h2>\n'
        f'        <p class="sh-sky-lede">{esc(SKY_LEDE)}</p>\n'

        '        <div class="sh-sky-pills filter-pills" role="group" '
        f'aria-label="{esc(SKY_TITLE)}">\n'
        f'{pills}'
        '          <button type="button" class="filter-pill sh-sky-pill" '
        'id="shSkyGeo">Use my location</button>\n'
        '        </div>\n'

        '        <details class="sh-sky-adv">\n'
        f'          <summary>{esc(SKY_ADVANCED)}</summary>\n'
        '          <div class="sh-sky-adv-grid">\n'
        '            <label>Latitude<input type="number" id="shSkyLat" '
        'step="0.0001" placeholder="25.2048" /></label>\n'
        '            <label>Longitude<input type="number" id="shSkyLng" '
        'step="0.0001" placeholder="55.2708" /></label>\n'
        f'            <label>Bortle<select id="shSkyBortle">{bortle_opts}</select></label>\n'
        '            <button type="button" class="btn sh-sky-apply" '
        'id="shSkyApply">Apply</button>\n'
        '          </div>\n'
        '          <label class="sh-sky-alt">Minimum height\n'
        '            <input type="range" id="shSkyMinAlt" min="15" max="50" '
        'step="5" value="30" />\n'
        '            <output id="shSkyMinAltOut">30&deg;</output>\n'
        '          </label>\n'
        f'          <p class="sh-sky-alt-help">{esc(SKY_ALT_HELP)}</p>\n'
        '        </details>\n'

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

   The ranked list is capped at SHOWN until the reader asks for the rest.
   A first-time visitor meeting nineteen objects at once learns nothing;
   five with a real reason attached is a decision they can act on. */
(function () {
  var sky = document.getElementById('shSky');
  var out = document.getElementById('shSkyOut');
  var C   = window.TonightCore;
  if (!sky || !out || !C) return;

  var SHOWN = 5;

  var pills = Array.prototype.slice.call(sky.querySelectorAll('.sh-sky-pill[data-lat]'));
  var geo   = document.getElementById('shSkyGeo');
  if (!pills.length) return;

  var state = {
    lat: +pills[0].dataset.lat,
    lng: +pills[0].dataset.lng,
    bortle: +pills[0].dataset.bortle,
    name: pills[0].textContent,
    offset: 0,
    minAlt: 30,
    expanded: false
  };

  try {
    var saved = JSON.parse(localStorage.getItem('tonight.loc') || 'null');
    if (saved && typeof saved.lat === 'number') {
      state.lat = saved.lat; state.lng = saved.lng;
      state.bortle = saved.bortle; state.name = saved.name;
    }
  } catch (e) {}

  function save() {
    try {
      localStorage.setItem('tonight.loc', JSON.stringify({
        lat: state.lat, lng: state.lng, bortle: state.bortle, name: state.name
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

  function markPills() {
    var matched = false;
    pills.forEach(function (p) {
      var on = Math.abs(+p.dataset.lat - state.lat) < 0.001 &&
               Math.abs(+p.dataset.lng - state.lng) < 0.001;
      if (on) matched = true;
      p.setAttribute('aria-pressed', on ? 'true' : 'false');
      p.classList.toggle('is-active', on);
    });
    if (geo) {
      geo.setAttribute('aria-pressed', matched ? 'false' : 'true');
      geo.classList.toggle('is-active', !matched);
    }
  }

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
    markPills();

    var date = new Date();
    date.setDate(date.getDate() + state.offset);
    document.getElementById('shSkyDate').textContent = state.offset === 0
      ? 'Tonight'
      : date.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });

    var plan = C.planNight(date, state.lat, state.lng, state.bortle, state.minAlt);

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
        '<span><b>' + state.name + '</b><i>Bortle ' + state.bortle + '</i></span>' +
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
      html += '<p class="sh-sky-wait">Nothing clears that height during tonight\u2019s ' +
              'dark window from here. Try lowering the minimum height, or step ' +
              'forward a few nights.</p>';
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
        (state.expanded
          ? 'Show fewer'
          : 'Show all ' + plan.targets.length) + '</button>';
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

  pills.forEach(function (p) {
    p.addEventListener('click', function () {
      state.lat = +p.dataset.lat; state.lng = +p.dataset.lng;
      state.bortle = +p.dataset.bortle; state.name = p.textContent;
      save(); render();
    });
  });

  if (geo) geo.addEventListener('click', function () {
    if (!navigator.geolocation) return;
    geo.textContent = 'Locating\u2026';
    navigator.geolocation.getCurrentPosition(function (pos) {
      geo.textContent = 'Use my location';
      state.lat = pos.coords.latitude;
      state.lng = pos.coords.longitude;
      state.name = 'Your location';
      save(); render();
    }, function () {
      geo.textContent = 'Use my location';
    }, { timeout: 10000 });
  });

  document.getElementById('shSkyPrev').addEventListener('click', function () {
    state.offset--; render();
  });
  document.getElementById('shSkyNext').addEventListener('click', function () {
    state.offset++; render();
  });

  var slider = document.getElementById('shSkyMinAlt');
  slider.addEventListener('input', function () {
    state.minAlt = parseInt(this.value, 10);
    document.getElementById('shSkyMinAltOut').textContent = state.minAlt + '\u00B0';
    render();
  });

  document.getElementById('shSkyApply').addEventListener('click', function () {
    var la = parseFloat(document.getElementById('shSkyLat').value);
    var ln = parseFloat(document.getElementById('shSkyLng').value);
    if (isNaN(la) || isNaN(ln) || la < -90 || la > 90 || ln < -180 || ln > 180) return;
    state.lat = la; state.lng = ln;
    state.bortle = parseInt(document.getElementById('shSkyBortle').value, 10);
    state.name = 'Your location';
    save(); render();
  });

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

{build_sky()}
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
