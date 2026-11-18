#!/usr/bin/env python3
"""Render a visualize template into one HTML file.

  render.py mermaid SOURCE.mmd OUT.html [--title T]
  render.py mockup BODY.html OUT.html [--title T] [--css FILE ...] [--lib NAME ...]
  render.py pin PACKAGE@VERSION/PATH

Libraries load from jsDelivr at exact versions with Subresource Integrity
hashes, so the browser refuses any script whose bytes differ from the pin.
`pin` downloads a file and prints the PINS entry for it.
Only the Python standard library is required.
"""

import argparse
import base64
import hashlib
import html
import mimetypes
import re
import sys
import urllib.request
from pathlib import Path

CDN = "https://cdn.jsdelivr.net/npm/"

# name: (path on the CDN, SRI hash, libraries it needs first)
# A library qualifies only if every script it runs comes through a tag here.
# Add or bump one with `render.py pin <package>@<exact version>/<file>`.
PINS = {
    "mermaid": ("mermaid@12.3.0/dist/mermaid.min.js",
                "sha384-HHW54r639fK42Ip0coGF3mz8oSiGn0eEoWNTLs75X7H63pLSDBa0Tqs0RwGmLlXE", []),
    "tailwind": ("@tailwindcss/browser@4.3.5/dist/index.global.js",
                 "sha384-t+qLIxS5zM/KF99/doWY+dxTsavdvgayaZt8A9ntLsUjEkiXzYl5M3Ij8zVFPL9j", []),
    # React 19 ships no UMD build, so React stays on 18 for plain <script> loading.
    "react-core": ("react@18.3.1/umd/react.production.min.js",
                   "sha384-DGyLxAyjq0f9SPpVevD6IgztCFlnMF6oW/XQGmfe+IsZ8TqEiDrcHkMLKI6fiB/Z", []),
    "react-dom": ("react-dom@18.3.1/umd/react-dom.production.min.js",
                  "sha384-gTGxhz21lVGYNMcdJOyq01Edg0jhn/c22nsx0kyqP0TxaV5WVdsSH1fSDUf5YJj1", ["react-core"]),
    "react-is": ("react-is@18.3.1/umd/react-is.production.min.js",
                 "sha384-XYVQ7LtYqgha4ByzNRLR6NHo9p0yVDvmTNuQkiIweU0U8WqLWBkH1L771VlP6fYx", []),
    "babel": ("@babel/standalone@8.1.2/babel.min.js",
              "sha384-UAlciMo5b2RD3a217OI/cCTcJmMLNExS2TKgjGbkN2s81rj5PMd2J2kKlsD3PS8x", []),
    "react": (None, None, ["react-core", "react-dom", "babel"]),
    "recharts": ("recharts@3.10.1/umd/Recharts.js",
                 "sha384-B2qLloNSIrxapii5UnBrm+3aDNWhVlmIFQONXg13tES0lEd7YUzh6lrjD3WSiwZ1",
                 ["react-core", "react-dom", "react-is"]),
}
MOCKUP_LIBS = ["tailwind", "react", "recharts"]
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def resolve(names, ordered=None):
    ordered = [] if ordered is None else ordered
    for name in names:
        if name not in ordered:
            resolve(PINS[name][2], ordered)
            ordered.append(name)
    return ordered


def script_tags(names):
    tags = []
    for name in resolve(names):
        path, integrity, _ = PINS[name]
        if path:
            tags.append(f'<script src="{CDN}{path}" integrity="{integrity}" crossorigin="anonymous"></script>')
    return "\n".join(tags)


def pin(path):
    if not re.match(r"^(@[^/]+/)?[^/@]+@\d+\.\d+\.\d+[^/]*/.+", path):
        sys.exit("render.py: pin needs an exact version, such as chart.js@4.6.1/dist/chart.umd.js")
    with urllib.request.urlopen(CDN + path, timeout=60) as response:
        data = response.read()
    digest = base64.b64encode(hashlib.sha384(data).digest()).decode("ascii")
    print(f'    "<name>": ("{path}",\n               "sha384-{digest}", []),')
    print(f"# {len(data)} bytes. Check that it loads no other scripts at runtime before adding it.")


def inline_images(markup, base):
    """Replace local <img src="..."> paths with data URLs so the page stands alone."""

    def replace(match):
        src = match.group(2)
        if re.match(r"^(data:|https?:|//)", src):
            return match.group(0)
        path = (base / src).resolve()
        if not path.is_file():
            sys.exit(f"render.py: image not found: {src}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"{match.group(1)}data:{mime};base64,{data}{match.group(3)}"

    return re.sub(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', replace, markup)


def fill(template, values):
    # One pass, so placeholder-like text inside the values is left alone.
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values.get(m.group(1), m.group(0)), template)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "pin":
        return pin(sys.argv[2])
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=["mermaid", "mockup"])
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--title", default="")
    parser.add_argument("--css", action="append", default=[], type=Path, help="app CSS to inline (mockup)")
    parser.add_argument("--lib", action="append", default=[], choices=MOCKUP_LIBS, help="library to load (mockup)")
    args = parser.parse_args()

    source = args.source.read_text(encoding="utf-8")
    title = html.escape(args.title or args.source.stem)

    if args.kind == "mermaid":
        template = (TEMPLATES / "mermaid.html").read_text(encoding="utf-8")
        values = {"TITLE": title, "HEAD": script_tags(["mermaid"]), "BODY": html.escape(source, quote=False)}
    else:
        template = (TEMPLATES / "mockup.html").read_text(encoding="utf-8")
        css = "\n".join(path.read_text(encoding="utf-8") for path in args.css)
        values = {
            "TITLE": title,
            "HEAD": script_tags(args.lib),
            "APP_CSS": css.replace("</style", "<\\/style"),
            "BODY": inline_images(source, args.source.resolve().parent),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(fill(template, values), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
