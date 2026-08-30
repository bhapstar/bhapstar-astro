#!/usr/bin/env python3
"""
fieldcard.py — the drawing kit behind the printable field cards
--------------------------------------------------------------
One side of A4, dark ink on white so it does not drink toner, with the site
palette used only for headings, values and accent bars. Every measurement here
was taken from the two meteor cards so a new sheet sits in the same family.

Fonts: Outfit is a variable font in the repo, and reportlab wants static ones,
so three weights are instantiated into the repo-root fonts/ directory on first
run. All paths here are resolved relative to this file, not the working
directory, so the drivers work from anywhere.

Nothing in here knows about any particular card. The content lives in the
make-*-card.py drivers.
"""

import os
from reportlab import rl_config
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
from reportlab.pdfgen import canvas as rl_canvas

# ── reproducible output ────────────────────────────────────────────────
# ReportLab stamps a creation date, a modification date and a random document
# ID into every PDF, so two runs over identical content produce two different
# files. That is fine for a one-off, and wrong for a file that lives in git:
# every rebuild would commit six changed binaries whether anything changed or
# not. invariant fixes the dates and derives the ID from the content, so a
# rebuild with no content change is byte-identical and git sees nothing.
rl_config.invariant = 1

# ── palette ────────────────────────────────────────────────────────────
# The site's own colours, darkened for paper. On screen the theme is light
# text on #050414; on paper it has to be the other way round, so these are
# the print-safe cousins of --accent, --accent2 and --accent4.
INK      = HexColor('#141229')   # headings
BODY     = HexColor('#3a3556')   # running text
MUTED    = HexColor('#6b6590')   # captions, notes, the third table column
VIOLET   = HexColor('#6d43e8')   # --accent
BLUE     = HexColor('#2563eb')   # --accent2
PINK     = HexColor('#d6337f')   # --accent4
LINE     = HexColor('#d9d4ee')   # hairlines and box borders
SOFT_V   = HexColor('#f5f3fd')   # violet-tinted fill, table stripes
SOFT_B   = HexColor('#edf3fe')   # blue-tinted fill, tiles and cards

# ── page ───────────────────────────────────────────────────────────────
PW, PH   = A4
MARGIN   = 34.0
CONTENT  = PW - MARGIN * 2       # 527.28pt

F_REG    = 'Outfit-Regular'
F_SEMI   = 'Outfit-SemiBold'
F_BOLD   = 'Outfit-Bold'

TRACKING = 1.6                   # letter-spacing on section headings

# ── paths ──────────────────────────────────────────────────────────────
# Anchored to this file (scripts/fieldcard.py), so a driver launched from
# scripts/, the repo root, or anywhere else finds the same fonts/ and
# downloads/ directories at the repo root.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)                       # scripts/ -> repo root
_FONT_DIR = os.path.join(_ROOT, 'fonts')
_VARIABLE_FONT = os.path.join(_FONT_DIR, 'outfit-latin-wght-normal.woff2')


def out_path(filename):
    """Absolute path to downloads/<filename> at the repo root, so a driver
    writes its PDF to the right place no matter where it was launched from."""
    d = os.path.join(_ROOT, 'downloads')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, filename)


def register_fonts(font_dir=_FONT_DIR, variable=_VARIABLE_FONT):
    """Instantiate three static weights out of the variable Outfit, then
    register them. Skips the conversion if the .ttf files are already there."""
    os.makedirs(font_dir, exist_ok=True)
    wanted = [(400, F_REG), (600, F_SEMI), (700, F_BOLD)]
    missing = [w for w in wanted if not os.path.isfile(os.path.join(font_dir, w[1] + '.ttf'))]
    if missing:
        from fontTools.ttLib import TTFont
        from fontTools.varLib import instancer
        for wght, name in missing:
            f = TTFont(variable)
            inst = instancer.instantiateVariableFont(f, {'wght': wght})
            inst.flavor = None
            inst.save(os.path.join(font_dir, name + '.ttf'))
    for _, name in wanted:
        pdfmetrics.registerFont(RLTTFont(name, os.path.join(font_dir, name + '.ttf')))


def sw(text, font, size):
    return pdfmetrics.stringWidth(text, font, size)


def wrap(text, font, size, width):
    """Greedy wrap. Returns a list of lines."""
    words, lines, cur = text.split(), [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if sw(trial, font, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Card:
    """A single side of A4. Coordinates are PDF points from the bottom left,
    but every helper takes a top-edge y and returns the y it finished at, so
    the drivers read top to bottom."""

    def __init__(self, path, title, subject):
        self.c = rl_canvas.Canvas(path, pagesize=A4)
        self.c.setTitle(title)
        self.c.setAuthor('Bhapinder Singh')
        self.c.setSubject(subject)

    def save(self):
        self.c.showPage()
        self.c.save()

    # ── text ───────────────────────────────────────────────────────────
    def text(self, x, y, s, font=F_REG, size=7.2, colour=BODY, align='left'):
        c = self.c
        c.setFillColor(colour)
        c.setFont(font, size)
        if align == 'right':
            c.drawRightString(x, y, s)
        elif align == 'centre':
            c.drawCentredString(x, y, s)
        else:
            c.drawString(x, y, s)

    def para(self, x, y, width, s, font=F_REG, size=7.2, leading=8.8, colour=BODY):
        """Wrapped block. y is the first baseline. Returns the baseline of the
        line after the last one drawn."""
        for line in wrap(s, font, size, width):
            self.text(x, y, line, font, size, colour)
            y -= leading
        return y

    # ── structure ──────────────────────────────────────────────────────
    def header(self, title, subtitle, kicker='Fragments of the Universe',
               site='bhapstar.com'):
        """Title left, site right, then the three-segment accent rule."""
        c = self.c
        top = PH - MARGIN - 15
        self.text(MARGIN, top, title, F_BOLD, 18, INK)
        self.text(PW - MARGIN, top + 9, kicker, F_REG, 8.6, MUTED, 'right')
        self.text(PW - MARGIN, top - 2, site, F_SEMI, 8.6, VIOLET, 'right')
        self.text(MARGIN, top - 14, subtitle, F_REG, 9.2, BODY)

        seg = CONTENT / 3.0
        bar = top - 25
        for i, col in enumerate((VIOLET, BLUE, PINK)):
            c.setFillColor(col)
            c.rect(MARGIN + seg * i, bar, seg, 2.2, stroke=0, fill=1)
        return bar - 8

    def section(self, x, y, width, label, colour=VIOLET):
        """Letter-spaced small caps with a hairline running to the column edge.
        y is the baseline. Returns the baseline of the first line beneath."""
        c = self.c
        c.setFillColor(colour)
        c.setFont(F_SEMI, 8.4)
        cx = x
        for ch in label.upper():
            c.drawString(cx, y, ch)
            cx += sw(ch, F_SEMI, 8.4) + TRACKING
        if cx + 10 < x + width:
            c.setStrokeColor(LINE)
            c.setLineWidth(0.7)
            c.line(cx + 10 - TRACKING, y + 2.6, x + width, y + 2.6)
        return y - 13

    def callout(self, x, y, width, heading, body,
                accent=VIOLET, fill=SOFT_V, size=7.6, leading=9.2):
        """Tinted panel with an accent bar down the left. y is the top edge.
        Returns the bottom edge."""
        c = self.c
        lines = wrap(body, F_REG, size, width - 24)
        h = 14 + 11 + len(lines) * leading
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.roundRect(x, y - h, width, h, 5, stroke=1, fill=1)
        c.setFillColor(accent)
        c.rect(x, y - h, 2.6, h, stroke=0, fill=1)
        self.text(x + 12, y - 14, heading, F_SEMI, 9, INK)
        by = y - 25
        for line in lines:
            self.text(x + 12, by, line, F_REG, size, BODY)
            by -= leading
        return y - h

    def note_card(self, x, y, width, heading, body, accent=VIOLET,
                  fill=SOFT_B, size=7, leading=8.4, head_size=8.6, min_h=None):
        """Same shape as a callout, tuned for the short cards along the bottom.
        Returns the bottom edge."""
        c = self.c
        lines = wrap(body, F_REG, size, width - 22)
        h = 13 + 11 + len(lines) * leading
        if min_h:
            h = max(h, min_h)
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.roundRect(x, y - h, width, h, 5, stroke=1, fill=1)
        c.setFillColor(accent)
        c.rect(x, y - h, 2.4, h, stroke=0, fill=1)
        self.text(x + 10, y - 13, heading, F_SEMI, head_size, INK)
        by = y - 24
        for line in lines:
            self.text(x + 10, by, line, F_REG, size, BODY)
            by -= leading
        return y - h

    def table(self, x, y, cols, rows, head=None, size=7.4, note_size=6.8,
              leading=8.0, pad_top=10, pad_bottom=6, total=None):
        """Striped table. `cols` is a list of (offset, width, style) where style
        is one of 'label', 'value', 'note'. y is the top edge of the first row.
        `total` is how far the stripe runs from x; it defaults to the last
        column's right edge, which leaves a ragged stripe when that column is
        narrow, so pass the column width for a clean block.
        Returns the bottom edge of the last row."""
        c = self.c
        if total is None:
            total = max(off + w for off, w, _ in cols)

        if head:
            hy = y - 8
            for (off, w, _), title in zip(cols, head):
                self.text(x + off, hy, title, F_SEMI, 6.4, MUTED)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.7)
            c.line(x - 3, hy - 5, x + total, hy - 5)
            y = hy - 9

        for i, row in enumerate(rows):
            wrapped, tallest = [], 1
            for (off, w, style), cell in zip(cols, row):
                fs = note_size if style == 'note' else size
                fn = F_REG if style == 'note' else F_SEMI
                ls = wrap(str(cell), fn, fs, w)
                wrapped.append((off, ls, style, fn, fs))
                tallest = max(tallest, len(ls))
            h = pad_top + (tallest - 1) * leading + pad_bottom
            if i % 2 == 0:
                c.setFillColor(SOFT_V)
                c.rect(x - 3, y - h, total + 3, h, stroke=0, fill=1)
            by = y - pad_top
            for off, ls, style, fn, fs in wrapped:
                col = {'label': INK, 'value': BLUE, 'note': MUTED}[style]
                yy = by
                for line in ls:
                    self.text(x + off, yy, line, fn, fs, col)
                    yy -= leading
            y -= h
        return y

    def stage(self, x, y, width, height, label, sub, accent=None, fill=SOFT_B):
        """One rounded box in a flow strip. y is the top edge."""
        c = self.c
        c.setFillColor(fill)
        c.setStrokeColor(accent or LINE)
        c.setLineWidth(1.5 if accent else 0.7)
        c.roundRect(x, y - height, width, height, 5, stroke=1, fill=1)
        self.text(x + width / 2, y - 15, label, F_SEMI, 8, INK, 'centre')
        if sub:
            self.text(x + width / 2, y - 25, sub, F_REG, 6.4, MUTED, 'centre')

    def arrow(self, x, y, colour=BLUE, size=6):
        """Small right-pointing triangle, vertically centred on y."""
        c = self.c
        p = c.beginPath()
        p.moveTo(x, y + size / 2)
        p.lineTo(x + size, y)
        p.lineTo(x, y - size / 2)
        p.close()
        c.setFillColor(colour)
        c.drawPath(p, stroke=0, fill=1)

    def rule(self, y, colour=LINE):
        self.c.setStrokeColor(colour)
        self.c.setLineWidth(0.7)
        self.c.line(MARGIN, y, PW - MARGIN, y)

    def footer(self, heading, body, url, qr_caption='Scan for the article'):
        """Hairline, a short pitch on the left, QR to the article on the right,
        pinned to the bottom margin exactly as the meteor cards are."""
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPDF
        from reportlab.graphics.barcode.qr import QrCodeWidget

        self.rule(96)
        self.text(MARGIN, 77, heading, F_SEMI, 9, INK)
        by = 65
        for line in wrap(body, F_REG, 7.8, CONTENT - 130):
            self.text(MARGIN, by, line, F_REG, 7.8, MUTED)
            by -= 9.6

        widget = QrCodeWidget(url, barLevel='M')
        b = widget.getBounds()
        d = Drawing(52, 52, transform=[52.0 / (b[2] - b[0]), 0, 0,
                                       52.0 / (b[3] - b[1]), 0, 0])
        d.add(widget)
        renderPDF.draw(d, self.c, PW - MARGIN - 52, MARGIN)
        self.text(PW - MARGIN - 62, 37, qr_caption, F_REG, 7, MUTED, 'right')
