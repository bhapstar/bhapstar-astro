#!/usr/bin/env python3
"""
make-milky-way-camera-card.py — the printable crib sheet for the camera route
-----------------------------------------------------------------------------
One side of A4, for someone setting a camera up on a tripod at a dark site.
Content follows /articles/photograph-meteor-shower-milky-way-camera.html.

Rebuilt from the printed card after the original driver was lost. The layout
is measured off that card so a reprint sits beside the old one: settings table
in a narrow left column, three short sections stacked on the right, the
trailing figures as five tiles, then two rows of note cards. The meteor
section on the right has been replaced by the timelapse material, and meteors
now have a card of their own in make-meteor-shower-card.py.

    python3 make-milky-way-camera-card.py
"""

from fieldcard import (Card, register_fonts, out_path, MARGIN, PW, CONTENT,
                       INK, BODY, MUTED, VIOLET, BLUE, PINK, LINE,
                       SOFT_V, SOFT_B, F_REG, F_SEMI, F_BOLD, sw, wrap)

OUT = out_path('meteors-milky-way-camera-field-card.pdf')
URL = ('https://bhapstar.com/articles/'
       'photograph-meteor-shower-milky-way-camera.html?src=pdf-camera')

register_fonts()

card = Card(OUT,
            'The Milky Way on a camera: field card',
            'Printable crib sheet for photographing the Milky Way and shooting '
            'a night timelapse with a camera on a tripod')
c = card.c

y = card.header('The Milky Way on a camera',
                'Print it, fold it, take it out with you.')

# ── the whole idea, before anything else ───────────────────────────────
y = card.callout(
    MARGIN, y, CONTENT,
    'The whole technique, in one paragraph',
    'Put a wide lens on a tripod, set the camera to manual, focus on a bright '
    'star, and take the same frame over and over for an hour or two. From '
    'roughly April to September the bright core of the Milky Way is up after '
    'dark. The same frames also play back as a timelapse and stack into a star '
    'trail, so one session gives you three finished results.')

# ── two columns: the settings table, and three short sections ──────────
# Widths measured off the printed card so a reprint matches the old one.
LEFT_W = 296.0
GUTTER = 14.0
RIGHT_X = MARGIN + LEFT_W + GUTTER
RIGHT_W = CONTENT - LEFT_W - GUTTER

col_top = y - 14
ly = card.section(MARGIN, col_top, LEFT_W,
                  'Set everything manually, then leave it alone')

COLS = [(0, 78, 'label'), (83, 105, 'value'), (194, 102, 'note')]
ROWS = [
    ('Mode', 'Manual', 'Nothing should change between frames'),
    ('File', 'RAW', 'You will lift shadows heavily later'),
    ('Aperture', 'Lowest f-number your lens has',
     'Usually f/2.8. If yours stops at f/4, use f/4 and raise the ISO to match'),
    ('ISO', '3200 at a dark site',
     '1600 to 2500 suburban. High enough for faint detail, low enough to keep '
     'the sky from clipping'),
    ('Shutter', '20s at 14mm, 15s at 18mm', 'See the chart below for other lenses'),
    ('Focus', 'Manual, on a bright star',
     'Magnify the live view and adjust until the star is smallest. The infinity '
     'mark is not reliable'),
    ('White balance', 'Manual, around 4000K',
     'Consistent colour across hundreds of frames'),
    ('Long exposure NR', 'Off',
     'It pauses the camera for as long as the exposure itself, halving how much '
     'sky you collect and doubling your timelapse interval'),
    ('Stabilisation', 'Off',
     'It corrects for shake that is not there on a tripod, and can add a wobble '
     'of its own'),
    ('Drive', 'Continuous, remote locked on', 'Shoot without pause for hours'),
]
ly = card.table(MARGIN, ly + 3, COLS, ROWS, total=LEFT_W)

# right column
ry = card.section(RIGHT_X, col_top, RIGHT_W, 'What to bring')
ry = card.para(RIGHT_X, ry, RIGHT_W,
               'A camera that shoots manual and RAW, the widest and fastest '
               'lens you own, and a tripod that will not sag. Wide is better '
               'because it covers more sky. Fast means a low smallest '
               'f-number, which gathers more light. Around 14mm to 24mm at '
               'f/2.8 is close to ideal, and cheap in manual-focus form. If '
               'your widest lens only opens to f/4 that is fine: raise the ISO '
               'to compensate. Also bring spare batteries, a remote release '
               'that locks on, and a cloth for the dew.',
               F_REG, 7.2, 8.8, BODY)

ry = card.section(RIGHT_X, ry - 9, RIGHT_W, 'Where to point it', BLUE)
ry = card.para(RIGHT_X, ry, RIGHT_W,
               'From roughly April to September the bright core rises in the '
               'south-east after dark and arcs across the southern sky, '
               'highest around the middle of the night in midsummer. Any free '
               'stargazing app shows exactly where it is from where you are '
               'standing. Then put something along the bottom of the frame, a '
               'tree line or a dune ridge, because sky alone is a record '
               'rather than a picture.',
               F_REG, 7.2, 8.8, BODY)

ry = card.section(RIGHT_X, ry - 9, RIGHT_W,
                  'For a timelapse, one extra setting', PINK)
ry = card.para(RIGHT_X, ry, RIGHT_W,
               'A night timelapse is these same frames played back in order, '
               'so nothing above changes. Set the intervalometer gap to your '
               'shutter speed plus one or two seconds and no more: just enough '
               'to write the file. Any longer and the stars jump between '
               'frames instead of gliding, which is also why long exposure '
               'noise reduction has to stay off. Keep ISO, white balance and '
               'focus manual, because small decisions between frames become '
               'visible flicker at 25 frames a second.',
               F_REG, 7.2, 8.8, BODY)

y = min(ly, ry)

# ── how long before stars trail ────────────────────────────────────────
y = card.section(MARGIN, y - 14, CONTENT, 'How long before stars start trailing')

TRAIL = [('14mm', '36s', '20s'), ('18mm', '28s', '15s'), ('24mm', '21s', '12s'),
         ('35mm', '14s', '8s'), ('50mm', '10s', '6s')]
TILE_W = (CONTENT - 4 * 8) / 5.0
TILE_H = 54.0
ty = y + 2
for i, (focal, five, npf) in enumerate(TRAIL):
    tx = MARGIN + i * (TILE_W + 8)
    c.setFillColor(SOFT_B)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(tx, ty - TILE_H, TILE_W, TILE_H, 5, stroke=1, fill=1)
    card.text(tx + 11, ty - 15, focal, F_SEMI, 9, INK)
    card.text(tx + 11, ty - 30, '500 rule', F_REG, 7, MUTED)
    card.text(tx + TILE_W - 11, ty - 30, five, F_SEMI, 10.5, PINK, 'right')
    card.text(tx + 11, ty - 44, 'NPF rule', F_REG, 7, MUTED)
    card.text(tx + TILE_W - 11, ty - 44, npf, F_SEMI, 10.5, VIOLET, 'right')
y = ty - TILE_H
y = card.para(MARGIN, y - 10, CONTENT,
              'The Earth turns, so stars drift across the frame. Leave the '
              'shutter open too long and they stop being points and become '
              'short dashes. Figures are for a 24-megapixel full-frame camera. '
              'The older 500 rule is generous; the newer NPF rule is stricter '
              'and holds up better on a modern sensor. Either is fine, and '
              'anywhere between them is fine too. If the Milky Way is the '
              'priority, stay closer to NPF.', F_REG, 6.8, 8.0, MUTED)

# ── what the same frames give you ──────────────────────────────────────
y = card.section(MARGIN, y - 8, CONTENT,
                 'Three results, from the same set of frames')

CARD_W = (CONTENT - 2 * 12) / 3.0
y3 = y + 2
row1 = [
    card.note_card(MARGIN, y3, CARD_W, 'One cleaner Milky Way',
                   'Combine all the frames into a single image. Averaging many '
                   'together is what removes the grain, and the difference is '
                   'large.', VIOLET),
    card.note_card(MARGIN + CARD_W + 12, y3, CARD_W, 'A star trail',
                   'Stack the whole run and the stars draw curved lines as the '
                   'Earth turns. A free second picture from files you already '
                   'have.', BLUE),
    card.note_card(MARGIN + 2 * (CARD_W + 12), y3, CARD_W, 'A timelapse',
                   'Play the same run back in order. Apply one identical edit '
                   'to every frame, then import the folder as an image '
                   'sequence.', PINK),
]
y = min(row1) - 12

row2 = [
    card.note_card(MARGIN, y, CARD_W, 'Drive out to a dark sky',
                   'This is the single decision that matters most. Under city '
                   'glow the background sky is brighter than the Milky Way '
                   'itself, and no amount of processing brings back what the '
                   'sensor never recorded. The same camera and the same '
                   'settings an hour out of town produce a completely '
                   'different photograph.', BLUE),
    card.note_card(MARGIN + CARD_W + 12, y, CARD_W,
                   'Spend five minutes on the framing',
                   'A frame of nothing but sky is a technical record. Put a '
                   'tree line, a dune ridge or a person looking up along the '
                   'bottom and it becomes a photograph. The composition you '
                   'choose in the first five minutes is the one you keep. Then '
                   'start the intervalometer, lie back and watch.', VIOLET),
    card.note_card(MARGIN + 2 * (CARD_W + 12), y, CARD_W,
                   'How long a timelapse takes',
                   'Video runs at about 25 frames a second, so ten seconds of '
                   'finished clip costs 250 frames. At a 20 second exposure '
                   'plus a 2 second gap: one hour gives about 6 seconds, two '
                   'hours about 13, three hours about 20. Two hours is a '
                   'sensible first target.', PINK),
]

# ── the pre-flight strip ───────────────────────────────────────────────
# Five checks that decide whether an unattended run survives the night. One
# line each, because the panels above already fill the sheet and there is
# only so much room above the footer rule at y=96.
y = card.section(MARGIN, min(row2) - 15, CONTENT, 'Before you walk away')
CHECKS = [
    ('Battery', 'two spares'),
    ('Card space', '500 RAWs, 40GB'),
    ('All manual', 'auto becomes flicker'),
    ('Dew', 'check the lens hourly'),
    ('Tripod legs', 'press into the sand'),
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
    'Full walkthrough with example images, the reasoning behind each setting, '
    'and a phone version of this guide for nights when all you have is the one '
    'in your pocket. Meteor showers have a card of their own.',
    URL)

card.save()
print('wrote', OUT, 'lowest card bottom:', round(min(row2), 1))
