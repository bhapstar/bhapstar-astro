#!/usr/bin/env python3
"""
glossary.py — shared by generate-article-pages.py and generate-gear-pages.py
-------------------------------------------------------------
Marks the first mention of each technical word in a page body and attaches a
plain-English explainer: hover on a desktop, tap on a phone, Enter or Space on
a keyboard.

The words themselves live in content/glossary.json, with the rest of the
hand-written content. Nothing is marked by hand, so the prose fragments in content/articles/ and
content/gear/ stay clean, and a definition is written once rather than once
per page. Add a term to the JSON, run python build.py, and every page that
uses the word picks it up.

Used from a generator like this:

    from glossary import (load_glossary, annotate_glossary,
                          GLOSSARY_CSS, GLOSSARY_JS)

    glossary = load_glossary()                  # once, in main()
    body, n = annotate_glossary(body, slug, glossary)
    css = GLOSSARY_CSS if n else ''             # a page with no marked words
    js  = GLOSSARY_JS  if n else ''             # carries neither

Both generators are run with the repository root as their working directory,
which is how content/glossary.json is found.

The escaping helper is deliberately local rather than imported from either
generator: this module has to work the same way whichever one loads it.
"""

import json
import os
import re
from html import escape as _escape
from html.parser import HTMLParser

# content/, with the article and gear prose, because the definitions are
# hand-written content rather than code. Resolved against the repository root,
# which is the working directory both generators are run from (build.py sets
# it, and so does running a generator by hand from the root).
GLOSSARY_FILE = os.path.join('content', 'glossary.json')


def esc(s):
    """Escape for HTML attribute/text context."""
    return _escape(str(s or ''), quote=True)


# ---------------------------------------------------------------------------
# Which regions of a page are searched
#
# The words a beginner trips over are marked automatically rather than by hand,
# so the prose fragments in content/articles/ stay readable and a definition is
# written once instead of once per article. Only the FIRST occurrence in each
# article is marked: past that the reader has met the word.
#
# The matcher walks real text nodes, never the raw string, so it cannot damage
# a tag or an attribute. Whole regions are skipped:
#
#   a         a term inside a link would need an <a> inside an <a>, which is
#             invalid HTML, and the link already leads to the explanation
#   svg       the hand-drawn diagrams: their <text> labels are positioned to
#             the pixel and an inserted <span> would shift them
#   headings  a dotted underline in a heading reads as damage, not as help
#   code/pre  those are literal strings
# ---------------------------------------------------------------------------
GLOSS_SKIP_TAGS = {'a', 'svg', 'code', 'pre', 'script', 'style',
                   'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

# Tags that never have a closing partner, so they must not go on the stack.
GLOSS_VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                   'link', 'meta', 'param', 'source', 'track', 'wbr'}


def load_glossary():
    """Read the JSON into a list of terms, each with its forms compiled.

    Shape of each item:

        {'term': 'reducer', 'def': '...', 'except': {...},
         'res': [<compiled 'reducers'>, <compiled 'reducer'>]}

    Two different orderings are at work here and mixing them up is the easy
    mistake:

      - BETWEEN terms, longest first, so 'dual narrowband' claims its span
        before plain 'narrowband' can, and 'meridian flip' before 'meridian'.
        A term is ranked on its longest form.
      - WITHIN a term, no ordering at all. Every form is searched and the
        EARLIEST match in the page wins. Rank the forms by length instead and
        'reducers' beats 'reducer', so a plural three paragraphs down gets the
        explainer while the plain singular in the opening sentence goes bare.

    Missing file is not an error: pages simply build without explainers.
    """
    if not os.path.isfile(GLOSSARY_FILE):
        print(f"  ! {GLOSSARY_FILE} not found, no glossary terms marked")
        return []

    with open(GLOSSARY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    terms = []
    for item in data.get('terms', []):
        term = (item.get('term') or '').strip()
        definition = (item.get('def') or '').strip()
        if not term or not definition:
            continue
        forms = [term] + [a for a in item.get('aliases', []) if a]
        terms.append({
            'term': term,
            'def': definition,
            'except': set(item.get('except', [])),
            # Phrases the word must not be marked inside. 'triplet' is a lens
            # made of three elements, and it is also the second half of 'Leo
            # Triplet', a group of galaxies. An except list cannot separate
            # those two: they turn up on the same page.
            'avoid': [re.compile(r'(?<![\w/-])' + re.escape(a).replace(r'\ ', r'\s+')
                                 + r'(?![\w/-])', re.IGNORECASE)
                      for a in item.get('avoid', [])],
            'forms': forms,
            'res': [_compile_form(f) for f in forms],
            'rank': max(len(f) for f in forms),
        })

    # Longest first, so 'dual narrowband' claims its span before plain
    # 'narrowband' can. The term name is a tiebreak purely so the ordering is
    # decided by content and never by position in the file: that leaves the
    # JSON free to be kept in alphabetical order for editing, with no risk of
    # rearranging it quietly changing which word gets marked on a page.
    terms.sort(key=lambda t: (-t['rank'], t['term'].lower()))
    return terms


def _compile_form(form):
    """Compile one spelling of a term into a matcher.

    A form written with a capital in it is an acronym or a name, and is
    matched case-sensitively: otherwise FITS catches the verb 'fits' and RAW
    catches 'a raw dark'. An all-lowercase form is matched either way, so it
    is still found at the start of a sentence.

    \\b is wrong here: it treats a hyphen as a boundary, so 'deep sky' would
    match inside 'deep-sky-object' and 'APO' inside 'APO-chromat'. Look-arounds
    on the word characters plus hyphen and slash are exact. The escaped space
    becomes \\s+ so a term split over two lines in the source still matches.
    """
    flags = 0 if any(c.isupper() for c in form) else re.IGNORECASE
    return re.compile(r'(?<![\w/-])'
                      + re.escape(form).replace(r'\ ', r'\s+')
                      + r'(?![\w/-])', flags)


class _TextNodeFinder(HTMLParser):
    """Records the byte span of every text node, and the tags enclosing it.

    convert_charrefs is off so that data arrives exactly as written in the
    file: with it on, entities are decoded and adjacent runs are merged, and
    the offsets stop lining up with the source.
    """

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        # Start offset of each line, so getpos() can be turned into an index.
        self.line_starts = [0]
        for line in source.splitlines(keepends=True):
            self.line_starts.append(self.line_starts[-1] + len(line))
        self.stack = []
        self.spans = []          # (start, end) of text nodes worth searching

    def _offset(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag not in GLOSS_VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if not data.strip():
            return
        if any(t in GLOSS_SKIP_TAGS for t in self.stack):
            return
        start = self._offset()
        self.spans.append((start, start + len(data)))


def annotate_glossary(body_html, slug, glossary):
    """Mark the first mention of each glossary term in one page body.

    Returns (html, count). Replacements are applied back to front so that every
    offset gathered from the original string stays valid.
    """
    if not glossary or not body_html:
        return body_html, 0

    finder = _TextNodeFinder(body_html)
    try:
        finder.feed(body_html)
        finder.close()
    except Exception as exc:                       # pragma: no cover
        # A malformed fragment should cost the explainers, not the page.
        print(f"  ! {slug}: could not parse for glossary ({exc})")
        return body_html, 0

    edits = []          # (start, end, term, definition)
    claimed = []        # spans already taken, so two terms cannot overlap

    def free(a, b):
        return not any(a < cb and ca < b for ca, cb in claimed)

    def blocked(entry, a, b):
        """True if this match sits inside one of the term's avoid phrases."""
        for rx in entry['avoid']:
            # Only the immediate neighbourhood can contain the phrase.
            lo = max(0, a - 60)
            for m in rx.finditer(body_html, lo, b + 60):
                if m.start() <= a and m.end() >= b:
                    return True
        return False

    for entry in glossary:
        if slug in entry['except']:
            continue

        # Earliest match anywhere in the page, across every spelling of this
        # term. Searching form by form and stopping at the first hit would
        # let a plural late in the page beat the singular in the opening line.
        best = None
        for start, end in finder.spans:
            for rx in entry['res']:
                pos = start
                while pos < end:
                    m = rx.search(body_html, pos, end)
                    if not m:
                        break
                    a, b = m.span()
                    if free(a, b) and not blocked(entry, a, b):
                        if best is None or a < best[0]:
                            best = (a, b)
                        break
                    # Overlaps something already marked, or sits inside a
                    # proper name. Keep looking further along THIS text node
                    # rather than abandoning it: the next sentence may hold a
                    # clean occurrence.
                    pos = b
            if best is not None and best[0] < start:
                break               # nothing later can beat this
        if best is None:
            continue

        a, b = best
        edits.append((a, b, entry['term'], entry['def']))
        claimed.append((a, b))

    if not edits:
        return body_html, 0

    # Numbered in reading order, so the ids on the page run top to bottom.
    edits.sort(key=lambda e: e[0])
    out = body_html
    for idx, (a, b, term, definition) in reversed(list(enumerate(edits, 1))):
        ref = f"gl-{slug}-{idx}"
        out = out[:a] + (
            f'<span class="gl" role="button" tabindex="0" '
            f'aria-describedby="{ref}" data-gl-term="{esc(term)}">'
            f'{out[a:b]}</span>'
            f'<span class="gl-def" id="{ref}" hidden>{esc(definition)}</span>'
        ) + out[b:]
    return out, len(edits)


GLOSSARY_CSS = """
    /* ── Glossary explainers ──
       The marked word is a <span role="button">, not a <button>, for one
       practical reason: a real button is an inline-block and will not break
       across a line, so a two word term at the end of a line pushes itself
       whole onto the next one and leaves a gap. A span wraps like the prose
       around it and behaves as a button for the keyboard and screen readers.

       Dotted rather than solid, and no accent colour on the text itself, so
       it cannot be mistaken for a link: links here are solid-underlined and
       coloured, and the two must not look alike. */
    .gl { cursor: help; border-bottom: 1px dotted rgba(var(--accent-rgb),0.75);
          transition: background 180ms ease, border-color 180ms ease; }
    .gl:hover, .gl:focus-visible, .gl.gl-on {
          background: rgba(var(--accent-rgb),0.14);
          border-bottom-color: var(--accent); border-radius: 3px; }
    .gl:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
    /* On a touch screen there is no hover to hint with, so the word has to
       look tappable while sitting still. */
    @media (hover: none) {
      .gl { border-bottom-width: 2px; background: rgba(var(--accent-rgb),0.10);
            border-radius: 3px; padding: 0 2px; }
    }
    /* Definitions live in the page rather than in an attribute, so a screen
       reader can reach them and they are in the HTML a crawler sees. Hidden
       from view: the panel takes its text from here. */
    .gl-def { display: none; }

    .gl-pop { position: fixed; z-index: 9998; width: 300px;
              max-width: calc(100vw - 24px); padding: 13px 15px;
              border-radius: 12px; border: 1px solid var(--line);
              /* --soft is a 7% tint. That is correct for a block sitting in
                 the page flow, and useless for a panel floating over text,
                 which shows straight through it. The tint is applied as a
                 gradient layer over an opaque base instead, so the panel
                 looks the same as the rest of the site and is solid. */
              background: linear-gradient(rgba(var(--accent-rgb),0.07),
                                          rgba(var(--accent-rgb),0.07)),
                          var(--bg2);
              box-shadow: 0 14px 40px rgba(0,0,0,0.45);
              opacity: 0; transform: translateY(-4px); pointer-events: none;
              transition: opacity 160ms ease, transform 160ms ease; }
    html[data-theme="light"] .gl-pop {
              box-shadow: 0 12px 30px rgba(0,0,0,0.20); }
    .gl-pop.open { opacity: 1; transform: translateY(0); pointer-events: auto; }
    .gl-pop-term { font-size: 10.5px; letter-spacing: 0.16em;
                   text-transform: uppercase; color: var(--accent);
                   margin: 0 0 6px; padding-right: 18px; }
    .gl-pop-def { font-size: 13.5px; line-height: 1.6; color: var(--text);
                  margin: 0; }
    .gl-pop-close { position: absolute; top: 7px; right: 8px; display: none;
                    width: 26px; height: 26px; padding: 0; border: 0;
                    border-radius: 50%; background: transparent; cursor: pointer;
                    color: var(--muted); font-size: 17px; line-height: 26px; }
    /* Nothing to hover away from on touch, so give it a way out. */
    @media (hover: none) { .gl-pop-close { display: block; } }
"""

# The panel is one element reused by every term, so a page with forty marked
# words still carries one node and one set of listeners.
GLOSSARY_JS = """
  <script>
  (function () {
    var terms = document.querySelectorAll('.gl');
    if (!terms.length) return;

    var pop = document.createElement('div');
    pop.className = 'gl-pop';
    pop.setAttribute('role', 'tooltip');
    var head = document.createElement('p');
    head.className = 'gl-pop-term';
    var body = document.createElement('p');
    body.className = 'gl-pop-def';
    var shut = document.createElement('button');
    shut.className = 'gl-pop-close';
    shut.type = 'button';
    shut.setAttribute('aria-label', 'Close');
    shut.innerHTML = '&#215;';
    pop.appendChild(head);
    pop.appendChild(body);
    pop.appendChild(shut);
    document.body.appendChild(pop);

    var current = null;   // the word the panel is describing
    var pinned = false;   // opened by tap or click, so hovering away leaves it
    var hideTimer = null;

    function place() {
      if (!current) return;
      var r = current.getBoundingClientRect();
      var w = pop.offsetWidth, h = pop.offsetHeight;
      var margin = 12, gap = 10;
      var left = r.left + r.width / 2 - w / 2;
      left = Math.max(margin, Math.min(left, window.innerWidth - w - margin));
      // Below by default. Above only if it would otherwise run off the
      // bottom and there is genuinely more room up top.
      var top = r.bottom + gap;
      if (top + h > window.innerHeight - margin && r.top - gap - h > margin) {
        top = r.top - gap - h;
      }
      top = Math.max(margin, Math.min(top, window.innerHeight - h - margin));
      pop.style.left = left + 'px';
      pop.style.top = top + 'px';
    }

    function show(el, sticky) {
      clearTimeout(hideTimer);
      var def = document.getElementById(el.getAttribute('aria-describedby'));
      if (!def) return;
      if (current && current !== el) current.classList.remove('gl-on');
      current = el;
      pinned = !!sticky;
      head.textContent = el.getAttribute('data-gl-term') || '';
      body.textContent = def.textContent;
      el.classList.add('gl-on');
      pop.classList.add('open');
      place();
    }

    function hide() {
      clearTimeout(hideTimer);
      if (current) current.classList.remove('gl-on');
      current = null;
      pinned = false;
      pop.classList.remove('open');
    }

    for (var i = 0; i < terms.length; i++) {
      (function (el) {
        el.addEventListener('mouseenter', function () {
          if (!pinned) show(el, false);
        });
        el.addEventListener('mouseleave', function () {
          if (pinned) return;
          // A short grace period, so moving the pointer down into the panel
          // to read a long definition does not dismiss it on the way.
          hideTimer = setTimeout(hide, 140);
        });
        el.addEventListener('click', function (e) {
          e.stopPropagation();
          if (current === el && pinned) { hide(); return; }
          show(el, true);
        });
        el.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
            e.preventDefault();
            if (current === el && pinned) { hide(); } else { show(el, true); }
          }
        });
        el.addEventListener('focus', function () { show(el, false); });
        el.addEventListener('blur', function () { if (!pinned) hide(); });
      })(terms[i]);
    }

    pop.addEventListener('mouseenter', function () { clearTimeout(hideTimer); });
    pop.addEventListener('mouseleave', function () { if (!pinned) hide(); });
    pop.addEventListener('click', function (e) { e.stopPropagation(); });
    shut.addEventListener('click', hide);

    document.addEventListener('click', function () { if (pinned) hide(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') hide();
    });
    // Follow the word rather than float over the page while it scrolls away.
    window.addEventListener('scroll', function () {
      if (current) place();
    }, { passive: true });
    window.addEventListener('resize', function () {
      if (current) place();
    });
  })();
  </script>
"""
