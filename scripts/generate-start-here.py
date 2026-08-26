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

  It is therefore not a reading list. It opens with evidence, gives away
  something free before asking for anything, and only then offers a short
  route. The eighty-minute path still exists, at the bottom, collapsed,
  for the reader who is already sold.

The page has four parts:

  1. PROOF    Three gallery images, captioned with what took them. Pulled
              from the gallery entries in site-data.json so the specs can
              never drift from the gallery itself.

  2. TONIGHT  One thing to do on the next clear night with no equipment.
              Pure copy, edited in TONIGHT_STEPS below.

  3. ROUTES   Six curated routes of three articles each, chosen by where
              the reader is rather than by what they own.

  4. FULL     Every staged article in order, inside a closed <details>.

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
PAGE_DESC = ("You need less equipment than you think. Four galaxies taken with "
             "a smart telescope that fits in a shoulder bag, one thing to try "
             "tonight with nothing at all, and a short route through the rest "
             "depending on where you are.")

SUBTITLE = "You need less equipment than you think."

INTRO = ("This page is for anyone who has looked at a picture of a galaxy and "
         "wondered whether an ordinary person could take one. You can. This is "
         "where to begin, and the first step costs nothing at all.")


# ---------------------------------------------------------------- 1. PROOF

# Gallery slugs, in display order. Everything else about each image, the
# file, the alt text and the capture specs, is read from its gallery entry
# so this page and gallery.html can never disagree about what took what.
#
# All three show at every width: a grid on desktop, a snap-scroll strip on
# mobile. Nothing is dropped on small screens, because PROOF_LINE below
# refers to these images by what they are. "Four galaxies and the centre
# of our own Milky Way" counts Andromeda as one, the Leo Triplet as three,
# and the Milky Way as the last, so changing this list means changing that
# sentence too.
PROOF_SLUGS = [
    "andromeda-galaxy-m31",
    "leo-triplet-m65-m66-ngc3628",
    "the-milky-way",
]

# Short display names, because gallery titles carry catalogue numbers that
# mean nothing to a first-time reader. A slug with no entry here keeps its
# gallery title.
PROOF_NAMES = {
    "andromeda-galaxy-m31": "The Andromeda Galaxy",
    "leo-triplet-m65-m66-ngc3628": "The Leo Triplet",
    "the-milky-way": "The Milky Way",
}

# Carries inline markup, so this one is not escaped. Keep it plain.
PROOF_LINE = ("Four galaxies and the centre of our own Milky Way, all taken "
              "with a <strong>smart telescope that fits in a shoulder "
              "bag</strong> and sets itself up in about a minute. No laptop, "
              "no counterweights, no observatory. Six of the images in the "
              "gallery were taken this way.")

# Used for the social card, since this page now has something worth showing.
SHARE_IMAGE = "images/andromeda-galaxy-m31.webp"


# -------------------------------------------------------------- 2. TONIGHT

TONIGHT_TITLE = "Try this tonight, with nothing"
TONIGHT_LEDE = ("Before you read anything or buy anything, do these three "
                "things on the next clear night. They take about half an hour "
                "and they will tell you more about your sky than any article "
                "can.")

TONIGHT_STEPS = [
    ("Go outside and wait twenty minutes",
     "Your eyes need roughly twenty minutes in the dark before they work "
     "properly. Keep your phone screen off, or switch it to the dimmest red "
     "setting you have. Stars will keep appearing the whole time you wait."),
    ("Count what you can actually see",
     "Pick one patch of sky and count the stars in it. From the middle of "
     "Dubai you might get one or two. An hour into the Dubai desert you will "
     "see hundreds. Two and a half hours into the heart of the Abu Dhabi, "
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
ROUTE_HELP = ("Pick one and you get three articles instead of eleven. Nothing "
              "is hidden permanently, and the full list is at the bottom of "
              "the page. Tap the same one again to clear it.")

GEAR_LINK = ('<a class="sh-more" href="/gear.html">Every piece of gear I use, '
             'with prices <span aria-hidden="true">&#8594;</span></a>')

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
            ("photograph-meteor-shower-milky-way-phone",
             "Photograph the Milky Way with Your Phone",
             "No camera and no experience needed, just a phone, a small "
             "tripod and a dark sky."),
        ],
        "ending": "Twenty two minutes of reading and one drive out of the "
                  "city, and you will have an answer. If it turns out you "
                  "want more, {route:buying} is the next question.",
    },
    {
        "key": "phone",
        "label": "I have a phone",
        "heading": "I have a phone",
        "lede": "A phone will get you the Milky Way arching over a horizon, "
                "and on a dark night it will get you more of it than you "
                "expect. Start here and spend nothing.",
        "cards": [
            ("photograph-meteor-shower-milky-way-phone",
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
            ("photograph-meteor-shower-milky-way-camera",
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
            ("photograph-meteor-shower-milky-way-phone",
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


# ----------------------------------------------------------------- 4. FULL

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


def build_proof(gallery):
    shots = []
    for slug in PROOF_SLUGS:
        entry = gallery.get(slug)
        if not entry:
            raise BuildError(f"proof image '{slug}' is not a gallery entry")
        file = entry.get("file")
        if not file:
            raise BuildError(f"proof image '{slug}' has no file")

        specs = entry.get("specs") or {}
        bits = [specs.get("telescope"), specs.get("integration"),
                (specs.get("location") or "").split(",")[0].strip()]
        caption = " &middot; ".join(esc(b) for b in bits if b)
        name = PROOF_NAMES.get(slug, entry.get("title", ""))
        blurb = entry.get("intro") or entry.get("desc") or ""

        # The href stays a real link to the gallery entry. The script
        # intercepts the click and opens the popup instead, so a reader
        # with no JS still gets somewhere sensible rather than a dead
        # image.
        shots.append(
            f'          <a class="sh-shot" href="/gallery.html#{esc(slug)}"\n'
            f'             data-blurb="{esc(blurb)}">\n'
            f'            <span class="sh-shot-frame">\n'
            f'              <img src="/{esc(file)}" '
            f'alt="{esc(entry.get("alt", ""))}" '
            f'loading="eager" decoding="async" />\n'
            f'            </span>\n'
            f'            <span class="sh-shot-name">{esc(name)}</span>\n'
            f'            <span class="sh-shot-spec">{caption}</span>\n'
            f'          </a>\n'
        )

    return (
        '      <section class="sh-proof">\n'
        '        <div class="sh-proof-grid">\n'
        + "".join(shots) +
        '        </div>\n'
        f'        <p class="sh-proof-line">{PROOF_LINE}</p>\n'
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


def build_modal():
    """One popup, reused by all three proof images.

    Deliberately not the gallery lightbox: this page is trying to hold a
    first-time reader, and sending them to gallery.html one tap in is the
    easiest way to lose them. The popup keeps them here and offers the
    gallery as a decision rather than an accident.
    """
    return (
        '  <div class="sh-modal" id="shModal" hidden>\n'
        '    <div class="sh-modal-back" data-sh-close></div>\n'
        '    <div class="sh-modal-card protect-zone" role="dialog" '
        'aria-modal="true" aria-labelledby="shModalName">\n'
        '      <button type="button" class="sh-modal-x" data-sh-close '
        'aria-label="Close">&#215;</button>\n'
        '      <img class="sh-modal-img" id="shModalImg" src="" alt="" />\n'
        '      <div class="sh-modal-body">\n'
        '        <p class="sh-modal-name" id="shModalName"></p>\n'
        '        <p class="sh-modal-spec" id="shModalSpec"></p>\n'
        '        <p class="sh-modal-blurb" id="shModalBlurb"></p>\n'
        '        <a class="sh-modal-link" id="shModalLink" href="/gallery.html">'
        'See it in the gallery <span aria-hidden="true">&#8594;</span></a>\n'
        '      </div>\n'
        '    </div>\n'
        '  </div>\n'
    )


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
  // route, so the page opens on the proof and the free step.
  commit(saved && valid ? saved : 'none');
})();

/* ── Proof image popup ──────────────────────────────────────────────
   Opens the image in place rather than following the link through to
   gallery.html, so a first-time reader cannot lose this page with one
   stray tap. The link is still there inside the popup for anyone who
   means it. */
(function () {
  var modal = document.getElementById('shModal');
  var shots = Array.prototype.slice.call(document.querySelectorAll('.sh-shot'));
  if (!modal || !shots.length) return;

  var img   = document.getElementById('shModalImg');
  var name  = document.getElementById('shModalName');
  var spec  = document.getElementById('shModalSpec');
  var blurb = document.getElementById('shModalBlurb');
  var link  = document.getElementById('shModalLink');
  var close = modal.querySelector('.sh-modal-x');
  var opener = null;

  function text(el, selector) {
    var found = el.querySelector(selector);
    return found ? found.textContent.trim() : '';
  }

  function open(shot) {
    var picture = shot.querySelector('img');
    if (!picture) return;

    opener = shot;
    img.src = picture.getAttribute('src');
    img.alt = picture.getAttribute('alt') || '';
    name.textContent  = text(shot, '.sh-shot-name');
    spec.textContent  = text(shot, '.sh-shot-spec');
    blurb.textContent = shot.getAttribute('data-blurb') || '';
    blurb.hidden = !blurb.textContent;
    link.setAttribute('href', shot.getAttribute('href'));

    modal.hidden = false;
    // Next frame, so the opacity transition has a starting value to move
    // from rather than being collapsed into the same style recalculation.
    window.requestAnimationFrame(function () {
      modal.classList.add('open');
    });
    document.body.classList.add('sh-modal-lock');
    if (close) close.focus();
  }

  function shut() {
    if (modal.hidden) return;
    modal.classList.remove('open');
    document.body.classList.remove('sh-modal-lock');

    window.setTimeout(function () {
      modal.hidden = true;
      // removeAttribute, not src = '': an empty src resolves against the
      // document URL and makes the browser refetch the page as an image.
      img.removeAttribute('src');
      if (opener) { opener.focus(); opener = null; }
    }, 200);
  }

  shots.forEach(function (shot) {
    shot.addEventListener('click', function (ev) {
      // Let modified clicks through, so "open in new tab" still works.
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
      ev.preventDefault();
      open(shot);
    });
  });

  modal.addEventListener('click', function (ev) {
    if (ev.target.closest && ev.target.closest('[data-sh-close]')) shut();
  });

  document.addEventListener('keydown', function (ev) {
    if (modal.hidden) return;
    if (ev.key === 'Escape') { shut(); return; }
    // Keep tabbing inside the dialog while it is open.
    if (ev.key === 'Tab') {
      var focusable = modal.querySelectorAll('button, a[href]');
      if (!focusable.length) return;
      var first = focusable[0];
      var last  = focusable[focusable.length - 1];
      if (ev.shiftKey && document.activeElement === first) {
        ev.preventDefault(); last.focus();
      } else if (!ev.shiftKey && document.activeElement === last) {
        ev.preventDefault(); first.focus();
      }
    }
  });
})();
"""


def build_page(articles, gallery, by_stage):
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

{build_proof(gallery)}
{build_tonight(articles)}
{build_chooser()}
{build_routes(articles)}
{full_html}
      <p class="sh-veteran">{VETERAN}</p>

    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

{build_modal()}
  <script src="/partials/partials.js"></script>
  <script src="/protect-images.js"></script>
  <script>{SCRIPT}</script>
</body>
</html>
'''


def main():
    try:
        articles, gallery = load_data()
        by_stage = staged(articles)
        html = build_page(articles, gallery, by_stage)
    except BuildError as exc:
        print(f"✗ {OUT}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    on_path = sum(len(v) for v in by_stage.values())
    print(f"✓ {OUT}  ({len(ROUTES)} routes, "
          f"{on_path} articles in the full path)")

    # An article that is live but on neither a route nor the full path is
    # almost always an oversight rather than a decision.
    routed = {slug for r in ROUTES for slug, _, _ in r["cards"]}
    for slug, entry in sorted(articles.items()):
        if slug not in routed and not entry.get("stage"):
            print(f"  ! '{slug}' appears nowhere on this page")

    for key, heading in STAGES:
        if not by_stage.get(key) and key not in STAGE_FOOTERS:
            print(f"  ! stage '{key}' ({heading}) is empty and was omitted")


if __name__ == "__main__":
    main()
