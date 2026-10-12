#!/usr/bin/env python3
"""Import the approved site from five checksum-verified upload archives.

No network calls. Only site/ and source/ are extracted; workflow files are
never accepted from an archive. Original image bytes are preserved.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools/package-manifest.json"


def record(ready: bool, imported: bool, message: str) -> None:
    print(message)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"ready={str(ready).lower()}\n")
            stream.write(f"imported={str(imported).lower()}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("## Site files\n\n" + message + "\n\n")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    required = ["site/index.html", "source/build.py", "source/check_files.py",
                "source/projects.json", "source/settings.json"]
    if all((ROOT / name).is_file() for name in required):
        record(True, False, "Site source already imported. Building from the repository.")
        return
    if any((ROOT / name).exists() for name in required):
        raise SystemExit("Partial site source detected; refusing to overwrite existing files.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = [part["name"] for part in manifest["parts"]
               if not (ROOT / part["name"]).is_file()]
    if missing:
        record(False, False,
               "**NOT PUBLISHED:** waiting for the approved upload archives. "
               "Upload all five ZIP files to the repository root. Missing: "
               + ", ".join(f"`{name}`" for name in missing))
        return

    for part in manifest["parts"]:
        archive = ROOT / part["name"]
        if archive.stat().st_size != part["archive_bytes"] or digest(archive) != part["sha256"]:
            raise SystemExit(f"Checksum mismatch: {part['name']}. Upload the original supplied ZIP.")

    seen: set[str] = set()
    total_size = 0
    with tempfile.TemporaryDirectory(prefix="portfolio-import-") as temp:
        stage = Path(temp)
        for part in manifest["parts"]:
            count = 0
            raw_size = 0
            with ZipFile(ROOT / part["name"]) as archive:
                for item in archive.infolist():
                    path = PurePosixPath(item.filename)
                    if (item.is_dir() or "\\" in item.filename or path.is_absolute()
                            or ".." in path.parts or not path.parts
                            or path.parts[0] not in {"site", "source"}
                            or stat.S_ISLNK(item.external_attr >> 16)
                            or item.filename in seen):
                        raise SystemExit(f"Unsafe or duplicate archive entry: {item.filename}")
                    count += 1
                    raw_size += item.file_size
                    total_size += item.file_size
                    if total_size > manifest["total_uncompressed_bytes"]:
                        raise SystemExit("Unexpected uncompressed size.")
                    seen.add(item.filename)
                    dest = stage.joinpath(*path.parts)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source, dest.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    if dest.stat().st_size != item.file_size:
                        raise SystemExit(f"Incomplete extraction: {item.filename}")
            if count != part["file_count"] or raw_size != part["uncompressed_bytes"]:
                raise SystemExit(f"Unexpected archive contents: {part['name']}")
        if len(seen) != manifest["total_files"] or total_size != manifest["total_uncompressed_bytes"]:
            raise SystemExit("The combined package is incomplete.")
        if not all((stage / name).is_file() for name in required):
            raise SystemExit("Required site files are missing from the package.")
        for directory in ("site", "source"):
            if (ROOT / directory).exists():
                raise SystemExit(f"Refusing to overwrite existing directory: {directory}")
        for directory in ("site", "source"):
            shutil.copytree(stage / directory, ROOT / directory)
    record(True, True,
           f"Imported {len(seen)} approved files; archive checksums verified. "
           "The deployment job must finish before the site is live.")


if __name__ == "__main__":
    main()
