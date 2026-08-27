#!/usr/bin/env python3
"""
make-milky-way-phone-card.py — the printable crib sheet for the phone route
---------------------------------------------------------------------------
One side of A4, for someone standing in the dark with a phone on a small
tripod. Content follows
/articles/photograph-meteor-shower-milky-way-phone.html.

Rebuilt from the printed card after the original driver was lost, with the
meteor panel replaced by the timelapse and star trail material. Meteors now
have a card of their own: make-meteor-shower-card.py.

    python3 make-milky-way-phone-card.py
"""

from fieldcard import (Card, register_fonts, MARGIN, PW, CONTENT,
                       INK, BODY, MUTED, VIOLET, BLUE, PINK, LINE,
                       SOFT_V, SOFT_B, F_REG, F_SEMI, F_BOLD, sw, wrap)

OUT = 'meteors-milky-way-phone-field-card.pdf'
URL = ('https://bhapstar.com/articles/'
       'photograph-meteor-shower-milky-way-phone.html?src=pdf-phone')

register_fonts()

card = Card(OUT,
            'The Milky Way on a phone: field card',
            'Printable crib sheet for photographing the Milky Way and shooting '
            'a night timelapse with a phone on a tripod')
c = card.c

y = card.header('The Milky Way on a phone',
                'Print it, fold it, take it out with you.')

# ── the two things that decide the night ───────────────────────────────
y = card.section(MARGIN, y - 12, CONTENT, 'The two things that decide the night')

HALF = (CONTENT - 14) / 2.0
b1 = card.note_card(
    MARGIN, y + 2, HALF, 'A tripod',
    'Night photography holds the shutter open for several seconds, and anything '
    'hand-held moves in that time. A small tabletop tripod is enough. Bonus: '
    'many phones only unlock their longest exposures once they are sure the '
    'phone is completely still.', VIOLET)
b2 = card.note_card(
    MARGIN + HALF + 14, y + 2, HALF, 'A dark sky',
    'From a city the skyglow is brighter than the Milky Way, and no amount of '
    'editing recovers what the phone never saw. An hour out of most cities is '
    'usually enough, and the difference is dramatic rather than subtle.', BLUE)
y = min(b1, b2)

# ── your phone, by make ────────────────────────────────────────────────
y = card.section(MARGIN, y - 14, CONTENT, 'Your phone, by make')

COL_W = (CONTENT - 2 * 13) / 3.0
COL_X = [MARGIN, MARGIN + COL_W + 13, MARGIN + 2 * (COL_W + 13)]

MAKES = [
    ('iPhone', VIOLET, [
        ('Lens', 'Main wide lens, not the ultra-wide or the zoom. Biggest '
                 'sensor, fastest aperture.'),
        ('Up to iPhone 16', 'The moon icon appears in the dark. On a tripod the '
                            'exposure slider runs to about 30 seconds. Drag it '
                            'to maximum and tap the shutter.'),
        ('iPhone 17 series', 'The slider is gone. Night mode is Off, Auto or '
                             'Max. Choose Max: up to 30s on a tripod. Auto will '
                             'not give you a long exposure.'),
        ('ProRAW', 'Turn it on if your model offers it. It records a file you '
                   'can brighten properly afterwards.'),
    ]),
    ('Samsung Galaxy', BLUE, [
        ('Pro mode', 'Manual shutter to 30 seconds, plus manual ISO and focus. '
                     'Enough on its own.'),
        ('The hidden astro mode', 'Download Expert RAW from the Galaxy Store. '
                                  'Open it, tap the settings icon, turn on '
                                  'Special photo options. An astrophotography '
                                  'icon then appears.'),
        ('If you cannot find it', 'It only shows at 12MP resolution. Listed for '
                                  'S22 and S23 series onwards.'),
        ('Star trails', 'Hyperlapse mode, speed 300x, then a star trails toggle '
                        'appears. Set resolution to UHD.'),
    ]),
    ('Pixel and other Android', PINK, [
        ('Pixel', 'Night Sight, on a tripod, then leave it alone. It relabels '
                  'itself as astrophotography and offers up to about four '
                  'minutes, stacking frames internally.'),
        ('Everything else', 'Most Android phones have a Pro mode somewhere in '
                            'the camera app. 30 seconds is plenty.'),
        ('Worth ten minutes', 'Go through every mode in your camera app before '
                              'deciding your phone cannot do this. The useful '
                              'one is rarely on the front screen.'),
    ]),
]

col_top = y + 2
bottoms = []
for x, (name, accent, rows) in zip(COL_X, MAKES):
    cy = col_top
    c.setFillColor(accent)
    c.rect(x, cy - 4.8, 2.4, 9.2, stroke=0, fill=1)
    card.text(x + 9, cy, name, F_SEMI, 8.4, INK)
    cy -= 12
    for label, body in rows:
        card.text(x, cy, label, F_SEMI, 7.2, INK)
        cy -= 8.8
        cy = card.para(x, cy, COL_W, body, F_REG, 6.8, 8.0, MUTED)
        cy -= 3.4
    bottoms.append(cy)
y = min(bottoms)

# ── the pro mode tiles ─────────────────────────────────────────────────
y = card.section(MARGIN, y - 6, CONTENT, 'If your phone has a Pro mode, set this')

TILES = [
    ('ISO', '3200', 'Until the sky looks grey rather than black, then back off '
                    'a step'),
    ('SHUTTER', '20"', 'Long enough to record the core, short enough to repeat '
                       'all night'),
    ('WB', '4000K', 'Consistent colour across every frame of the night'),
    ('FOCUS', 'Infinity', 'The step most people skip. Slide it all the way by '
                          'hand'),
    ('FORMAT', 'RAW', 'Real latitude to lift the shadows afterwards'),
    ('TIMER', '3s', 'Stops the tap itself shaking the phone'),
]

TILE_W = (CONTENT - 5 * 9) / 6.0
TILE_H = 52.0
ty = y + 2
for i, (label, value, note) in enumerate(TILES):
    tx = MARGIN + i * (TILE_W + 9)
    c.setFillColor(SOFT_B)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(tx, ty - TILE_H, TILE_W, TILE_H, 5, stroke=1, fill=1)
    c.setFillColor((VIOLET, BLUE, PINK)[i % 3])
    c.rect(tx, ty - TILE_H, TILE_W, 2.2, stroke=0, fill=1)
    card.text(tx + TILE_W / 2, ty - 10, label, F_SEMI, 6.2, MUTED, 'centre')
    card.text(tx + TILE_W / 2, ty - 23, value, F_BOLD, 12, VIOLET, 'centre')
    ny = ty - 33
    for line in wrap(note, F_REG, 6.2, TILE_W - 10):
        card.text(tx + TILE_W / 2, ny, line, F_REG, 6.2, MUTED, 'centre')
        ny -= 7.2
y = ty - TILE_H
card.para(MARGIN, y - 10, CONTENT,
          'No manual mode? You lose very little. Night mode on a tripod, fired '
          'again and again, gets you most of the way there.',
          F_REG, 6.8, 8.0, MUTED)
y -= 20

# ── how long an exposure each route gives you ──────────────────────────
y = card.section(MARGIN, y - 6, CONTENT, 'How long an exposure each option gives you')

BARS = [
    ('Pixel astro mode', '~4 min', 240, 'tripod detected, automatic'),
    ('Manual camera app', '60s', 60, 'full manual, RAW, iOS or Android'),
    ('Samsung Expert RAW', '30s', 30, 'Pro mode, manual ISO'),
    ('iPhone Night mode', '30s', 30, 'on a tripod, no manual control'),
    ('Any phone, handheld', '3s', 3, 'the phone cannot hold still enough'),
]

BAR_X = MARGIN + 122
BAR_MAX = 250.0
by = y - 2
for i, (name, value, secs, note) in enumerate(BARS):
    card.text(MARGIN, by - 6, name, F_SEMI, 7.2, INK)
    card.text(MARGIN, by - 14, note, F_REG, 6.2, MUTED)
    # square root keeps the four-minute bar from flattening the rest
    w = BAR_MAX * (secs / 240.0) ** 0.5
    c.setFillColor((VIOLET, BLUE, BLUE, BLUE, PINK)[i])
    c.roundRect(BAR_X, by - 15, max(w, 4), 12, 2.5, stroke=0, fill=1)
    card.text(BAR_X + max(w, 4) + 7, by - 12, value, F_SEMI, 7.6, INK)
    by -= 21
card.para(MARGIN, by - 1, CONTENT,
          'Longer is not always better. Four minutes gives a lovely Milky Way, '
          'but the stars will have visibly moved across the frame. Twenty to '
          'thirty seconds, repeated over and over, is the sweet spot for most '
          'people.', F_REG, 6.8, 8.0, MUTED)
y = by - 27

# ── two columns: on the night, and the timelapse ───────────────────────
GUTTER = 15
LEFT_W = 250.0
RIGHT_X = MARGIN + LEFT_W + GUTTER
RIGHT_W = CONTENT - LEFT_W - GUTTER

col_top = y - 4
ly = card.section(MARGIN, col_top, LEFT_W, 'On the night')

NIGHT = [
    ('Clean the lens', 'A fingerprint you would never notice by day turns every '
                       'bright star into a smeared halo.'),
    ('Keep it firing', 'Take frame after frame for an hour or two. Every one is '
                       'a Milky Way exposure, and the whole run is also a '
                       'timelapse and a star trail.'),
    ('Frame something solid', 'A rock, a dune ridge, a tree line, a friend '
                              'looking up. Two minutes on composition pays for '
                              'the whole session.'),
    ('Screen down, red light on', 'Eyes take about twenty minutes to adapt and '
                                  'a bright screen undoes that in a second.'),
    ('Power bank, and watch for dew', 'Long exposures drain a phone fast. If '
                                      'everything suddenly looks soft, wipe the '
                                      'lens.'),
]
for i, (name, body) in enumerate(NIGHT):
    accent = (VIOLET, BLUE, PINK)[i % 3]
    c.setFillColor(accent)
    c.rect(MARGIN, ly - 4.4, 2.4, 8.2, stroke=0, fill=1)
    card.text(MARGIN + 9, ly, name, F_SEMI, 7.4, INK)
    ly -= 9.0
    ly = card.para(MARGIN + 9, ly, LEFT_W - 9, body, F_REG, 6.8, 8.0, MUTED)
    ly -= 3.6

ry = card.section(RIGHT_X, col_top, RIGHT_W, 'Timelapses and star trails')

TL = [
    ('It is the same hour, played back',
     'A star trail is that hour drawn as one picture. A timelapse is the same '
     'hour as video. Hyperlapse on a Samsung, Time-lapse on an iPhone, both '
     'happier once the phone is already on a tripod.'),
    ('The exchange rate is brutal',
     'Video runs at about 25 frames a second, so a satisfying ten second clip '
     'needs a few hundred separate exposures. That is an hour or two of real '
     'time for a few seconds of video.'),
    ('Do not touch it once it is running',
     'Picking the phone up to check ends the sequence, and there is no way to '
     'join the two halves back together afterwards. Set it going and walk '
     'away.'),
]
for i, (heading, body) in enumerate(TL):
    accent = (PINK, VIOLET, BLUE)[i % 3]
    c.setFillColor(accent)
    c.rect(RIGHT_X, ry - 4.4, 2.4, 8.2, stroke=0, fill=1)
    ry = card.para(RIGHT_X + 9, ry, RIGHT_W - 9, heading, F_SEMI, 7.4, 9.0, INK)
    ry += 9.0 - 9.2
    ry = card.para(RIGHT_X + 9, ry, RIGHT_W - 9, body, F_REG, 6.8, 8.0, MUTED)
    ry -= 4.4

card.footer(
    'The full guide, with examples',
    'Full walkthrough with example images, where the astro mode hides on each '
    'make, and the camera version of this card for when you want to go further '
    'than the phone can take you. There is a separate card for meteor showers.',
    URL)

card.save()
print('wrote', OUT, 'lowest column bottom:', round(min(ly, ry), 1))
