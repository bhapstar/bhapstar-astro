#!/usr/bin/env python3
"""
make-calibration-card.py — the printable crib sheet for calibration frames
--------------------------------------------------------------------------
One side of A4, meant to live in the eyepiece case and come out at the end of
a session when it is cold and late and the order of things is easy to get
wrong. Content follows /articles/calibration-frames-darks-flats-biases.html.

    python3 make-calibration-card.py
"""

from fieldcard import (Card, register_fonts, out_path, MARGIN, PW, CONTENT,
                       INK, BODY, MUTED, VIOLET, BLUE, PINK, LINE,
                       SOFT_V, SOFT_B, F_REG, F_SEMI, F_BOLD, sw, wrap)

OUT = out_path('calibration-frames-field-card.pdf')
URL = ('https://bhapstar.com/articles/'
       'calibration-frames-darks-flats-biases.html?src=pdf-calibration')

register_fonts()

card = Card(OUT,
            'Calibration frames: field card',
            'Printable crib sheet for taking darks, flats, bias and dark flat '
            'frames at the end of an imaging session')
c = card.c

y = card.header('Calibration frames',
                'Print it, fold it, take it out with you.')

# ── the whole idea, before anything else ───────────────────────────────
y = card.callout(
    MARGIN, y, CONTENT,
    'The whole thing in one paragraph',
    'Every frame you take holds the night sky plus a set of marks the camera '
    'and telescope put there on their own: dust shadows, darker corners, heat, '
    'and an electrical floor. Calibration frames are pictures of those marks '
    'with no sky in them, so the software can work out what to remove. Twenty '
    'minutes at the end of the night, and it is the difference between a clean '
    'picture and a blotchy one.')

# ── the four frames ────────────────────────────────────────────────────
y = card.section(MARGIN, y - 14, CONTENT, 'The four frames, and what each one removes')

COLS = [
    (0,   52,  'label'),
    (60,  104, 'value'),
    (172, 200, 'note'),
    (382, 66,  'note'),
    (456, 71,  'note'),
]
HEAD = ['Frame', 'What it removes', 'How to take it', 'How many', 'How long it lasts']

ROWS = [
    ('Dark', 'Heat and hot pixels',
     'Cap on. Same exposure, gain and sensor temperature as your lights',
     '20 to 30', 'Months, if the camera is cooled'),
    ('Bias', 'The sensor\u2019s fixed offset',
     'Cap on. The shortest exposure the camera will physically take',
     '50 to 100', 'Until you change gain'),
    ('Flat', 'Dust shadows and darker corners',
     'Even light through the whole imaging train, with nothing moved or refocused',
     'About 30', 'That session, that filter'),
    ('Dark flat', 'The offset, out of the flats',
     'Cap on. Same exposure as the flats you have just taken',
     'Match the flats', 'With the flats'),
]

y = card.table(MARGIN, y - 2, COLS, ROWS, head=HEAD, total=CONTENT)

# ── the arithmetic ─────────────────────────────────────────────────────
y -= 12
BAND_H = 34
c.setFillColor(SOFT_B)
c.setStrokeColor(LINE)
c.setLineWidth(0.7)
c.roundRect(MARGIN, y - BAND_H, CONTENT, BAND_H, 5, stroke=1, fill=1)

formula = '( light \u2212 dark )  \u00f7  ( flat \u2212 bias )'
card.text(MARGIN + 16, y - 22, formula, F_BOLD, 13, VIOLET)
fx = MARGIN + 16 + sw(formula, F_BOLD, 13) + 18
card.text(fx, y - 15, 'Subtract what the sensor added.', F_REG, 7.2, BODY)
card.text(fx, y - 25, 'Divide out what the optics took away. What is left is the sky.',
          F_REG, 7.2, BODY)
y -= BAND_H

# ── two columns ────────────────────────────────────────────────────────
GUTTER = 15
LEFT_W = 236.0
RIGHT_X = MARGIN + LEFT_W + GUTTER
RIGHT_W = CONTENT - LEFT_W - GUTTER

col_top = y - 14
ly = card.section(MARGIN, col_top, LEFT_W, 'At the scope, in this order')

STEPS = [
    ('Lights', 'Shoot the target. Nothing on the rig moves, rotates or refocuses '
               'until the run is finished.'),
    ('Flats', 'Dawn sky, a flat panel, or a white T-shirt over the front with a '
              'tablet behind it. Same focus, same rotation, same filter. Set the '
              'exposure so the histogram peak sits near the middle.'),
    ('Dark flats', 'Cap on. Same exposure as the flats you just took, and the same '
                   'number of them. Take these and you do not need biases at all.'),
    ('Darks', 'Cap on. Same exposure, gain and temperature as the lights. If the '
              'camera is not cooled, take them now while the air is still the '
              'temperature it was.'),
    ('Biases', 'Cap on. A thousandth of a second. They cost nothing and they keep '
               'for months, so they can be done indoors another day.'),
    ('Now pack up', 'Only once the flats are safely on the card is it safe to '
                    'loosen, rotate or take anything apart.'),
]

for i, (name, body) in enumerate(STEPS, start=1):
    c.setFillColor(VIOLET)
    c.circle(MARGIN + 6, ly - 2.4, 6.4, stroke=0, fill=1)
    card.text(MARGIN + 6, ly - 4.6, str(i), F_SEMI, 6.6, SOFT_V, 'centre')
    card.text(MARGIN + 18, ly, name, F_SEMI, 7.6, INK)
    ly -= 9.4
    ly = card.para(MARGIN + 18, ly, LEFT_W - 18, body, F_REG, 6.9, 8.2, MUTED)
    ly -= 3.6

ry = card.section(RIGHT_X, col_top, RIGHT_W, 'The rules people break')

RULES = [
    ('Take flats before you take anything apart',
     'The moment the camera rotates in the focuser, even slightly, the dust '
     'shadows move and that night\u2019s flats stop matching. This is the single '
     'most common mistake and it costs the whole set.'),
    ('Do not touch focus',
     'Dust shadows change size with focus position, so a flat taken at a '
     'different focus point removes the wrong shapes.'),
    ('One set of flats per filter',
     'Each filter carries its own dust and its own transmission. A quick-change '
     'filter drawer does not exempt you from re-shooting them.'),
    ('Narrowband flats take longer than you expect',
     'A 3nm filter blocks nearly everything, so a panel bright enough for an '
     'unfiltered flat gives you a nearly black one. Dim the panel and extend the '
     'exposure rather than the other way round.'),
    ('Aim at something evenly lit',
     'A cloud, a sunlit wall or a laptop screen with a gradient across it all '
     'produce a flat that makes the picture worse, because the software will '
     'faithfully divide out whatever unevenness you photographed.'),
]

for i, (heading, body) in enumerate(RULES):
    accent = (PINK, VIOLET, BLUE)[i % 3]
    c.setFillColor(accent)
    c.rect(RIGHT_X, ry - 4.6, 2.4, 8.4, stroke=0, fill=1)
    ry = card.para(RIGHT_X + 9, ry, RIGHT_W - 9, heading, F_SEMI, 7.6, 9.2, INK)
    ry += 9.2 - 9.4
    ry = card.para(RIGHT_X + 9, ry, RIGHT_W - 9, body, F_REG, 6.9, 8.2, MUTED)
    ry -= 4.6

y = min(ly, ry)

# ── what skipping costs, and where it all happens ──────────────────────
y = card.section(MARGIN, y - 6, CONTENT, 'What it costs to skip them, and where it happens')

CARD_W = (CONTENT - 2 * 12) / 3.0
y3 = y + 2
bottoms = []
bottoms.append(card.note_card(
    MARGIN, y3, CARD_W, 'Skipping darks',
    'Some extra noise and a scattering of coloured speckles. Survivable, and if '
    'you dithered during capture the stacking software rejects most of the hot '
    'pixels anyway.', PINK))
bottoms.append(card.note_card(
    MARGIN + CARD_W + 12, y3, CARD_W, 'Skipping flats',
    'This is the one that ruins pictures. Vignetting and dust are multiplied '
    'into the frame rather than added to it, so background extraction later '
    'cannot model them. The result looks nearly right and is subtly wrong '
    'everywhere.', VIOLET))
bottoms.append(card.note_card(
    MARGIN + 2 * (CARD_W + 12), y3, CARD_W, 'Where it actually happens',
    'Folders named lights, darks, flats and biases. Point Siril at the parent '
    'folder and run its one-shot-colour script: it stacks the calibration frames '
    'into masters, applies them, aligns everything and stacks the result, all '
    'unattended.', BLUE))


# ── what a flat actually removes ───────────────────────────────────────
# The same three-panel idea as the diagram in the article, drawn small enough
# to survive a mono laser printer: the vignette is a stack of nested rectangles
# rather than a gradient, and the dust marks are rings, because that is what a
# dust shadow looks like on a real frame.
y = min(bottoms) - 16
y = card.section(MARGIN, y, CONTENT, 'What a flat frame actually removes')

PANEL_W, PANEL_H = 152.0, 70.0
SYM_W = 30.0
px0 = MARGIN
panel_top = y + 4


def vignette(x, top, w, h, strength=1.0, dust=(), stars=()):
    """A frame corner-darkened by nested rectangles, with optional dust rings
    and stars. The insets are a fraction of each side rather than a fixed step,
    so the rectangles shrink towards the centre instead of collapsing into a
    band on the shorter axis."""
    steps = 16
    for i in range(steps):
        t = i / float(steps - 1)
        g = 0.72 + 0.26 * t
        g = 1.0 - (1.0 - g) * strength
        c.setFillColorRGB(g, g, min(g * 1.01, 1.0))
        ix = t * w * 0.42
        iy = t * h * 0.42
        c.rect(x + ix, top - h + iy,
               max(w - 2 * ix, 0.5), max(h - 2 * iy, 0.5), stroke=0, fill=1)
    for dx, dy, r in dust:
        c.setStrokeColorRGB(0.58, 0.58, 0.62)
        c.setLineWidth(1.3)
        c.circle(x + dx, top - h + dy, r, stroke=1, fill=0)
    for dx, dy, r in stars:
        c.setFillColorRGB(1, 1, 1)
        c.circle(x + dx, top - h + dy, r, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.setFillColorRGB(1, 1, 1)
    c.rect(x, top - h, w, h, stroke=1, fill=0)


DUST = [(34, 49, 5.2), (86, 22, 3.6), (120, 54, 4.4), (60, 14, 2.8)]
STARS = [(24, 18, 1.0), (52, 41, 1.4), (78, 57, 0.9), (104, 31, 1.2),
         (132, 44, 1.0), (68, 29, 0.8), (98, 12, 1.0), (40, 59, 1.1),
         (116, 63, 0.9), (18, 47, 0.8), (140, 20, 1.1), (60, 52, 0.9)]

vignette(px0, panel_top, PANEL_W, PANEL_H, 1.0, DUST, STARS)
px1 = px0 + PANEL_W + SYM_W
vignette(px1, panel_top, PANEL_W, PANEL_H, 1.0, DUST)
px2 = px1 + PANEL_W + SYM_W
c.setFillColorRGB(0.93, 0.93, 0.95)
c.rect(px2, panel_top - PANEL_H, PANEL_W, PANEL_H, stroke=0, fill=1)
for dx, dy, r in STARS:
    c.setFillColorRGB(1, 1, 1)
    c.circle(px2 + dx, panel_top - PANEL_H + dy, r, stroke=0, fill=1)
c.setStrokeColor(LINE)
c.setLineWidth(0.7)
c.rect(px2, panel_top - PANEL_H, PANEL_W, PANEL_H, stroke=1, fill=0)

sym_y = panel_top - PANEL_H / 2 - 5
card.text(px0 + PANEL_W + SYM_W / 2, sym_y, '\u00f7', F_BOLD, 15, VIOLET, 'centre')
card.text(px1 + PANEL_W + SYM_W / 2, sym_y, '=', F_BOLD, 15, VIOLET, 'centre')

cap_y = panel_top - PANEL_H - 10
for px, cap in ((px0, 'Your frame: corners lost, four dust shadows'),
                (px1, 'The flat: the same marks, on a blank field'),
                (px2, 'Corners back, marks gone, sky unchanged')):
    card.para(px, cap_y, PANEL_W, cap, F_REG, 6.6, 7.8, MUTED)

card.footer(
    'The full guide, with examples',
    'The reasoning behind each frame, what a flat actually removes, why '
    'gradient removal later cannot stand in for one, and the Siril workflow '
    'that puts it all together.',
    URL)

card.save()
print('wrote', OUT, 'lowest card bottom:', round(min(bottoms), 1))
