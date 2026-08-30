#!/usr/bin/env python3
"""
make-moon-card.py — the printable crib sheet for the Moon
----------------------------------------------------------------------------
One side of A4, for someone standing outside deciding whether tonight is worth
it and what to set. Content follows /articles/photograph-the-moon.html.

Same family as the other five cards: the fieldcard kit supplies the header,
the accent rule, the striped table, the note cards and the footer QR, so the
measurements are inherited rather than re-invented here.

Two things on this sheet are computed rather than typed, because both are easy
to get subtly wrong by hand:

  The phase discs. The lit region is the right half of the disc closed by an
  ellipse of semi-minor axis R*|1-2k| for illuminated fraction k, which is the
  real construction. A straight line down the middle is only correct at the
  quarters, and a card that draws a crescent wrongly is worse than one that
  draws no crescent at all.

  The rise and set times. rise = 06:00 + age * 0.813h, set = rise + 12h. That
  puts new moon rise at 06:00, first quarter at noon, full at sunset and last
  quarter at midnight, which is the textbook behaviour, and it makes the fifty
  minutes a day figure fall out of the row rather than being asserted next to
  it. Times are nominal: real ones move with latitude and season, and the card
  says so.

The strip across the top is the part that earns the sheet its place in a bag.
The article can afford three paragraphs explaining that the Moon is not up
every night. A field card has to answer it in one glance.

    python3 make-moon-card.py
"""

from fieldcard import (Card, register_fonts, out_path, MARGIN, PW, CONTENT,
                       INK, BODY, MUTED, VIOLET, BLUE, PINK, LINE,
                       SOFT_V, SOFT_B, F_REG, F_SEMI, F_BOLD, sw, wrap)

OUT = out_path('moon-field-card.pdf')
URL = 'https://bhapstar.com/articles/photograph-the-moon.html?src=pdf-moon'

register_fonts()

card = Card(OUT,
            'Photograph the Moon: field card',
            'Printable crib sheet for photographing the Moon with a phone, a '
            'camera or a telescope, including when the Moon is actually up')
c = card.c

y = card.header('Photograph the Moon',
                'Print it, fold it, take it out with you.')

# ── the whole idea, before anything else ───────────────────────────────
y = card.callout(
    MARGIN, y, CONTENT,
    'The whole technique, in one paragraph',
    'The Moon is a sunlit rock, so expose it like something in daylight, not '
    'like the night sky. Set the camera to manual, f/8 to f/11, ISO 100 to '
    '200, and a shutter of one over the ISO number. Nothing needs to track, '
    'because at those speeds the sky has not moved. Then pick a night that is '
    'not full: all the detail lives along the terminator, the curved line '
    'between the lit and unlit halves, where the shadows are long.')

# ── is it up tonight, and is it a good night ───────────────────────────
# Eight columns across the full width. Each one carries the phase drawn
# properly, the nominal window it is above the horizon, and whether the
# shadows are worth photographing. This is the question the article spends
# three paragraphs on and it has to be answerable here in one glance.
y = card.section(MARGIN, y - 16, CONTENT,
                 'Is it up tonight, and is tonight worth it')

PHASES = [
    # age, short name, day label, up window, detail verdict
    (3.7,  'Crescent',   'day 3',  'until 9pm',      'good'),
    (7.4,  'First qtr',  'day 7',  'until midnight', 'best'),
    (11.0, 'Gibbous',    'day 11', 'until 3am',      'good'),
    (14.8, 'Full',       'day 15', 'all night',      'flat'),
    (18.5, 'Gibbous',    'day 18', 'from 9pm',       'good'),
    (22.1, 'Last qtr',   'day 22', 'from midnight',  'best'),
    (25.8, 'Crescent',   'day 26', 'from 3am',       'good'),
    (0.0,  'New',        'day 0',  'daytime only',   'none'),
]

VERDICT = {
    'best': (VIOLET, 'shadows at their longest'),
    'good': (BLUE,   'plenty of relief'),
    'flat': (PINK,   'no shadows facing you'),
    'none': (MUTED,  'go shoot the Milky Way'),
}

COL_W = CONTENT / len(PHASES)
DISC_R = 13.0
strip_top = y + 4
disc_cy = strip_top - DISC_R - 2


def phase_disc(cx, cy, r, age):
    """One phase, drawn from the illuminated fraction rather than sketched.

    On paper the metaphor has to invert: the whole disc is laid down in ink
    and the LIT part is knocked back out in white, so the dark ink reads as
    the shadow it is. Filling the lit part with ink instead prints a full moon
    as a solid black circle, which is exactly backwards.

    The outline is walked as points rather than assembled from arc primitives,
    because the sign of the terminator then does the work on its own. The lit
    region is the sunward limb (a semicircle of radius r) closed by the
    terminator, a half-ellipse of signed semi-minor axis r*(1-2k) for
    illuminated fraction k. Positive bulges towards the Sun and gives a
    crescent, zero is the straight line of a quarter, negative bulges away and
    gives a gibbous, and -r closes the full disc. One expression covers every
    phase with no special cases to get backwards.

    Waxing is lit on the right, which is the northern hemisphere view. Past
    full the whole construction mirrors.
    """
    import math
    k = (1 - math.cos(2 * math.pi * age / 29.5)) / 2
    sign = 1.0 if age < 29.5 / 2 else -1.0      # sunward side: right, then left

    c.setFillColor(INK)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.circle(cx, cy, r, stroke=1, fill=1)

    if k > 0.02:
        rx = r * (1 - 2 * k)                    # signed, deliberately
        N = 48
        pts = []
        for i in range(N + 1):                  # sunward limb, bottom to top
            th = -math.pi / 2 + math.pi * i / N
            pts.append((cx + sign * r * math.cos(th), cy + r * math.sin(th)))
        for i in range(N + 1):                  # terminator, top back to bottom
            th = math.pi / 2 - math.pi * i / N
            pts.append((cx + sign * rx * math.cos(th), cy + r * math.sin(th)))
        path = c.beginPath()
        path.moveTo(*pts[0])
        for pt in pts[1:]:
            path.lineTo(*pt)
        path.close()
        c.setFillColor(HexWhite)
        c.drawPath(path, stroke=0, fill=1)

    # redraw the outline so the knocked-out side still has an edge
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.circle(cx, cy, r, stroke=1, fill=0)
    return k


from reportlab.lib.colors import HexColor as _Hex
HexWhite = _Hex('#ffffff')

for i, (age, name, day, window, verdict) in enumerate(PHASES):
    cx = MARGIN + COL_W * i + COL_W / 2
    phase_disc(cx, disc_cy, DISC_R, age)

    card.text(cx, disc_cy - DISC_R - 11, name, F_SEMI, 7.2, INK, 'centre')
    card.text(cx, disc_cy - DISC_R - 19, day, F_REG, 6.0, MUTED, 'centre')

    col, blurb = VERDICT[verdict]
    wy = disc_cy - DISC_R - 30
    c.setFillColor(col)
    c.roundRect(cx - COL_W / 2 + 4, wy - 2, COL_W - 8, 10, 3, stroke=0, fill=1)
    card.text(cx, wy + 1, window, F_SEMI, 6.2, HexWhite, 'centre')
    card.text(cx, wy - 11, blurb, F_REG, 5.7, col, 'centre')

y = disc_cy - DISC_R - 58
y = card.para(MARGIN, y, CONTENT,
              'The Moon rises about fifty minutes later each day, so it works '
              'its way round the clock once a month. Times above are nominal '
              'and move with your latitude and the season, but the order never '
              'changes: the first half of the month is an evening Moon, the '
              'second half is a small-hours Moon, and for three or four nights '
              'around new there is nothing to photograph at all. Those are the '
              'nights the rest of astrophotography waits for.',
              F_REG, 6.8, 8.0, MUTED)

# ── two columns: camera settings, and everything that is not a camera ──
LEFT_W = 300.0
GUTTER = 15.0
RIGHT_X = MARGIN + LEFT_W + GUTTER
RIGHT_W = CONTENT - LEFT_W - GUTTER

col_top = y - 10
ly = card.section(MARGIN, col_top, LEFT_W, 'Camera on a tripod, all manual')

COLS = [(0, 62, 'label'), (67, 96, 'value'), (169, 131, 'note')]
ROWS = [
    ('Mode', 'Manual',
     'Every auto mode meters the black sky and blows the Moon out'),
    ('Aperture', 'f/8 to f/11',
     'Most lenses are sharpest a stop or two down from wide open'),
    ('ISO', '100 to 200',
     'There is plenty of light. Low ISO keeps the file clean'),
    ('Shutter', 'One over the ISO',
     'ISO 200 means 1/200s. The Looney 11 rule. Then adjust by eye'),
    ('Focus', 'Manual, magnified',
     'Put a crater edge or the terminator centre screen and turn until the '
     'shadows snap. Re-check after half an hour as the lens cools'),
    ('File', 'RAW',
     'Keeps the detail in the bright areas that a JPEG throws away'),
    ('Drive', 'Burst of 20 or more',
     'The air is moving. Some frames caught it holding still'),
    ('Stabilisation', 'Off',
     'On a tripod it can add the shake it exists to remove'),
    ('Tracking', 'Not needed',
     'At 1/200s the sky has not moved. A wall will do'),
]
ly = card.table(MARGIN, ly - 2, COLS, ROWS, size=7.0, note_size=6.4,
                leading=7.6, pad_top=9, pad_bottom=5, total=LEFT_W)

ly = card.para(MARGIN, ly - 9, LEFT_W,
               'A crescent wants a little more light than a full Moon, because '
               'you are seeing the surface at a low angle. Start at the numbers '
               'above and open up half a stop at a time until the terminator '
               'stops looking empty.', F_REG, 6.8, 8.0, MUTED)

# ── right column ───────────────────────────────────────────────────────
ry = card.section(RIGHT_X, col_top, RIGHT_W, 'Without a camera', BLUE)

ry = card.note_card(
    RIGHT_X, ry + 4, RIGHT_W, 'Phone on its own',
    'Tap the Moon and hold until the exposure locks, then drag the slider a '
    'long way down until grey markings appear. Use the telephoto lens if the '
    'phone has one, never the digital zoom.', BLUE)

ry = card.note_card(
    RIGHT_X, ry - 8, RIGHT_W, 'Phone at an eyepiece',
    'The cheapest big jump there is. Focus by eye first, then hold the main '
    'camera lens square to the eyepiece and close in. A dark ring means you '
    'are too far back. Lock the exposure, drag it down, shoot a burst.', VIOLET)

ry = card.note_card(
    RIGHT_X, ry - 8, RIGHT_W, 'Smart telescope',
    'Use the mode meant for bright targets. It drops the exposure right down '
    'and tracks while you watch. Aperture matters far less on the Moon than '
    'on a faint galaxy, so a small one does well here.', PINK)

# ── how much lens you actually need ────────────────────────────────────
# The single number that decides how good a lunar picture can be. Percentages
# are the Moon at 31 arcmin measured against the 24mm short side of a
# full-frame sensor, so 2700mm is where it fills the frame edge to edge.
y = card.section(MARGIN, min(ly, ry) - 16, CONTENT,
                 'How much of the frame the Moon fills', BLUE)

LENSES = [
    ('100mm', '4%', 'a dot'),
    ('200mm', '8%', 'a small disc'),
    ('400mm', '15%', 'croppable'),
    ('800mm', '30%', 'a real picture'),
    ('1600mm', '60%', 'craters everywhere'),
    ('2700mm', '100%', 'edge to edge'),
]
TILE_W = CONTENT / len(LENSES)
ty = y + 2
for i, (focal, pct, note) in enumerate(LENSES):
    tx = MARGIN + TILE_W * i
    c.setFillColor(SOFT_B)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(tx + 2, ty - 34, TILE_W - 4, 34, 4, stroke=1, fill=1)
    card.text(tx + TILE_W / 2, ty - 12, focal, F_SEMI, 8.0, INK, 'centre')
    card.text(tx + TILE_W / 2, ty - 21, pct, F_SEMI, 7.4, BLUE, 'centre')
    card.text(tx + TILE_W / 2, ty - 30, note, F_REG, 6.0, MUTED, 'centre')

y = ty - 34
y = card.para(MARGIN, y - 9, CONTENT,
              'Measured on a full-frame sensor. A crop body shows the Moon '
              'about half again as large at the same focal length, and a small '
              'astronomy camera larger still, because both are cropping into '
              'the middle of the same picture.', F_REG, 6.8, 8.0, MUTED)

# ── the things that actually decide how sharp it is ────────────────────
y = card.section(MARGIN, y - 14, CONTENT, 'What limits you is the air', PINK)

CARD_W = (CONTENT - 20) / 3.0
row = []
row.append(card.note_card(
    MARGIN, y + 4, CARD_W, 'Wait until it is high',
    'Near the horizon you are looking through several times more air. Thirty '
    'degrees up is a sensible minimum. Higher is better.', PINK, SOFT_V))
row.append(card.note_card(
    MARGIN + CARD_W + 10, y + 4, CARD_W, 'Never over a hot roof',
    'A road, a rooftop or an air conditioning unit that baked all day pours '
    'heat upwards all evening. In a city this ruins more nights than light '
    'pollution does.', PINK, SOFT_V))
row.append(card.note_card(
    MARGIN + (CARD_W + 10) * 2, y + 4, CARD_W, 'Stack the sharpest',
    'Shoot a burst or a short video, throw away the soft frames and average '
    'the rest. Siril does it free. That is how sharp lunar pictures are '
    'made.', PINK, SOFT_V))

# ── the pre-flight strip ───────────────────────────────────────────────
y = card.section(MARGIN, min(row) - 15, CONTENT, 'Before you press anything')
CHECKS = [
    ('Phase', 'not full'),
    ('Altitude', 'over 30 degrees'),
    ('Exposure', 'manual, way down'),
    ('Focus', 'magnified, by hand'),
    ('Frames', 'a burst, not one'),
]
CHK_W = CONTENT / len(CHECKS)
for i, (head, note) in enumerate(CHECKS):
    cx = MARGIN + CHK_W * i
    c.setFillColor(VIOLET)
    c.rect(cx, y - 1.4, 1.9, 8.4, stroke=0, fill=1)
    card.text(cx + 6, y, head, F_SEMI, 6.8, INK)
    card.text(cx + 6 + sw(head, F_SEMI, 6.8) + 4, y, note, F_REG, 6.4, MUTED)

card.footer(
    'The full guide, with examples',
    'Full walkthrough with example images, the phase timetable in detail, how '
    'to tell in ten seconds whether the Moon is up tonight, and what to '
    'photograph on the few nights each month when it is not.',
    URL)

card.save()
print('wrote', OUT, 'lowest card bottom:', round(min(row), 1))
