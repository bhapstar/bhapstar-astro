#!/usr/bin/env python3
"""
make-meteor-shower-card.py — the printable crib sheet for meteor showers
-------------------------------------------------------------------------
One side of A4, meant to live in the glovebox and come out twice a year.
Content follows /articles/photograph-a-meteor-shower.html.

This card exists because meteors belong to the calendar rather than to a
device: the two Milky Way cards cover the settings for a phone and a camera,
and this one covers which nights to be out on and which way to point. The
radiant diagram is drawn with flat fills and hairlines so it survives a mono
laser printer.

    python3 make-meteor-shower-card.py
"""

import math

from fieldcard import (Card, register_fonts, MARGIN, PW, CONTENT,
                       INK, BODY, MUTED, VIOLET, BLUE, PINK, LINE,
                       SOFT_V, SOFT_B, F_REG, F_SEMI, F_BOLD, sw, wrap)

OUT = 'meteor-shower-field-card.pdf'
URL = ('https://bhapstar.com/articles/'
       'photograph-a-meteor-shower.html?src=pdf-meteors')

register_fonts()

card = Card(OUT,
            'Photographing a meteor shower: field card',
            'Printable crib sheet for the annual meteor showers: peak dates, '
            'expected rates, where to point a camera and what to set')
c = card.c

y = card.header('Photographing a meteor shower',
                'Print it, fold it, take it out with you.')

# ── the whole idea, before anything else ───────────────────────────────
y = card.callout(
    MARGIN, y, CONTENT,
    'The whole thing in one paragraph',
    'You do not chase meteors. A meteor lasts a fraction of a second, so the '
    'only thing that decides whether you catch one is how much of the night '
    'your shutter was open. Point at a good patch of sky, set the camera or '
    'the phone running, and take hundreds of frames. Every one of them is also '
    'a Milky Way exposure, so a quiet night is never a wasted one.')

# ── the showers ────────────────────────────────────────────────────────
y = card.section(MARGIN, y - 14, CONTENT, 'The showers worth planning around')

COLS = [
    (0,   64,  'label'),
    (72,  82,  'value'),
    (162, 92,  'value'),
    (262, 265, 'note'),
]
HEAD = ['Shower', 'Peak', 'Rough rate at a dark site', 'Worth knowing']

ROWS = [
    ('Quadrantids', '3 to 4 January', '25 to 50 an hour',
     'The peak is very short, often only a few hours. Get the night right or '
     'miss it entirely'),
    ('Lyrids', '22 to 23 April', '10 to 20 an hour',
     'Modest, but it breaks the long gap between January and August'),
    ('Eta Aquariids', '5 to 6 May', '20 to 40 an hour',
     'Dust from Halley\u2019s Comet. Fast, and best in the hours before dawn'),
    ('Perseids', '12 to 13 August', '50 to 80 an hour',
     'Warm nights and a high radiant make this the easiest one to sit through'),
    ('Orionids', '21 to 22 October', '10 to 20 an hour',
     'Halley\u2019s Comet again, from the other side of its orbit'),
    ('Leonids', '17 to 18 November', '10 to 15 an hour',
     'Quiet most years, with occasional storms decades apart'),
    ('Geminids', '13 to 14 December', '60 to 100 an hour',
     'The best of the year. Bright, slow, and coming from an asteroid rather '
     'than a comet'),
    ('Ursids', '22 to 23 December', '5 to 10 an hour',
     'Small, and easy to combine with the Geminids the week before'),
]

y = card.table(MARGIN, y - 2, COLS, ROWS, head=HEAD, total=CONTENT)
y = card.para(MARGIN, y - 10, CONTENT,
              'Those rates are what a patient person sees by eye at a genuinely '
              'dark site, with the radiant high and the moon out of the way. '
              'Published figures are often higher because they describe an '
              'idealised sky. Your camera will record fewer than your eyes do, '
              'because it only looks at one part of the sky at a time.',
              F_REG, 6.8, 8.0, MUTED)

# ── two columns: the diagram, and what to set ──────────────────────────
LEFT_W = 300.0
GUTTER = 15.0
RIGHT_X = MARGIN + LEFT_W + GUTTER
RIGHT_W = CONTENT - LEFT_W - GUTTER

col_top = y - 12
ly = card.section(MARGIN, col_top, LEFT_W, 'Point away from the radiant')

# ── the diagram ────────────────────────────────────────────────────────
# Same idea as the article's figure: a horizon with compass ticks, the
# radiant climbing through the night, meteors streaming away from it, and the
# stretch of sky worth framing marked out.
DW, DH = LEFT_W, 132.0
dx0 = MARGIN
dtop = ly + 2
horizon = dtop - DH + 22

# the stretch worth pointing at
c.setFillColor(SOFT_V)
c.setStrokeColor(VIOLET)
c.setLineWidth(0.8)
c.roundRect(dx0 + 158, horizon + 12, 142, DH - 46, 4, stroke=1, fill=1)
card.text(dx0 + 229, dtop - 22, 'point the camera here', F_SEMI, 7.4, VIOLET,
          'centre')
card.text(dx0 + 229, dtop - 31, '40 to 60\u00b0 from the radiant, and high up',
          F_REG, 6.2, MUTED, 'centre')

# altitude guides
c.setStrokeColor(LINE)
c.setLineWidth(0.6)
for alt, yy in (('60\u00b0', horizon + 74), ('30\u00b0', horizon + 38)):
    c.line(dx0 + 4, yy, dx0 + 152, yy)
    card.text(dx0 + 6, yy + 3, alt, F_REG, 5.8, MUTED)

# horizon and compass
c.setStrokeColor(INK)
c.setLineWidth(1.1)
c.line(dx0, horizon, dx0 + DW, horizon)
for i, pt in enumerate(('N', 'NE', 'E', 'SE', 'S', 'SW')):
    px = dx0 + 12 + i * (DW - 24) / 5.0
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(px, horizon, px, horizon - 3.5)
    card.text(px, horizon - 12, pt, F_REG, 6.2, MUTED, 'centre')

# the radiant climbing through the night
c.setStrokeColor(PINK)
c.setLineWidth(0.9)
p = c.beginPath()
p.moveTo(dx0 + 40, horizon + 14)
p.curveTo(dx0 + 56, horizon + 34, dx0 + 68, horizon + 62, dx0 + 86, horizon + 92)
c.drawPath(p, stroke=1, fill=0)
c.setFillColor(PINK)
for px, py, r in ((40, 14, 1.9), (62, 46, 2.3), (86, 92, 3.0)):
    c.circle(dx0 + px, horizon + py, r, stroke=0, fill=1)
card.text(dx0 + 46, horizon + 10, 'early, low', F_REG, 5.8, PINK)
card.text(dx0 + 68, horizon + 43, 'later', F_REG, 5.8, PINK)
card.text(dx0 + 93, horizon + 89, 'small hours, best rates', F_REG, 5.8, PINK)
card.text(dx0 + 86, horizon + 100, 'the radiant', F_SEMI, 6.4, INK, 'centre')

# meteors streaming away from it
c.setStrokeColor(BODY)
c.setLineCap(1)
# The box caption occupies the top of the panel, so every stroke inside it
# stays below horizon+50, which clears the second caption line by a good
# margin. One stroke sits outside, between the radiant and the panel.
for x1, y1, x2, y2, w in ((118, 44, 148, 31, 0.9), (164, 50, 206, 35, 1.4),
                          (198, 35, 232, 22, 0.9), (244, 48, 284, 33, 1.1),
                          (220, 20, 252, 13, 0.8), (262, 30, 294, 17, 0.9)):
    c.setLineWidth(w)
    c.line(dx0 + x1, horizon + y1, dx0 + x2, horizon + y2)
c.setLineCap(0)

ly = horizon - 22
ly = card.para(MARGIN, ly, LEFT_W,
               'Meteors near the radiant are travelling towards you and appear '
               'as short stubs. The long, photogenic ones are always well off '
               'to the side. Anywhere high and dark works, so use that freedom '
               'to pick the direction with the least streetlight and the best '
               'foreground.', F_REG, 6.8, 8.0, MUTED)

# ── right column ───────────────────────────────────────────────────────
ry = card.section(RIGHT_X, col_top, RIGHT_W, 'Check the moon first', BLUE)
ry = card.para(RIGHT_X, ry, RIGHT_W,
               'This is the step that decides the night. A bright moon washes '
               'the sky out exactly the way a city does, and hides most of the '
               'fainter meteors. A shower peaking two days after full moon is '
               'worth skipping. A shower on a bright night is often still worth '
               'shooting in the window after the moon has set, even if that '
               'window starts at three in the morning.',
               F_REG, 7.2, 8.8, BODY)

ry = card.section(RIGHT_X, ry - 9, RIGHT_W, 'Stay late', PINK)
ry = card.para(RIGHT_X, ry, RIGHT_W,
               'Rates almost always build through the night. Early on the '
               'radiant is still low and much of the shower is happening below '
               'the horizon. By the small hours the Earth has turned to face '
               'into the stream. If you can only be out for part of the night, '
               'arrive late rather than leaving early.',
               F_REG, 7.2, 8.8, BODY)

ry = card.section(RIGHT_X, ry - 9, RIGHT_W, 'What to set', VIOLET)
SETTINGS = [
    ('Camera', 'Manual, RAW, lowest f-number, ISO 3200 at a dark site, 15 to '
               '20 seconds on a wide lens. Lock the intervalometer on.'),
    ('Phone', 'Night mode on a tripod, or Pro mode at ISO 3200 and 20 seconds, '
              'fired again and again.'),
    ('Either', 'Shorten any long night mode. A meteor in a four minute frame is '
               'swamped by four minutes of skyglow; the same meteor in a 20 '
               'second frame stands out sharply.'),
]
for label, body in SETTINGS:
    card.text(RIGHT_X, ry, label, F_SEMI, 7.2, INK)
    ry -= 8.8
    ry = card.para(RIGHT_X, ry, RIGHT_W, body, F_REG, 6.8, 8.0, MUTED)
    ry -= 3.4

y = min(ly, ry)

# ── the bottom row ─────────────────────────────────────────────────────
y = card.section(MARGIN, y - 8, CONTENT, 'On the night, and afterwards')

CARD_W = (CONTENT - 2 * 12) / 3.0
y3 = y + 2
row = [
    card.note_card(MARGIN, y3, CARD_W, 'Take more frames than feels sensible',
                   'One exposure is a lottery ticket. Thirty is a fair chance. '
                   'A few hundred, across two or three hours, is how people '
                   'come home with the shot. Expect most frames to hold '
                   'nothing, which is completely normal.', VIOLET),
    card.note_card(MARGIN + CARD_W + 12, y3, CARD_W, 'What decides the night',
                   'More power than you think, because cold drains batteries '
                   'fast. Card space: three hours of 20 second frames is around '
                   '500 files. Check the front of the lens every half hour for '
                   'dew. Dress for two hours longer than you plan to stay.',
                   BLUE),
    card.note_card(MARGIN + 2 * (CARD_W + 12), y3, CARD_W, 'Three pictures after',
                   'Pick the best single meteor frame and process it alone. '
                   'Combine several meteors onto one sky, which is fine as long '
                   'as you say so. Average or stack the whole run for a clean '
                   'Milky Way or a star trail.', PINK),
]

card.footer(
    'The full guide, with examples',
    'Full walkthrough with example images, the radiant explained properly, and '
    'the separate phone and camera cards with the complete settings for each.',
    URL)

card.save()
print('wrote', OUT, 'lowest card bottom:', round(min(row), 1))
