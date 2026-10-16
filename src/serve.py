#!/usr/bin/env python3
"""Build the site into dist/ (unless --no-build) and serve it locally.

  python3 src/serve.py
  python3 src/serve.py --port 8080
  python3 src/serve.py --no-build
"""
from __future__ import annotations

import argparse
import functools
import http.server
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def main() -> int:
    ap = argparse.ArgumentParser(description="Serve the built site from dist/")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-build", action="store_true", help="skip rebuild")
    args = ap.parse_args()

    if not args.no_build:
        # Run the builder in-process so SITE_ORIGIN etc. stay available.
        sys.path.insert(0, str(ROOT / "src"))
        import build as site_build  # noqa: WPS433
        code = site_build.build()
        if code != 0:
            return code
    elif not (DIST / "index.html").exists():
        print("dist/ is empty — run without --no-build, or: python3 src/build.py")
        return 1

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(DIST)
    )
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"serving dist/ at http://{args.host}:{args.port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
