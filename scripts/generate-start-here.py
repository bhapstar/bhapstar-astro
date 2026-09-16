#!/usr/bin/env python3
"""
generate-start-here.py — bhapstar
-------------------------------------------------------------
Writes start-here.html: the page that has to convince a stranger this
hobby is within reach, and then give them one small thing to do.

    python generate-start-here.py

Why this page exists, and why it is not articles.html:

  articles.html is the shelf. Everything, newest first or in reading
  order, which is what a returning reader wants. This page is for someone
  who has just found the site, probably owns a phone and nothing else, and
  has not yet decided whether any of this is for them.

  So it answers one question: what do I do next? It opens with something
  the reader can do on the next clear night for nothing, then offers a
  short route based on what they already have, then points at the planner.

The page has three parts:

  1. TONIGHT  Four things to do on the next clear night with no equipment.
              Pure copy, edited in TONIGHT_STEPS below. This is the start.

  2. ROUTES   Six curated routes of three or four articles each, chosen by
              where the reader is rather than by what they own.

     Opening a card saves the route to sessionStorage, and the article
              page reads it to show a route bar: where the reader is in the
              route, a link back to it, and the next article on it. That bar
              is built by scripts/generate-article-pages.py.

  3. PLAN     One block linking to tonight.html, the planner. The planner
              used to sit at the top of this page. It asked for a location
              and a darkness rating before the page had explained either,
              and it is a tool people return to, so it has its own page.

What used to be here and where it went:

  The meteor shower block is now a link inside the phone and camera route
  endings, and the upcoming peaks are listed on tonight.html. The full
  eighty-minute path is the "Reading order" view on articles.html, which
  still reads "stage" and "stageOrder" from site-data.json.

Where the routes come from:

  ROUTES below, not site-data.json. The same article is framed differently
  depending on who is reading it, and one "desc" field cannot do that, so
  the route blurb lives with the route.

  Each card names a slug. The slug is looked up in site-data.json for its
  URL and read time, and a missing slug fails the build rather than
  silently dropping a card.

Tokens available in route ledes, endings and tonight steps:

      {route:key}             a button that switches to that route
      {article:slug|label}    a link to an article page
      {url:path|label}        a link to anything else on the site
      {ext:https://...|label} a link off the site, opened in a new tab

The page is fully generated, so editing start-here.html by hand will be
overwritten on the next build. Change the copy below instead. Page CSS
lives in /styles.css under "PAGE: Start Here".
"""

import json
import re
import sys
from html import escape as esc

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT = "start-here.html"
ARTICLE_DIR = "articles"

PAGE_TITLE = "Start Here"
PAGE_DESC = ("Four things to try on the next clear night with no equipment "
             "at all, and a short reading route based on what you already "
             "have.")

SUBTITLE = "What to try on the next clear night, and where to go from there."

# No claim about cost here. The free promise lives in TONIGHT_LEDE, where
# it is the literal truth.
INTRO = ("This page is for anyone who has looked at a picture of the night "
         "sky and wondered whether an ordinary person could take one. You "
         "can, and with less equipment than you would guess. Start with the "
         "four steps below on the next clear night, then pick where you are "
         "now for a short list of what to read next.")

SHARE_IMAGE = "images/andromeda-galaxy-m31.webp"


# -------------------------------------------------------------- 1. TONIGHT

TONIGHT_TITLE = "Try this tonight, with nothing"
TONIGHT_LEDE = ("Before you read anything or buy anything, do these four "
                "things on the next clear night. They cost nothing at all, "
                "they take about half an hour, and they will tell you more "
                "about your sky than any article can.")

TONIGHT_STEPS = [
    ("See what is up before you go out",
     "Open {ext:https://stellarium-web.org/|Stellarium Web} in any browser, "
     "put in your town, and it draws tonight's sky above you with the stars "
     "and planets named. It is free and there is nothing to install. It is "
     "the first thing I open before every session."),
    ("Go outside and wait twenty minutes",
     "Your eyes need roughly twenty minutes in the dark before they work "
     "properly. Keep your phone screen off, or switch it to the dimmest red "
     "setting you have. Stars will keep appearing the whole time you wait."),
    ("Count what you can actually see",
     "Pick one patch of sky and count the stars in it. From the middle of "
     "Dubai you might get one or two. An hour into the Dubai desert you will "
     "see hundreds. Two and a half hours into the heart of the Abu Dhabi "
     "desert, you will lose count. That difference is the single biggest "
     "factor in what you will be able to photograph. If you want to know "
     "what those counted stars mean, "
     "{article:bortle-scale-narrowband-filters|the Bortle scale explains it}."),
    ("Take one photo with the phone in your pocket",
     "If you have a small phone tripod, now is the time to use it. Otherwise "
     "prop the phone against a wall or a bag so it cannot move. Use night "
     "mode, or set the shutter to ten seconds, and point it up. Most modern "
     "phones will record stars you could not see with your eyes."),
]

TONIGHT_OUT = ("That is the hobby in miniature: a plan, dark skies, patience, "
               "and a camera held still. Everything below is a way of doing "
               "more of it.")


# --------------------------------------------------------------- 2. ROUTES

ROUTE_PROMPT = "Where are you right now?"
ROUTE_HELP = ("Pick the one that fits and a short reading list opens "
              "underneath.")

GEAR_LINK = ('<a class="sh-more" href="/gear.html">Every piece of gear I use, '
             'with links to buy <span aria-hidden="true">&#8594;</span></a>')

STELLARIUM = "how-i-plan-every-astrophotography-session-using-stellarium"
METEORS = "photograph-a-meteor-shower"

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
            (STELLARIUM,
             "Planning with Stellarium",
             "Free software that tells you what is up tonight, how high it "
             "gets, and when it is highest."),
        ],
        "ending": "The same phone on a tripod will also catch a "
                  "{article:" + METEORS + "|meteor shower}, and "
                  "{url:tonight.html|the tonight page} lists the next ones. "
                  "What a phone will not get you is deep sky: faint nebulae "
                  "and galaxies need longer exposures than a handset will "
                  "give you. When you want those, {route:buying} picks up "
                  "where this one stops.",
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
            (STELLARIUM,
             "Planning with Stellarium",
             "Ten minutes before you go out that tells you what is up, how "
             "high it climbs, and whether it will fit your lens."),
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
                  "that quietly decides how clean the final picture looks. "
                  "The camera and tripod you already have are also all a "
                  "{article:" + METEORS + "|meteor shower} needs.",
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
            (STELLARIUM,
             "Planning with Stellarium",
             "Choosing the target and the night before the box comes out, "
             "including whether the target fits the Seestar's frame."),
            ("siril-post-processing-guide",
             "Finishing the Image in Siril",
             "The free route from the box's output to a picture worth "
             "printing, and the one rule about stretching."),
        ],
        "ending": "Shooting from a balcony? "
                  "{article:imaging-from-a-city-balcony|Imaging from a city "
                  "balcony} covers working with half the sky and half the "
                  "night. When you want more aperture than 30mm can give "
                  "you, {route:rig} is where that leads.",
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
            (STELLARIUM,
             "Planning with Stellarium",
             "Your own telescope and camera drawn onto the sky, so you know "
             "which focal length suits a target before you set anything up."),
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


# ----------------------------------------------------------------- 3. PLAN

PLAN_TITLE = "What is up from where you are"
PLAN_TEXT = ("Drop a pin where you will be observing from, and the tonight "
             "page works out when it gets properly dark, what the moon is "
             "doing, which objects are worth setting up for, and when the "
             "next meteor shower peaks.")
PLAN_LINK = "Open the tonight page"

# Carries inline markup, so this one is not escaped.
VETERAN = ('Already shooting? You probably want '
           '<a href="/gallery.html">the gallery</a> or '
           '<a href="/gear.html">the gear list</a> instead. Every article '
           'lives on <a href="/articles.html">the articles page</a>, newest '
           'first, or <a href="/articles.html?order=reading">in reading '
           'order</a> from planning the night to finishing the image.')


# ------------------------------------------------------------------ build

class BuildError(Exception):
    """A missing slug is worth failing the build for. A card that silently
    vanishes is far harder to notice than a red cross in Actions."""


def load_articles():
    with open(DATA, "r", encoding="utf-8") as f:
        items = json.load(f)
    articles = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("slug")
        if slug and not entry.get("hidden") and entry.get("section") == "article":
            articles[slug] = entry
    return articles


def article_url(slug):
    return f"/{ARTICLE_DIR}/{slug}.html"


def tokens(text, articles):
    """Expand {route:}, {article:}, {url:} and {ext:} inside escaped copy.

    The prose is escaped first and the markup spliced in afterwards, so the
    copy above stays plain text and an ampersand in a sentence cannot break
    the page. A brace that is not a known token is left alone.
    """
    out = ""
    rest = esc(text)
    while "{" in rest:
        before, brace, after = rest.partition("{")
        kind, colon, tail = after.partition(":")
        if (kind not in ("route", "article", "url", "ext")
                or not colon or "}" not in tail):
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
            continue

        target, _, label = body.partition("|")
        label = label or target
        if kind == "article":
            if target not in articles:
                raise BuildError(f"unknown article slug '{target}' in copy")
            out += f'<a href="{esc(article_url(target))}">{label}</a>'
        elif kind == "ext":
            out += (f'<a href="{target}" target="_blank" '
                    f'rel="noopener noreferrer">{label}</a>')
        else:
            href = target if target.startswith("/") else "/" + target
            out += f'<a href="{href}">{label}</a>'
    return out + rest


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
    the free steps rather than a wall of choices."""
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


def build_plan():
    return (
        '      <section class="sh-plan">\n'
        f'        <h2>{esc(PLAN_TITLE)}</h2>\n'
        f'        <p>{esc(PLAN_TEXT)}</p>\n'
        f'        <a class="btn sh-plan-link" href="/tonight.html">'
        f'{esc(PLAN_LINK)}</a>\n'
        '      </section>\n'
    )


def route_slugs():
    """Every article slug on a route, in page order, without repeats."""
    seen, order = set(), []
    for route in ROUTES:
        for slug, _, _ in route["cards"]:
            if slug not in seen:
                seen.add(slug)
                order.append(slug)
    return order


def linked_slugs():
    """Slugs reached through {article:} tokens in any copy on the page."""
    copy = [body for _, body in TONIGHT_STEPS]
    for route in ROUTES:
        copy += [route.get("lede", ""), route.get("ending", "")]
    return set(re.findall(r"\{article:([^|}]+)", " ".join(copy)))


def build_json_ld(articles):
    """An ItemList of the articles on the routes, in page order, so the
    reading lists stay legible to a crawler even though the markup keeps
    them collapsed until a pill is tapped."""
    elements = [
        {
            "@type": "ListItem",
            "position": i,
            "url": f"{DOMAIN}{article_url(slug)}",
            "name": articles[slug].get("title", ""),
        }
        for i, slug in enumerate(route_slugs(), start=1)
    ]
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Start Here: reading routes into astrophotography",
        "description": PAGE_DESC,
        "url": f"{DOMAIN}/{OUT}",
        "numberOfItems": len(elements),
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

  // Scroll the chooser to just below the sticky header. scrollIntoView
  // would tuck the question underneath the nav, and the header's height
  // changes as the nav wraps, so it is measured each time. The position
  // comes from offsetTop rather than getBoundingClientRect, because the
  // scroll reveal in partials.js holds the section 18px low while it fades
  // in, and measuring during that would stop the scroll short.
  function toChooser(smooth) {
    var header = document.querySelector('header');
    var offset = (header ? header.getBoundingClientRect().height : 0) + 16;
    var y = 0;
    for (var el = chooser; el; el = el.offsetParent) y += el.offsetTop;
    window.scrollTo({
      top: Math.max(0, y - offset),
      behavior: smooth && !still ? 'smooth' : 'auto'
    });
  }

  // "the full rig route" inside a closing line.
  document.addEventListener('click', function (ev) {
    var jump = ev.target.closest && ev.target.closest('.sh-goto');
    if (!jump) return;
    apply(jump.getAttribute('data-goto'), true);
    toChooser(true);
  });

  // Remember the route a card was opened from, so the article page can say
  // where the reader is in it and link straight to the next one. Written on
  // click, which fires before the page unloads, and on middle click. The
  // article page only acts on this when the reader arrived from here or
  // from another article on the same route, so a stale trail does nothing.
  var TRAIL = 'bhapstar:routeTrail';

  function slugOf(href) {
    return (href || '').split('/').pop().replace(/\\.html$/, '');
  }

  function saveTrail(ev) {
    var card = ev.target.closest && ev.target.closest('.sh-route-block .sh-card');
    if (!card) return;
    var block = card.closest('.sh-route-block');
    var head = block.querySelector('.sh-route-head');
    var cards = Array.prototype.slice.call(block.querySelectorAll('.sh-card'))
      .map(function (c) {
        var t = c.querySelector('.sh-title');
        return { slug: slugOf(c.getAttribute('href')),
                 title: t ? t.textContent : '' };
      });
    try {
      sessionStorage.setItem(TRAIL, JSON.stringify({
        key: block.getAttribute('data-block'),
        heading: head ? head.textContent : '',
        cards: cards
      }));
    } catch (e) {}
  }
  document.addEventListener('click', saveTrail);
  document.addEventListener('auxclick', saveTrail);

  var saved = null;
  try { saved = sessionStorage.getItem(KEY); } catch (e) {}
  var valid = pills.some(function (p) {
    return p.getAttribute('data-route') === saved;
  });

  // First paint, no animation. With nothing saved this collapses every
  // route, so the page opens on the free steps.
  commit(saved && valid ? saved : 'none');

  // Arriving from an article's "back to the route" link. The route is
  // already open from sessionStorage above, so bring it into view. The
  // header is injected by partials.js after this runs, so wait for it
  // first, or the scroll lands short by the height of the nav.
  if (location.hash === '#routes' && saved && valid) {
    var tries = 0;
    (function waitForHeader() {
      if (document.querySelector('header') || ++tries > 60) {
        requestAnimationFrame(function () { toChooser(false); });
      } else {
        setTimeout(waitForHeader, 50);
      }
    })();
  }
})();
"""


def build_page(articles):
    page_url = f"{DOMAIN}/{OUT}"
    share_url = f"{DOMAIN}/{SHARE_IMAGE}"
    return f'''<!doctype html>
<!-- Generated by scripts/generate-start-here.py. Do not edit this file by
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
  <!-- Page CSS lives in /styles.css under "PAGE: Start Here". -->

  <script type="application/ld+json">
{build_json_ld(articles)}
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

{build_tonight(articles)}
{build_chooser()}
{build_routes(articles)}
{build_plan()}
      <p class="sh-veteran">{VETERAN}</p>

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
    try:
        articles = load_articles()
        html = build_page(articles)
    except BuildError as exc:
        print(f"✗ {OUT}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ {OUT}  ({len(ROUTES)} routes, "
          f"{len(route_slugs())} articles on them)")

    # An article that is live but on no route card and linked from no copy
    # is almost always an oversight rather than a decision. It is still
    # on articles.html either way.
    reached = set(route_slugs()) | linked_slugs()
    for slug in sorted(articles):
        if slug not in reached:
            print(f"  ! '{slug}' appears nowhere on this page")


if __name__ == "__main__":
    main()
