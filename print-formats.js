/* ─────────────────────────────────────────────────────────────────────────────
   print-formats.js

   One definition of every print format, shared by:
     - prints.html            (the enquiry builder dropdowns and summary)
     - print-simulator.html   (the on-the-wall preview, drawn at real scale)

   Sizes are the SHORT and LONG edge in centimetres. Orientation is decided
   per image: a landscape photo prints landscape, a portrait photo prints
   portrait, so only the pair of numbers is stored here.

   Change a size here and both pages follow. The one place that does NOT
   follow automatically is the wording of the "What print sizes are
   available?" FAQ answer in prints.html, which is plain prose so that it
   still reads correctly with JavaScript turned off. Keep the two in step.
───────────────────────────────────────────────────────────────────────────── */

(function () {
  'use strict';

  /* Paper prints. A-series, short edge first. */
  const PAPER = [
    { v: 'A3', t: 'A3 paper print', short: 29.7, long: 42.0, in: '11.7 x 16.5 in' },
    { v: 'A4', t: 'A4 paper print', short: 21.0, long: 29.7, in: '8.3 x 11.7 in' },
    { v: 'A5', t: 'A5 paper print', short: 14.8, long: 21.0, in: '5.8 x 8.3 in' },
  ];

  /* Canvas prints, stretched over a wooden frame and ready to hang.
     These are the three standard stretched-canvas sizes. */
  const CANVAS = [
    { v: 'Canvas S', t: 'Canvas small, 30 x 40 cm',   short: 30, long: 40,  in: '11.8 x 15.7 in' },
    { v: 'Canvas M', t: 'Canvas medium, 50 x 70 cm',  short: 50, long: 70,  in: '19.7 x 27.6 in' },
    { v: 'Canvas L', t: 'Canvas large, 70 x 100 cm',  short: 70, long: 100, in: '27.6 x 39.4 in' },
  ];

  const DIGITAL = { v: 'Digital', t: 'Digital file' };

  /* How much frame shows around a framed paper print, per edge, in cm.
     The prints FAQ quotes this as approx. 2.5 cm (1 in). */
  const FRAME_BORDER_CM = 2.5;

  /* Depth of a stretched canvas, in cm. Used only to draw the wrapped
     side edge in the simulator. */
  const CANVAS_DEPTH_CM = 3;

  const ALL = PAPER.concat(CANVAS, [DIGITAL]);

  function byValue(v) {
    return ALL.find(f => f.v === v) || null;
  }

  /* 'paper' | 'canvas' | 'digital' | '' */
  function kindOf(v) {
    if (!v) return '';
    if (v === DIGITAL.v) return 'digital';
    if (CANVAS.some(f => f.v === v)) return 'canvas';
    if (PAPER.some(f => f.v === v)) return 'paper';
    return '';
  }

  function labelOf(v) {
    const f = byValue(v);
    return f ? f.t : '';
  }

  /* Short label for tables: "A3", "Canvas 50 x 70 cm", "Digital file". */
  function tableLabelOf(v) {
    const kind = kindOf(v);
    const f = byValue(v);
    if (!f) return '';
    if (kind === 'digital') return 'Digital file';
    if (kind === 'canvas') return 'Canvas ' + f.short + ' x ' + f.long + ' cm';
    return f.v;
  }

  /* Printed size in centimetres for a given orientation.
     landscape = true puts the long edge across. */
  function dimensions(v, landscape) {
    const f = byValue(v);
    if (!f || !f.short) return null;
    return landscape
      ? { w: f.long, h: f.short }
      : { w: f.short, h: f.long };
  }

  window.PRINT_FORMATS = {
    paper: PAPER,
    canvas: CANVAS,
    digital: DIGITAL,
    all: ALL,
    FRAME_BORDER_CM: FRAME_BORDER_CM,
    CANVAS_DEPTH_CM: CANVAS_DEPTH_CM,
    byValue: byValue,
    kindOf: kindOf,
    labelOf: labelOf,
    tableLabelOf: tableLabelOf,
    dimensions: dimensions,
  };
})();
