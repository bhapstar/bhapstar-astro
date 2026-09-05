/* =========================================================
   tonight-core.js — bhapstar
   ---------------------------------------------------------
   Shared night-planning engine. Loaded by BOTH tonight.html
   (full ranked list) and start-here.html (compact top three),
   so the astronomy lives in exactly one place.

   Pure maths, no DOM and no network, so both pages keep
   working offline from the service worker cache.

   Exposes window.TonightCore:
     planNight(date, lat, lng, bortle, minAlt)
     moonPhaseName(phase)
     TARGETS, PRESETS, LABEL
   ========================================================= */
(function (global) {
  'use strict';

var RAD = Math.PI / 180;
  var J2000 = 2451545;
  var e = RAD * 23.4397;

  /* ── Core astronomy ─────────────────────────── */
  function toDays(date) { return date.valueOf() / 86400000 - 0.5 + 2440588 - J2000; }

  function rightAscension(l, b) {
    return Math.atan2(Math.sin(l) * Math.cos(e) - Math.tan(b) * Math.sin(e), Math.cos(l));
  }
  function declination(l, b) {
    return Math.asin(Math.sin(b) * Math.cos(e) + Math.cos(b) * Math.sin(e) * Math.sin(l));
  }
  function altitudeOf(H, phi, dec) {
    return Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H));
  }
  function azimuthOf(H, phi, dec) {
    return Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(dec) * Math.cos(phi));
  }
  function siderealTime(d, lw) { return RAD * (280.16 + 360.9856235 * d) - lw; }

  function sunCoords(d) {
    var M = RAD * (357.5291 + 0.98560028 * d);
    var C = RAD * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
    var L = M + C + RAD * 102.9372 + Math.PI;
    return { ra: rightAscension(L, 0), dec: declination(L, 0) };
  }

  function moonCoords(d) {
    var L = RAD * (218.316 + 13.176396 * d);
    var M = RAD * (134.963 + 13.064993 * d);
    var F = RAD * (93.272 + 13.229350 * d);
    var l = L + RAD * 6.289 * Math.sin(M);
    var b = RAD * 5.128 * Math.sin(F);
    return { ra: rightAscension(l, b), dec: declination(l, b), dist: 385001 - 20905 * Math.cos(M) };
  }

  function sunAltitude(date, lat, lng) {
    var d = toDays(date), c = sunCoords(d);
    return altitudeOf(siderealTime(d, RAD * -lng) - c.ra, RAD * lat, c.dec) / RAD;
  }

  function moonAltitude(date, lat, lng) {
    var d = toDays(date), c = moonCoords(d);
    return altitudeOf(siderealTime(d, RAD * -lng) - c.ra, RAD * lat, c.dec) / RAD;
  }

  function moonIllumination(date) {
    var d = toDays(date), s = sunCoords(d), m = moonCoords(d), sdist = 149598000;
    var phi = Math.acos(Math.sin(s.dec) * Math.sin(m.dec) +
              Math.cos(s.dec) * Math.cos(m.dec) * Math.cos(s.ra - m.ra));
    var inc = Math.atan2(sdist * Math.sin(phi), m.dist - sdist * Math.cos(phi));
    var angle = Math.atan2(
      Math.cos(s.dec) * Math.sin(s.ra - m.ra),
      Math.sin(s.dec) * Math.cos(m.dec) - Math.cos(s.dec) * Math.sin(m.dec) * Math.cos(s.ra - m.ra)
    );
    return {
      fraction: (1 + Math.cos(inc)) / 2,
      phase: 0.5 + 0.5 * inc * (angle < 0 ? -1 : 1) / Math.PI
    };
  }

  function targetAltAz(date, lat, lng, raHours, decDeg) {
    var d = toDays(date);
    var ra = raHours * 15 * RAD, dec = decDeg * RAD, phi = RAD * lat;
    var H = siderealTime(d, RAD * -lng) - ra;
    return { alt: altitudeOf(H, phi, dec) / RAD, az: (azimuthOf(H, phi, dec) / RAD + 180) % 360 };
  }

  function moonPhaseName(p) {
    if (p < 0.03 || p > 0.97) return 'New moon';
    if (p < 0.22) return 'Waxing crescent';
    if (p < 0.28) return 'First quarter';
    if (p < 0.47) return 'Waxing gibbous';
    if (p < 0.53) return 'Full moon';
    if (p < 0.72) return 'Waning gibbous';
    if (p < 0.78) return 'Last quarter';
    return 'Waning crescent';
  }

  /* ── Targets ─────────────────────────────────────────────────────────
     Every one links to its gallery page and carries its gallery image, so
     the list can show a thumbnail without a second network request.

     f     gallery image, root relative. The thumbnail is the same path
           with "thumbs/" inserted, which is how the rest of the site
           stores them. generate-start-here.py fails the build if either
           file is missing, so this cannot quietly drift.

     band  what the light actually is, which is the only thing that
           decides whether a filter helps:
             'narrow' emission line objects, strong in hydrogen alpha
                      and oxygen three. Narrowband filters work here.
             'broad'  continuum objects: galaxies, star clusters, dust
                      lit by starlight. Narrowband filters block the
                      very light you are trying to collect.

     k     what you can see or shoot it with under a good sky, in the
           order [eyes, phone, smart telescope, full rig]
           0 = not really, 1 = works, 2 = best results.

     b     the brightest sky each of those four still holds up under,
           as a Bortle number, same order. Above it the slot drops to
           nothing; at it exactly, a 2 drops to a 1. This is what makes
           the chips answer for the sky the reader actually has instead
           of quietly assuming a dark one. 9 means the sky is not the
           limiting factor.

     Both are judgement calls, not measurements. Edit freely.  */
  var TARGETS = [
    { n:"Orion Nebula (M42)",        ra:5.588,  dec:-5.39,  t:"emission", slug:"orion-nebula-m42",
      f:"images/orion-nebula-m42.webp", band:"narrow", k:[1,1,2,2], b:[7,6,9,9],
      d:"Bright enough to show colour in a short stack. The easiest deep sky object there is." },
    { n:"Flame &amp; Horsehead",     ra:5.683,  dec:-2.45,  t:"emission", slug:"flame-horsehead-nebulae",
      f:"images/flame-horsehead-nebulae.webp", band:"narrow", k:[0,0,1,2], b:[0,0,6,9],
      d:"The Horsehead is faint and wants a hydrogen alpha filter. The Flame comes easily." },
    { n:"Rosette Nebula (NGC 2244)", ra:6.528,  dec:4.95,   t:"emission", slug:"rosette-nebula-ngc2244",
      f:"images/rosette-nebula-ngc2244.webp", band:"narrow", k:[0,0,2,2], b:[0,0,8,9],
      d:"Big and round, and a good match for a short focal length. Responds well to dual narrowband." },
    { n:"Jellyfish Nebula (IC 443)", ra:6.283,  dec:22.78,  t:"emission", slug:"jellyfish-nebula-ic443",
      f:"images/jellyfish-nebula-ic443.webp", band:"narrow", k:[0,0,1,2], b:[0,0,6,9],
      d:"A supernova remnant. Faint, so give it plenty of total time." },
    { n:"Monkey Head (NGC 2174)",    ra:6.162,  dec:20.50,  t:"emission", slug:"monkey-head-nebula-ngc2174",
      f:"images/monkey-head-nebula-ngc2174.webp", band:"narrow", k:[0,0,1,2], b:[0,0,7,9],
      d:"Strong in hydrogen alpha, which makes it a solid city target with the right filter." },
    { n:"Christmas Tree (NGC 2264)", ra:6.683,  dec:9.88,   t:"emission", slug:"christmas-tree-nebula-ngc2264",
      f:"images/christmas-tree-nebula-ngc2264.webp", band:"narrow", k:[0,0,2,2], b:[0,0,7,9],
      d:"A star cluster sitting inside faint nebulosity. The cluster shows up fast." },
    { n:"Thor's Helmet (NGC 2359)",  ra:7.310,  dec:-13.20, t:"emission", slug:"thors-helmet-ngc2359",
      f:"images/thors-helmet-ngc2359.webp", band:"narrow", k:[0,0,1,2], b:[0,0,6,9],
      d:"Small and faint, but the shape is unmistakable once you have the signal." },
    { n:"Eagle Nebula (M16)",        ra:18.313, dec:-13.78, t:"emission", slug:"eagle-nebula-m16",
      f:"images/eagle-nebula-m16-2.webp", band:"narrow", k:[0,0,2,2], b:[0,0,8,9],
      d:"Home of the Pillars of Creation. Never climbs very high from northern latitudes, so catch it near its peak." },
    { n:"Lobster Nebula (NGC 6357)", ra:17.420, dec:-34.20, t:"emission", slug:"lobster-nebula-ngc6357",
      f:"images/lobster-nebula-ngc6357.webp", band:"narrow", k:[0,0,1,2], b:[0,0,6,9],
      d:"Very far south. Only worth it if you have a clear, low southern horizon." },
    { n:"Cat's Paw (NGC 6334)",      ra:17.347, dec:-36.10, t:"emission", slug:"cats-paw-nebula-ngc6334",
      f:"images/cats_paw_nebula_ngc6334.webp", band:"narrow", k:[0,0,1,2], b:[0,0,6,9],
      d:"Even lower than the Lobster. A genuine challenge from the northern hemisphere." },
    { n:"Andromeda Galaxy (M31)",    ra:0.712,  dec:41.27,  t:"galaxy",   slug:"andromeda-galaxy-m31",
      f:"images/andromeda-galaxy-m31.webp", band:"broad", k:[1,1,2,2], b:[6,4,7,8],
      d:"The biggest galaxy in the sky. Broadband, so it hates light pollution and moonlight." },
    { n:"Triangulum Galaxy (M33)",   ra:1.565,  dec:30.66,  t:"galaxy",   slug:"triangulum-galaxy-m33",
      f:"images/triangulum-galaxy-m33.webp", band:"broad", k:[1,0,2,2], b:[1,0,6,8],
      d:"Face on and spread out, which makes it dimmer than it looks on paper. Wants dark skies." },
    { n:"Pinwheel Galaxy (M101)",    ra:14.053, dec:54.35,  t:"galaxy",   slug:"pinwheel-galaxy-m101",
      f:"images/pinwheel-galaxy-m101.webp", band:"broad", k:[0,0,1,2], b:[0,0,5,7],
      d:"Beautiful spiral arms, but low surface brightness. Dark skies or nothing." },
    { n:"Bode's &amp; Cigar (M81/M82)", ra:9.927, dec:69.07, t:"galaxy",  slug:"bodes-cigar-galaxies-m81-m82",
      f:"images/bodes-cigar-galaxies-m81-m82-2.webp", band:"broad", k:[0,0,2,2], b:[0,0,6,8],
      d:"Two very different galaxies in one frame. Both are reasonably bright." },
    { n:"Needle Galaxy (NGC 4565)",  ra:12.605, dec:25.99,  t:"galaxy",   slug:"needle-galaxy-ngc4565",
      f:"images/needle-galaxy-ngc4565.webp", band:"broad", k:[0,0,1,2], b:[0,0,5,7],
      d:"Edge on and razor thin. Small, so it rewards a longer focal length." },
    { n:"Leo Triplet",               ra:11.337, dec:13.00,  t:"galaxy",   slug:"leo-triplet-m65-m66-ngc3628",
      f:"images/leo-triplet-m65-m66-ngc3628.webp", band:"broad", k:[0,0,1,2], b:[0,0,5,7],
      d:"Three galaxies in one field. A satisfying target once spring comes around." },
    { n:"Pleiades (M45)",            ra:3.783,  dec:24.12,  t:"cluster",  slug:"pleiades-m45",
      f:"images/pleiades-m45.webp", band:"broad", k:[2,1,2,2], b:[8,6,9,9],
      d:"Bright stars wrapped in blue dust. Easy to capture, hard to keep the stars small." },
    { n:"Little Beehive (M41)",      ra:6.767,  dec:-20.73, t:"cluster",  slug:"little-beehive-cluster-m41",
      f:"images/little-beehive-cluster-m41.webp", band:"broad", k:[1,0,2,2], b:[5,0,8,9],
      d:"An open cluster that works even under a bright moon. Good filler target." },
    { n:"Milky Way core",            ra:17.760, dec:-28.94, t:"wide",     slug:"the-milky-way",
      f:"images/the_milky_way.webp", band:"broad", k:[2,2,0,1], b:[4,4,0,5],
      d:"Camera and wide lens, not a telescope. Needs genuinely dark skies and no moon." }
  ];

  /* ── Filters ──────────────────────────────────────────────────────────
     Which filter earns its place depends on the object, the sky and the
     moon during that object's own window, not on the object alone. So
     this is worked out per target every time the plan is rebuilt.

     moonLoad is 0 to 1: how much moonlight actually lands on the target
     while it is up and worth shooting. It already accounts for the
     phase, how high the moon climbs and how far it sits from the target,
     so a full moon low in the opposite half of the sky scores far below
     a half moon sitting next to the object.                            */
  var FILTERS = {
    none: { s:'No filter',        l:'No filter needed',
            w:'Your sky is dark and the moon is out of the way. A filter here would cost you more light than it saves.' },
    opt:  { s:'Narrowband optional', l:'Narrowband optional, not required',
            w:'Dark sky, no moon to speak of, so this one records without a filter and keeps its natural star colour. A dual narrowband still lifts the nebula clear of the background if you would rather have contrast than colour, at the cost of needing longer on it.' },
    lp:   { s:'Light pollution',  l:'Light pollution filter',
            w:'A broadband filter cuts the orange glow of streetlights while letting starlight through. Narrowband would block the very light this object gives off.' },
    moon: { s:'None will help',   l:'No filter separates this from moonlight',
            w:'Moonlight is sunlight bounced off rock, so it carries the same broad spread of colour as the starlight you are collecting. Nothing can filter one out and leave the other. Shoot this when the moon is down, or accept the loss of contrast.' },
    wide: { s:'Wide narrowband',  l:'Wide narrowband, L-Quad style',
            w:'A wide multi-band filter holds back skyglow without throwing away the star colour. A good middle rung for a nebula from a suburban sky, or under a modest moon.' },
    nb:   { s:'7nm narrowband',   l:'Dual narrowband, around 7nm',
            w:'Passes only hydrogen alpha and oxygen three. This is the filter that makes emission nebulae work from a bright sky or under a moon.' },
    xnb:  { s:'3nm narrowband',   l:'Extreme narrowband, around 3nm',
            w:'A very tight pass band. It throws away most of the sky and keeps the nebula, which is what a city sky or a bright moon calls for. Needs longer exposures to make up for it.' }
  };

  /* Emission objects climb the ladder as the sky brightens or the moon
     moves in. Continuum objects cannot: a narrowband filter would block
     the starlight they are made of, and against moonlight no filter
     helps at all, which is worth saying plainly rather than suggesting
     a filter that will not do the job. */
  function filterFor(target, bortle, moonLoad) {
    var load = moonLoad || 0;
    if (target.band === 'narrow') {
      if (bortle >= 8 || (bortle >= 6 && load > 0.30)) return 'xnb';
      if (bortle >= 6 || load > 0.22) return 'nb';
      if (bortle >= 4 || load > 0.06) return 'wide';
      return 'opt';
    }
    if (bortle >= 5) return 'lp';
    /* Star clusters are made of bright points rather than faint spread
       out light, so a moon costs them contrast they can spare. The
       warning is for the things that genuinely lose the night to it. */
    if (load > 0.25 && target.t !== 'cluster') return 'moon';
    return 'none';
  }

  /* ── Kit ── */
  var KIT = [
    { key:'eye',   s:'Eyes',  l:'Naked eye' },
    { key:'phone', s:'Phone', l:'Phone on a tripod' },
    { key:'smart', s:'Smart', l:'Smart telescope' },
    { key:'rig',   s:'Rig',   l:'Telescope, mount and camera' }
  ];
  var KIT_STATE = ['Not worth trying', 'Works', 'Best results'];

  /* The chips a target earns under a given sky. Past its ceiling a slot
     goes to nothing; at the ceiling exactly, "best results" softens to
     "works", because the last usable Bortle class is never where an
     object looks its best. */
  function kitFor(target, bortle) {
    var k = target.k || [0, 0, 0, 0];
    var b = target.b || [9, 9, 9, 9];
    var out = [], i;
    for (i = 0; i < k.length; i++) {
      if (!k[i] || bortle > b[i]) out.push(0);
      else if (bortle === b[i]) out.push(Math.min(k[i], 1));
      else out.push(k[i]);
    }
    return out;
  }

  /* The thumbnail path for a target, from its gallery image. */
  function thumbFor(target) {
    return target.f ? target.f.replace(/^images\//, 'images/thumbs/') : '';
  }

  var LABEL = { emission:'Emission nebula', galaxy:'Galaxy', cluster:'Star cluster', wide:'Wide field' };

  /* ── Scoring ────────────────────────────────── */
  function bortleFactor(type, b) {
    if (type === 'emission') return b >= 7 ? 0.75 : 1.0;
    if (type === 'wide')     return b >= 7 ? 0.05 : (b >= 5 ? 0.55 : 1.0);
    if (type === 'cluster')  return b >= 7 ? 0.45 : (b >= 5 ? 0.80 : 1.0);
    return b >= 7 ? 0.12 : (b >= 5 ? 0.60 : 1.0);
  }

  /* Angle between two points on the sky, in degrees. */
  function separation(ra1, dec1, ra2, dec2) {
    var c = Math.sin(dec1) * Math.sin(dec2) +
            Math.cos(dec1) * Math.cos(dec2) * Math.cos(ra1 - ra2);
    return Math.acos(Math.max(-1, Math.min(1, c))) / RAD;
  }

  /* How much the moon costs you at one instant, on one target, 0 to 1.

     Three things decide it and all three matter. A moon below the
     horizon costs nothing at all. A moon just clearing the horizon
     shines through a long path of atmosphere and lights very little of
     the sky, so it is worth much less than a moon overhead. And a moon
     sitting next to the target is a different problem from a moon in
     the opposite half of the sky, which is why a target's own window is
     the only honest place to measure this. */
  function moonCost(illum, moonAlt, sep) {
    if (moonAlt <= 0) return 0;
    var altW = Math.min(1, Math.sin(moonAlt * RAD) / Math.sin(25 * RAD));
    var sepW = sep <= 30 ? 1
             : sep >= 100 ? 0.35
             : 1 - 0.65 * (sep - 30) / 70;
    return illum * altW * sepW;
  }

  function planNight(date, lat, lng, bortle, minAlt) {
    var start = new Date(date); start.setHours(12, 0, 0, 0);
    var STEP = 5, N = (24 * 60) / STEP, i;

    /* Take the longest unbroken stretch of astronomical darkness, not simply
       the first and last dark sample. If the device time zone does not match
       the coordinates being planned for, the noon-to-noon window can clip two
       separate nights, and first-to-last would report a 24 hour night. */
    var runs = [], cur = null;
    for (i = 0; i <= N; i++) {
      var d = new Date(start.getTime() + i * STEP * 60000);
      if (sunAltitude(d, lat, lng) < -18) {
        if (!cur) { cur = []; runs.push(cur); }
        cur.push(d);
      } else {
        cur = null;
      }
    }
    if (!runs.length) return { dark: false, targets: [] };

    var dark = runs[0];
    for (i = 1; i < runs.length; i++) if (runs[i].length > dark.length) dark = runs[i];

    var darkStart = dark[0], darkEnd = dark[dark.length - 1];
    var ill = moonIllumination(darkStart);

    /* The moon once, for every sample of the dark window, rather than
       once per target per sample. Where it sits is the expensive part
       and it does not depend on which object you are pointing at. */
    var moon = [], moonUp = 0, moonUpFrom = null, moonUpTo = null;
    for (i = 0; i < dark.length; i++) {
      var md = toDays(dark[i]);
      var mc = moonCoords(md);
      var mAlt = altitudeOf(siderealTime(md, RAD * -lng) - mc.ra, RAD * lat, mc.dec) / RAD;
      moon.push({ alt: mAlt, ra: mc.ra, dec: mc.dec });
      if (mAlt > 0) {
        moonUp++;
        if (!moonUpFrom) moonUpFrom = dark[i];
        moonUpTo = dark[i];
      }
    }
    var moonUpFrac = moonUp / dark.length;

    var out = [];
    for (var k = 0; k < TARGETS.length; k++) {
      var tg = TARGETS[k];
      var tRa = tg.ra * 15 * RAD, tDec = tg.dec * RAD;
      var maxAlt = -90, above = 0, winStart = null, winEnd = null;
      var loadSum = 0, moonUpInWindow = 0;

      for (i = 0; i < dark.length; i++) {
        var p = targetAltAz(dark[i], lat, lng, tg.ra, tg.dec);
        if (p.alt > maxAlt) maxAlt = p.alt;
        if (p.alt >= minAlt) {
          above++;
          if (!winStart) winStart = dark[i];
          winEnd = dark[i];
          loadSum += moonCost(ill.fraction, moon[i].alt,
                              separation(tRa, tDec, moon[i].ra, moon[i].dec));
          if (moon[i].alt > 0) moonUpInWindow++;
        }
      }

      var hours = above * STEP / 60;
      if (hours <= 0.5) continue;

      /* Averaged over the target's own window, not the whole night. An
         object that sets before moonrise is not competing with the moon,
         and the old whole-night average said it was. */
      var moonLoad = loadSum / above;

      var bf = bortleFactor(tg.t, bortle);
      var altScore = Math.max(0, Math.min(1, (maxAlt - minAlt) / 45));
      var timeScore = Math.min(1, hours / 5);

      /* Emission objects care far less, because the light you want from
         them sits in two narrow lines a filter can keep. */
      var penalty = moonLoad * (tg.band === 'narrow' ? 0.35 : 1.0);
      var score = (0.45 * altScore + 0.55 * timeScore) * bf * (1 - 0.75 * penalty);

      out.push({
        tg: tg, maxAlt: maxAlt, hours: hours,
        winStart: winStart, winEnd: winEnd, score: score,
        moonLoad: moonLoad, moonUpFrac: moonUpInWindow / above,
        bf: bf
      });
    }

    out.sort(function (a, b) { return b.score - a.score; });
    return {
      dark: true, darkStart: darkStart, darkEnd: darkEnd,
      moonIll: ill.fraction, moonPhase: ill.phase,
      moonUpFrac: moonUpFrac, moonUpFrom: moonUpFrom, moonUpTo: moonUpTo,
      targets: out
    };
  }

  global.TonightCore = {
    planNight: planNight,
    moonIllumination: moonIllumination,
    moonPhaseName: moonPhaseName,
    targetAltAz: targetAltAz,
    TARGETS: TARGETS,
    LABEL: LABEL,
    FILTERS: FILTERS,
    filterFor: filterFor,
    KIT: KIT,
    kitFor: kitFor,
    KIT_STATE: KIT_STATE,
    thumbFor: thumbFor
  };
})(window);
