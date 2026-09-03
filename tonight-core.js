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

     k     what you can see or shoot it with, in the order
             [eyes, phone, smart telescope, full rig]
           0 = not really, 1 = works, 2 = best results.
           These are judgement calls, not measurements. Edit freely.  */
  var TARGETS = [
    { n:"Orion Nebula (M42)",        ra:5.588,  dec:-5.39,  t:"emission", slug:"orion-nebula-m42",
      f:"images/orion-nebula-m42.webp", band:"narrow", k:[1,1,2,2],
      d:"Bright enough to show colour in a short stack. The easiest deep sky object there is." },
    { n:"Flame &amp; Horsehead",     ra:5.683,  dec:-2.45,  t:"emission", slug:"flame-horsehead-nebulae",
      f:"images/flame-horsehead-nebulae.webp", band:"narrow", k:[0,0,1,2],
      d:"The Horsehead is faint and wants a hydrogen alpha filter. The Flame comes easily." },
    { n:"Rosette Nebula (NGC 2244)", ra:6.528,  dec:4.95,   t:"emission", slug:"rosette-nebula-ngc2244",
      f:"images/rosette-nebula-ngc2244.webp", band:"narrow", k:[0,0,2,2],
      d:"Big and round, and a good match for a short focal length. Responds well to dual narrowband." },
    { n:"Jellyfish Nebula (IC 443)", ra:6.283,  dec:22.78,  t:"emission", slug:"jellyfish-nebula-ic443",
      f:"images/jellyfish-nebula-ic443.webp", band:"narrow", k:[0,0,1,2],
      d:"A supernova remnant. Faint, so give it plenty of total time." },
    { n:"Monkey Head (NGC 2174)",    ra:6.162,  dec:20.50,  t:"emission", slug:"monkey-head-nebula-ngc2174",
      f:"images/monkey-head-nebula-ngc2174.webp", band:"narrow", k:[0,0,1,2],
      d:"Strong in hydrogen alpha, which makes it a solid city target with the right filter." },
    { n:"Christmas Tree (NGC 2264)", ra:6.683,  dec:9.88,   t:"emission", slug:"christmas-tree-nebula-ngc2264",
      f:"images/christmas-tree-nebula-ngc2264.webp", band:"narrow", k:[0,0,2,2],
      d:"A star cluster sitting inside faint nebulosity. The cluster shows up fast." },
    { n:"Thor's Helmet (NGC 2359)",  ra:7.310,  dec:-13.20, t:"emission", slug:"thors-helmet-ngc2359",
      f:"images/thors-helmet-ngc2359.webp", band:"narrow", k:[0,0,1,2],
      d:"Small and faint, but the shape is unmistakable once you have the signal." },
    { n:"Eagle Nebula (M16)",        ra:18.313, dec:-13.78, t:"emission", slug:"eagle-nebula-m16",
      f:"images/eagle-nebula-m16-2.webp", band:"narrow", k:[0,0,2,2],
      d:"Home of the Pillars of Creation. Never climbs very high from northern latitudes, so catch it near its peak." },
    { n:"Lobster Nebula (NGC 6357)", ra:17.420, dec:-34.20, t:"emission", slug:"lobster-nebula-ngc6357",
      f:"images/lobster-nebula-ngc6357.webp", band:"narrow", k:[0,0,1,2],
      d:"Very far south. Only worth it if you have a clear, low southern horizon." },
    { n:"Cat's Paw (NGC 6334)",      ra:17.347, dec:-36.10, t:"emission", slug:"cats-paw-nebula-ngc6334",
      f:"images/cats_paw_nebula_ngc6334.webp", band:"narrow", k:[0,0,1,2],
      d:"Even lower than the Lobster. A genuine challenge from the northern hemisphere." },
    { n:"Andromeda Galaxy (M31)",    ra:0.712,  dec:41.27,  t:"galaxy",   slug:"andromeda-galaxy-m31",
      f:"images/andromeda-galaxy-m31.webp", band:"broad", k:[1,1,2,2],
      d:"The biggest galaxy in the sky. Broadband, so it hates light pollution and moonlight." },
    { n:"Triangulum Galaxy (M33)",   ra:1.565,  dec:30.66,  t:"galaxy",   slug:"triangulum-galaxy-m33",
      f:"images/triangulum-galaxy-m33.webp", band:"broad", k:[1,0,2,2],
      d:"Face on and spread out, which makes it dimmer than it looks on paper. Wants dark skies." },
    { n:"Pinwheel Galaxy (M101)",    ra:14.053, dec:54.35,  t:"galaxy",   slug:"pinwheel-galaxy-m101",
      f:"images/pinwheel-galaxy-m101.webp", band:"broad", k:[0,0,1,2],
      d:"Beautiful spiral arms, but low surface brightness. Dark skies or nothing." },
    { n:"Bode's &amp; Cigar (M81/M82)", ra:9.927, dec:69.07, t:"galaxy",  slug:"bodes-cigar-galaxies-m81-m82",
      f:"images/bodes-cigar-galaxies-m81-m82-2.webp", band:"broad", k:[0,0,2,2],
      d:"Two very different galaxies in one frame. Both are reasonably bright." },
    { n:"Needle Galaxy (NGC 4565)",  ra:12.605, dec:25.99,  t:"galaxy",   slug:"needle-galaxy-ngc4565",
      f:"images/needle-galaxy-ngc4565.webp", band:"broad", k:[0,0,1,2],
      d:"Edge on and razor thin. Small, so it rewards a longer focal length." },
    { n:"Leo Triplet",               ra:11.337, dec:13.00,  t:"galaxy",   slug:"leo-triplet-m65-m66-ngc3628",
      f:"images/leo-triplet-m65-m66-ngc3628.webp", band:"broad", k:[0,0,1,2],
      d:"Three galaxies in one field. A satisfying target once spring comes around." },
    { n:"Pleiades (M45)",            ra:3.783,  dec:24.12,  t:"cluster",  slug:"pleiades-m45",
      f:"images/pleiades-m45.webp", band:"broad", k:[2,1,2,2],
      d:"Bright stars wrapped in blue dust. Easy to capture, hard to keep the stars small." },
    { n:"Little Beehive (M41)",      ra:6.767,  dec:-20.73, t:"cluster",  slug:"little-beehive-cluster-m41",
      f:"images/little-beehive-cluster-m41.webp", band:"broad", k:[1,0,2,2],
      d:"An open cluster that works even under a bright moon. Good filler target." },
    { n:"Milky Way core",            ra:17.760, dec:-28.94, t:"wide",     slug:"the-milky-way",
      f:"images/the_milky_way.webp", band:"broad", k:[2,2,0,1],
      d:"Camera and wide lens, not a telescope. Needs genuinely dark skies and no moon." }
  ];

  /* ── Filters ──────────────────────────────────────────────────────────
     Five rungs, from nothing to a 3nm dual narrowband. Which rung applies
     depends on the object and on the night, not on the object alone, so
     this is worked out per target every time the plan is rebuilt.       */
  var FILTERS = {
    none: { s:'No filter',        l:'No filter needed',
            w:'Your sky is dark enough that a filter would cost you more light than it saves.' },
    lp:   { s:'Light pollution',  l:'Light pollution filter',
            w:'A broadband filter cuts the orange glow of streetlights while letting starlight through. Narrowband would block the very light this object gives off.' },
    wide: { s:'Wide narrowband',  l:'Wide narrowband, L-Quad style',
            w:'A wide multi-band filter holds back skyglow without throwing away the star colour. A good middle rung for a nebula from a suburban sky.' },
    nb:   { s:'7nm narrowband',   l:'Dual narrowband, around 7nm',
            w:'Passes only hydrogen alpha and oxygen three. This is the filter that makes emission nebulae work from a bright sky or under a moon.' },
    xnb:  { s:'3nm narrowband',   l:'Extreme narrowband, around 3nm',
            w:'A very tight pass band. It throws away most of the sky and keeps the nebula, which is what a city sky or a bright moon calls for. Needs longer exposures to make up for it.' }
  };

  /* Continuum objects never go past a light pollution filter, because a
     narrowband filter blocks the starlight they are made of. Emission
     objects climb the ladder as the sky gets brighter or the moon rises. */
  function filterFor(target, bortle, moonHit) {
    var heavyMoon = moonHit > 0.4;
    if (target.band === 'narrow') {
      if (bortle >= 8 || (bortle >= 6 && heavyMoon)) return 'xnb';
      if (bortle >= 6 || heavyMoon) return 'nb';
      if (bortle >= 4) return 'wide';
      return 'none';
    }
    if (bortle >= 6 || heavyMoon) return 'lp';
    return 'none';
  }

  /* ── Kit ── */
  var KIT = [
    { key:'eye',   s:'Eyes',  l:'Naked eye' },
    { key:'phone', s:'Phone', l:'Phone on a tripod' },
    { key:'smart', s:'Smart', l:'Smart telescope' },
    { key:'rig',   s:'Rig',   l:'Telescope, mount and camera' }
  ];
  var KIT_STATE = ['Not really', 'Works', 'Best results'];

  /* The thumbnail path for a target, from its gallery image. */
  function thumbFor(target) {
    return target.f ? target.f.replace(/^images\//, 'images/thumbs/') : '';
  }

  var LABEL = { emission:'Emission nebula', galaxy:'Galaxy', cluster:'Star cluster', wide:'Wide field' };

  /* ── Direction ────────────────────────────────
     Azimuth comes out of targetAltAz as a compass bearing, 0 north,
     90 east, 180 south, 270 west. Sixteen points rather than eight,
     because "east" for something sitting at 112 degrees is misleading
     when you are working out whether a building is in the way. */
  var COMPASS = [
    'north', 'north-north-east', 'north-east', 'east-north-east',
    'east', 'east-south-east', 'south-east', 'south-south-east',
    'south', 'south-south-west', 'south-west', 'west-south-west',
    'west', 'west-north-west', 'north-west', 'north-north-west'
  ];
  var COMPASS_SHORT = [
    'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
    'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
  ];

  function compassIndex(az) {
    return Math.round(((az % 360) + 360) % 360 / 22.5) % 16;
  }
  function compassName(az)  { return COMPASS[compassIndex(az)]; }
  function compassShort(az) { return COMPASS_SHORT[compassIndex(az)]; }

  /* Within about ten degrees of the zenith the azimuth stops meaning
     anything useful: the object is nearly straight up, so a small change
     in position swings the bearing right round. Saying "overhead" there
     is both more honest and more use to somebody deciding whether a
     building is in the way. */
  var ZENITH_CUTOFF = 80;
  function directionText(alt, az) {
    return alt >= ZENITH_CUTOFF ? 'overhead' : compassName(az);
  }
  function directionShort(alt, az) {
    return alt >= ZENITH_CUTOFF ? 'UP' : compassShort(az);
  }

  /* ── Scoring ────────────────────────────────── */
  function bortleFactor(type, b) {
    if (type === 'emission') return b >= 7 ? 0.75 : 1.0;
    if (type === 'wide')     return b >= 7 ? 0.05 : (b >= 5 ? 0.55 : 1.0);
    if (type === 'cluster')  return b >= 7 ? 0.45 : (b >= 5 ? 0.80 : 1.0);
    return b >= 7 ? 0.12 : (b >= 5 ? 0.60 : 1.0);
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

    var moonUp = 0;
    for (i = 0; i < dark.length; i++) if (moonAltitude(dark[i], lat, lng) > 0) moonUp++;
    var moonUpFrac = moonUp / dark.length;

    var out = [];
    for (var k = 0; k < TARGETS.length; k++) {
      var tg = TARGETS[k];
      var maxAlt = -90, above = 0, winStart = null, winEnd = null;
      var peakAt = null, peakAz = 0;

      for (i = 0; i < dark.length; i++) {
        var p = targetAltAz(dark[i], lat, lng, tg.ra, tg.dec);
        if (p.alt > maxAlt) { maxAlt = p.alt; peakAz = p.az; peakAt = dark[i]; }
        if (p.alt >= minAlt) {
          above++;
          if (!winStart) winStart = dark[i];
          winEnd = dark[i];
        }
      }

      var hours = above * STEP / 60;
      if (hours <= 0.5) continue;

      /* Nine samples evenly across the usable window, so the compass dial
         can draw the actual path the object takes rather than guessing a
         curve through three points. The peak always falls inside this
         window: maxAlt is at least minAlt for anything that survives the
         check above, so the highest moment is by definition part of the
         stretch that cleared it. */
      var track = [], TRACK_STEPS = 8, span = winEnd - winStart;
      for (var j = 0; j <= TRACK_STEPS; j++) {
        var tAt = new Date(winStart.getTime() + span * j / TRACK_STEPS);
        var q = targetAltAz(tAt, lat, lng, tg.ra, tg.dec);
        track.push({ alt: q.alt, az: q.az, at: tAt });
      }

      var moonHit = ill.fraction * moonUpFrac * (tg.t === 'emission' ? 0.35 : 1.0);
      var bf = bortleFactor(tg.t, bortle);
      var altScore = Math.max(0, Math.min(1, (maxAlt - minAlt) / 45));
      var timeScore = Math.min(1, hours / 5);
      var score = (0.45 * altScore + 0.55 * timeScore) * bf * (1 - 0.75 * moonHit);

      out.push({
        tg: tg, maxAlt: maxAlt, hours: hours,
        winStart: winStart, winEnd: winEnd, score: score,
        moonHit: moonHit, bf: bf,
        peakAt: peakAt, peakAz: peakAz, track: track
      });
    }

    out.sort(function (a, b) { return b.score - a.score; });
    return {
      dark: true, darkStart: darkStart, darkEnd: darkEnd,
      moonIll: ill.fraction, moonPhase: ill.phase, moonUpFrac: moonUpFrac,
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
    KIT_STATE: KIT_STATE,
    thumbFor: thumbFor,
    compassName: compassName,
    compassShort: compassShort,
    directionText: directionText,
    directionShort: directionShort
  };
})(window);
