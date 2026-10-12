#!/usr/bin/env python3
"""Check deployed pages and their local assets without submitting any form."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []
        self.h1 = 0
        self.main = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        fields = dict(attrs)
        self.h1 += tag == "h1"
        self.main += tag == "main"
        attribute = {"a": "href", "img": "src", "link": "href", "script": "src"}.get(tag)
        if attribute and fields.get(attribute):
            self.refs.append(fields[attribute])
        if tag == "img" and fields.get("srcset"):
            self.refs.extend(part.strip().split()[0] for part in fields["srcset"].split(","))


def fetch(url: str, method: str = "GET") -> bytes:
    safe = quote(url, safe=":/?=&%#@+;,")
    request = Request(safe, method=method, headers={"User-Agent": "ArinaPortfolio-DeploymentCheck/1.0"})
    with urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        if urlsplit(response.url).netloc != urlsplit(url).netloc:
            raise RuntimeError(f"Unexpected host redirect: {url}")
        return response.read() if method == "GET" else b""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    parts = urlsplit(base)
    if parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".github.io"):
        raise SystemExit("Expected an HTTPS GitHub Pages URL.")

    # Allow a short propagation delay after a successful Pages deployment.
    for attempt in range(12):
        try:
            home = fetch(base).decode("utf-8")
            if "Арина Самышева" not in home:
                raise RuntimeError("The requested portfolio is not visible yet.")
            break
        except (HTTPError, URLError, RuntimeError, TimeoutError) as error:
            if attempt == 11:
                raise SystemExit(str(error))
            time.sleep(10)

    projects = json.loads((ROOT / "source/projects.json").read_text(encoding="utf-8"))
    settings = json.loads((ROOT / "source/settings.json").read_text(encoding="utf-8"))
    pages = ["index.html", "works.html", "contact.html"]
    pages += [f"projects/{p['slug']}.html" for p in projects]
    assets: set[str] = set()
    page_errors: list[str] = []
    for path in pages:
        url = urljoin(base, path)
        try:
            content = fetch(url).decode("utf-8")
            parsed = Page()
            parsed.feed(content)
            if parsed.h1 != 1 or parsed.main != 1:
                raise RuntimeError("Expected exactly one h1 and main element.")
            for ref in parsed.refs:
                target = urljoin(url, ref).split("#", 1)[0]
                target_parts = urlsplit(target)
                if target_parts.netloc == parts.netloc and target_parts.path.startswith(parts.path):
                    assets.add(target)
        except (HTTPError, URLError, RuntimeError, TimeoutError, UnicodeError) as error:
            page_errors.append(f"{path}: {error}")
    if page_errors:
        raise SystemExit("\n".join(page_errors))

    js = fetch(urljoin(base, "assets/js/config.js")).decode("utf-8")
    if settings["email"] not in js or settings["formspreeId"] not in js:
        raise SystemExit("Published contact configuration does not match source settings.")
    css_url = urljoin(base, "assets/css/site.css")
    css = fetch(css_url).decode("utf-8")
    for match in re.finditer(r"url\(\s*['\"]?([^'\"\)]+)", css):
        target = urljoin(css_url, match.group(1).strip()).split("#", 1)[0]
        if urlsplit(target).netloc == parts.netloc:
            assets.add(target)
    assets.update([urljoin(base, "robots.txt"), urljoin(base, "sitemap.xml")])

    def check_asset(url: str) -> str | None:
        for attempt in range(2):
            try:
                fetch(url, "HEAD")
                return None
            except (HTTPError, URLError, RuntimeError, TimeoutError) as error:
                if attempt:
                    return f"{url}: {error}"
                time.sleep(2)
        return None

    errors = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for future in as_completed([pool.submit(check_asset, url) for url in sorted(assets)]):
            result = future.result()
            if result:
                errors.append(result)
    if errors:
        raise SystemExit("\n".join(errors))
    result = (f"Live check passed: {len(pages)} pages, {len(assets)} local URLs. "
              f"Site: {base}\nNo contact form submission was made. "
              "Mailbox delivery still needs one real end-to-end test.")
    print(result)
    import os
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write("## Public website check\n\n" + result + "\n")


if __name__ == "__main__":
    main()
