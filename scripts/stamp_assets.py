"""Stamp content hashes onto the assets index.html loads.

GitHub Pages caches every file for ten minutes independently. Right after a
deploy a browser can therefore hold new markup beside a stale app.js — which
looks exactly like a broken feature: the element is in the page and nothing
ever fills it.

Versioning the URLs makes a deploy atomic from the browser's side. index.html
is the entry point and carries the hashes, so when it changes the browser is
forced to fetch the assets it names.

Run after anything that rewrites docs/. Idempotent.
"""
import os, re, sys, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

ASSETS = ["styles.css", "app.js", "data.json", "live.json"]


def digest(name):
    path = C.p("docs", name)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:10]


def main():
    html_path = C.p("docs", "index.html")
    with open(html_path, encoding="utf-8") as fh:
        html = fh.read()

    versions = {name: digest(name) for name in ASSETS}
    missing = [n for n, v in versions.items() if v is None]
    if missing:
        print(f"  missing, not stamped: {', '.join(missing)}")

    changed = 0
    for name, ver in versions.items():
        if ver is None:
            continue
        # match the file wherever it is referenced, with or without an old ?v=
        pattern = re.compile(rf'({re.escape(name)})(\?v=[0-9a-f]+)?(["\'])')
        html, n = pattern.subn(rf'\g<1>?v={ver}\g<3>', html)
        changed += n

    # app.js fetches the data itself, so hand it the versioned URLs rather than
    # letting it request unversioned copies the preload never warmed.
    block = ("<script>window.__ASSETS__=" +
             "{" + ",".join(f'"{n}":"{n}?v={v}"' for n, v in versions.items() if v) + "};</script>")
    if "window.__ASSETS__" in html:
        html = re.sub(r"<script>window\.__ASSETS__=.*?</script>", block, html, flags=re.S)
    else:
        html = html.replace("</head>", block + "\n</head>")

    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"  stamped {changed} references: " +
          ", ".join(f"{n}={v}" for n, v in versions.items() if v))


if __name__ == "__main__":
    main()
