#!/usr/bin/env python3
"""
build.py — bhapstar
-------------------------------------------------------------
Runs every generator in the one order that actually works, so the sequence
does not have to be remembered or repeated in the workflow file.

    python build.py            # everything, in order
    python build.py gear share # just those stages, still in the right order
    python build.py --list     # show the stages and stop

Why the order matters:

  1. gear     Gear pages must exist on disk before share pages are built,
              because generate-share-pages.py only turns a capture spec into
              a link if gear/<slug>.html is already there. Build share first
              and a brand new piece of kit renders as plain text until the
              next run.
  2. article  Article pages. Independent of the others, but built before
              share so every internal link target exists by the time the
              share pages are written.
  3. share    One page per gallery entry, with capture specs linked to the
              gear pages produced in step 1.
  4. schema   Injects JSON-LD into gallery.html and field_notes.html. Runs
              after the pages so it can never describe a stale site.
  5. sitemap  Built from site-data.json rather than from disk, so it is
              order-independent, but it belongs last as the final index of
              everything above.
  6. starthere  start-here.html, the guided path. Built after the article
              pages so every link it writes points at a file already on disk.
  7. feed     feed.xml, the RSS feed. Also built from site-data.json, so it
              is order-independent too, but it runs last for the same reason
              as the sitemap: it describes everything above it.

Layout this expects:

    build.py            this file, at the repository root
    scripts/            the five generators
    content/articles/   hand-written article prose, one file per slug
    content/gear/       hand-written gear review prose, one file per slug
    site-data.json      the single source of data for all of it
    articles/ gear/ share/   generated output, never edited by hand

The generators resolve their paths relative to the working directory, so
this script runs each one with the repository root as its working
directory regardless of where build.py was invoked from.
"""

import os
import subprocess
import sys

# Stage name -> script filename. Order here is the build order.
SCRIPTS = "scripts"

STAGES = [
    ("gear",    "generate-gear-pages.py"),
    ("article", "generate-article-pages.py"),
    ("share",   "generate-share-pages.py"),
    ("schema",  "generate-schema.py"),
    ("sitemap", "generate-sitemap.py"),
    ("starthere", "generate-start-here.py"),
    ("feed",    "generate-feed.py"),
]

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(name, script):
    """Run one generator. Returns True on success."""
    print(f"\n\033[1m── {name} ── {SCRIPTS}/{script}\033[0m", flush=True)
    path = os.path.join(ROOT, SCRIPTS, script)
    if not os.path.exists(path):
        print(f"  ! {SCRIPTS}/{script} not found, skipped", file=sys.stderr)
        return False
    # cwd is the repo root, not scripts/, because every generator reads
    # site-data.json and writes its output using root-relative paths.
    result = subprocess.run([sys.executable, path], cwd=ROOT)
    if result.returncode != 0:
        print(f"  ! {script} exited with code {result.returncode}",
              file=sys.stderr)
        return False
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = [a for a in sys.argv[1:] if a.startswith("-")]

    if "--list" in flags or "-l" in flags:
        print("Build stages, in order:")
        for i, (name, script) in enumerate(STAGES, 1):
            print(f"  {i}. {name:<8} {SCRIPTS}/{script}")
        return 0

    if args:
        unknown = [a for a in args if a not in dict(STAGES)]
        if unknown:
            print(f"Unknown stage(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"Valid stages: {', '.join(n for n, _ in STAGES)}",
                  file=sys.stderr)
            return 2
        # Filter rather than reorder, so a subset still runs in build order.
        stages = [(n, s) for n, s in STAGES if n in args]
    else:
        stages = STAGES

    failed = []
    for name, script in stages:
        if not run(name, script):
            failed.append(name)
            # Later stages depend on earlier ones, so stop rather than
            # generating pages against a half-built site.
            print("\nStopping: later stages depend on this one.",
                  file=sys.stderr)
            break

    print()
    if failed:
        print(f"\033[1mBuild failed at: {', '.join(failed)}\033[0m",
              file=sys.stderr)
        return 1
    print(f"\033[1mBuild complete: {len(stages)} stage(s) in order "
          f"({', '.join(n for n, _ in stages)}).\033[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
