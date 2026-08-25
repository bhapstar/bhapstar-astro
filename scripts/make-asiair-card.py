#!/usr/bin/env python3
"""
make-asiair-card.py — the printable crib sheet for the ASIAir
--------------------------------------------------------------------------
One side of A4: what the box is, what plugs into it, the order a night runs
in including the fork between an unattended Autorun and Live stacking, the
settings worth getting right, and the four things worth knowing before a
first night. Content follows /articles/asiair-astrophotography-control.html.

    python3 make-asiair-card.py
"""

from fieldcard import (Card, register_fonts, MARGIN, PW, CONTENT,
                       INK, BODY, MUTED, VIOLET, BLUE, PINK, LINE,
                       SOFT_V, SOFT_B, F_REG, F_SEMI, F_BOLD, sw, wrap)

OUT = 'asiair-field-card.pdf'
URL = ('https://bhapstar.com/articles/'
       'asiair-astrophotography-control.html?src=pdf-asiair')

register_fonts()

card = Card(OUT,
            'The ASIAir: field card',
            'Printable crib sheet for running an imaging session from an '
            'ASIAir: what plugs in, the order a night runs in, and the '
            'settings worth getting right')
c = card.c

y = card.header('The ASIAir, on one page',
                'Print it, fold it, take it out with you.')

y = card.callout(
    MARGIN, y, CONTENT,
    'What it is, in one paragraph',
    'A small Linux computer that sits on the telescope. The mount, cameras, '
    'focuser and dew heater all plug into it, one 12 volt lead runs to the '
    'ground, and you drive the whole night from a tablet or phone over Wi-Fi. '
    'Plate solving, autofocus, guiding and the imaging plan all run on the box '
    'itself, so the frames keep being written even if the tablet goes flat or '
    'wanders out of range.')

# ── the night, with the fork ───────────────────────────────────────────
y = card.section(MARGIN, y - 14, CONTENT, 'A night, in the order it happens')

STAGE_H = 34.0
SHARED_W = 72.0
SHARED_GAP = 8.0
FORK_GAP = 26.0
BRANCH_W = 90.0
BRANCH_GAP = 8.0

flow_top = y + 2
mid = flow_top - 58          # vertical centre of the shared row

# The four stages you have to be awake for.
SHARED = [('Polar align', 'on-screen, ~5 min'),
          ('Plate solve', 'then goto target'),
          ('Autofocus', 'EAF V-curve'),
          ('Frame', 'rotate, re-solve')]

sx = MARGIN
for i, (label, sub) in enumerate(SHARED):
    card.stage(sx, mid + STAGE_H / 2, SHARED_W, STAGE_H, label, sub)
    if i < len(SHARED) - 1:
        card.arrow(sx + SHARED_W + 1.0, mid, BLUE)
    sx += SHARED_W + SHARED_GAP

fork_x = MARGIN + 4 * SHARED_W + 3 * SHARED_GAP
branch_x = fork_x + FORK_GAP
top_mid = mid + 26           # centre line of the Autorun branch
bot_mid = mid - 26           # centre line of the Live branch

# The elbow: out of Frame, then up and down into the two branches.
c.setStrokeColor(BLUE)
c.setLineWidth(1.1)
c.setLineCap(1)
c.line(fork_x + 1, mid, fork_x + 12, mid)
c.line(fork_x + 12, bot_mid, fork_x + 12, top_mid)
c.line(fork_x + 12, top_mid, branch_x - 7, top_mid)
c.line(fork_x + 12, bot_mid, branch_x - 7, bot_mid)
card.arrow(branch_x - 7, top_mid, BLUE)
card.arrow(branch_x - 7, bot_mid, BLUE)

TOP_BRANCH = [('Autorun', 'lights + dithering'), ('Meridian flip', 'then darks & flats')]
BOT_BRANCH = [('Live stack', 'builds on screen'), ('Save & show', 'one image, there and then')]

for branch, centre, accent in ((TOP_BRANCH, top_mid, VIOLET),
                               (BOT_BRANCH, bot_mid, PINK)):
    bx = branch_x
    for i, (label, sub) in enumerate(branch):
        card.stage(bx, centre + STAGE_H / 2, BRANCH_W, STAGE_H, label, sub,
                   accent=accent if i == 0 else None)
        if i < len(branch) - 1:
            card.arrow(bx + BRANCH_W + 1.0, centre, BLUE)
        bx += BRANCH_W + BRANCH_GAP

card.text(branch_x, top_mid + STAGE_H / 2 + 5, 'Leave it running',
          F_SEMI, 6.8, VIOLET)
card.text(branch_x, bot_mid - STAGE_H / 2 - 11, 'Watch it build',
          F_SEMI, 6.8, PINK)

y = bot_mid - STAGE_H / 2 - 22
y = card.para(MARGIN, y, CONTENT,
              'Only the first four stages need you awake. After framing, the night '
              'goes one of two ways. Set an Autorun and sleep through it: the box '
              'handles the meridian flip on its own, then re-solves and re-centres '
              'so the framing survives it. Or switch to Live and let the frames '
              'stack on screen as they arrive, which is the mode to use when there '
              'are people standing next to you waiting to see something.',
              F_REG, 6.9, 8.2, MUTED)

# ── two columns: what plugs in, settings ───────────────────────────────
GUTTER = 15
LEFT_W = 214.0
RIGHT_X = MARGIN + LEFT_W + GUTTER
RIGHT_W = CONTENT - LEFT_W - GUTTER

col_top = y - 10
ly = card.section(MARGIN, col_top, LEFT_W, 'What plugs into what')

PORTS = [
    ('Mount', 'goto, tracking, meridian flip'),
    ('Main camera', 'exposures, cooling, storage'),
    ('Guide camera', 'guiding and dithering'),
    ('Electronic focuser', 'autofocus by V-curve'),
    ('Dew heater', 'switched 12 V, warm all night'),
    ('One 12 V input', 'the only lead running to the ground'),
    ('Tablet or phone', 'Wi-Fi, no cable. A tablet is easier'),
]

for i, (name, role) in enumerate(PORTS):
    if i % 2 == 0:
        c.setFillColor(SOFT_V)
        c.rect(MARGIN - 3, ly - 4.4, LEFT_W + 3, 13.4, stroke=0, fill=1)
    card.text(MARGIN, ly, name, F_SEMI, 7.2, INK)
    card.text(MARGIN + LEFT_W, ly, role, F_REG, 6.8, MUTED, 'right')
    ly -= 13.4

ly = card.para(MARGIN, ly - 6, LEFT_W,
               'The short cables live on the telescope, which is where most lost '
               'sessions come from: a USB lead working loose in the cold, a hub '
               'dropping a device, a laptop lid closing. On this rig the '
               'controller, main sensor and guide sensor are all inside the '
               'ASI585MC Air, so three of those boxes collapse into one.',
               F_REG, 6.9, 8.2, MUTED)

ry = card.section(RIGHT_X, col_top, RIGHT_W, 'Settings worth getting right')

SET_COLS = [(0, 78, 'label'), (86, 92, 'value'), (186, 112, 'note')]
SET_ROWS = [
    ('Wi-Fi mode', 'Station mode',
     'Joins the box to your house network so the tablet keeps both'),
    ('Autofocus', 'Repeat hourly, or on a temperature drop',
     'A refractor moves focus measurably as the tube cools'),
    ('Dithering', 'On, always',
     'Fixed sensor noise lands somewhere new each frame and averages away'),
    ('Guiding', 'Below half your image scale',
     'In arcseconds. Keep under that and the stars stay round'),
    ('Power', 'One supply, generously sized',
     'Undersized ones fail while cooling and slewing at once, and it looks like a software fault'),
    ('Storage', 'Copy off after every night',
     'Short subframes fill the card faster than expected'),
]
ry = card.table(RIGHT_X, ry + 3, SET_COLS, SET_ROWS,
                size=7.0, note_size=6.5, leading=7.6,
                pad_top=9, pad_bottom=5, total=RIGHT_W)

y = min(ly, ry)

# ── strengths, limits, first night ─────────────────────────────────────
y = card.section(MARGIN, y - 12, CONTENT, 'Before your first night')

CARD_W = (CONTENT - 3 * 11) / 4.0
tops = y + 2
bottoms = []
FIRST = [
    ('Use station mode', 'Out of the box it broadcasts its own network, so your '
     'tablet has to leave your home Wi-Fi to reach it. Joining it to the house '
     'network keeps both, and lets you check a run from indoors.', VIOLET),
    ('Give it real power', 'A single 12 V feed runs the controller, a cooled '
     'camera, the mount and the dew heaters. Undersized supplies cause failures '
     'that look like software faults.', BLUE),
    ('Flats before teardown', 'The moment the camera rotates in the focuser, '
     'that night\u2019s flats stop matching. Two minutes at the end of the '
     'session saves a re-shoot.', PINK),
    ('It is a closed system', 'It expects ZWO cameras and a defined list of '
     'mounts, not anything that speaks ASCOM. Less choice, and far fewer things '
     'to debug in the dark.', VIOLET),
]
for i, (heading, body, accent) in enumerate(FIRST):
    bottoms.append(card.note_card(
        MARGIN + i * (CARD_W + 11), tops, CARD_W, heading, body, accent,
        size=6.7, leading=8.0, head_size=8.0))


# ── the three in the morning section ───────────────────────────────────
y = card.section(MARGIN, min(bottoms) - 16, CONTENT, 'When it goes wrong at three in the morning')

TROUBLE_COLS = [(0, 132, 'label'), (142, 150, 'value'), (302, 225, 'note')]
TROUBLE_HEAD = ['What you see', 'Usually', 'What to do']
TROUBLE_ROWS = [
    ('Plate solving keeps failing',
     'Too short an exposure, or focus badly out',
     'The solver needs stars it can measure. Get roughly focused first, then lengthen the solve exposure'),
    ('Autofocus comes back wrong',
     'Thin cloud, or too few stars in the frame',
     'Slew to a richer star field, run it there, then go back to the target'),
    ('Guiding graph wanders',
     'Polar alignment, or something pulling on a cable',
     'Check nothing is snagged as the mount turns, then re-run polar align. Aim under half your image scale'),
    ('Cooling or slewing drops out',
     'One 12 V supply doing too much at once',
     'It looks like a software fault and is not. Give it headroom, or split the load'),
    ('Frames stack badly the next day',
     'Dithering off, or flats taken after teardown',
     'Neither can be fixed later. Leave dithering on, and shoot flats before anything is loosened'),
]
y = card.table(MARGIN, y + 3, TROUBLE_COLS, TROUBLE_ROWS, head=TROUBLE_HEAD,
               size=7.0, note_size=6.6, leading=7.8,
               pad_top=9, pad_bottom=5, total=CONTENT)

card.footer(
    'The full guide, with examples',
    'Screenshots from a live session, how polar alignment works without seeing '
    'Polaris, what plate solving actually does, and where a mini PC running '
    'NINA makes more sense than a closed box.',
    URL)

card.save()
print('wrote', OUT, 'lowest card bottom:', round(min(bottoms), 1))
