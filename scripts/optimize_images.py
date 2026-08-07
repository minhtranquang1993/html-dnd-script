#!/usr/bin/env python3
"""
optimize_images.py -- Resize, convert, compress and tag images for DND articles.

Called by the dnd-html skill when the `images` parameter is a folder path
(see "Common Procedure -- Xu ly & toi uu anh folder" in SKILL.md).

Pipeline per image (source folder is never modified):
    1. resize to --width (aspect kept, never upscaled)
    2. convert to --format (default webp)
    3. compress via TinyPNG if an API key is available
    4. write metadata LAST -- TinyPNG strips it, so it must be re-applied after

Metadata written to every output image:
    EXIF Description  = image_description from the manifest
    XPKeywords (Tags) = image_description   (UTF-16, shows correctly on Windows)
    XPAuthor (Authors)= "Benh vien Mat Quoc te DND Sai Gon"

Output filenames come from `alt_text_slug` in the manifest. Always read
`final_filename` / `final_path` from the JSON output -- do not predict them,
collisions get a `-2`, `-3` suffix.

Usage:
    python3 optimize_images.py --folder /path/to/images --width 1200 \
        --manifest-file /tmp/dnd-optimize-manifest.json

Prints a single JSON object to stdout. On setup failure: {"ok": false, ...}.

Requires Pillow and piexif. If the interpreter used to launch the script lacks
them, it re-execs itself once with another interpreter that has them.
"""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

AUTHOR = "Bệnh viện Mắt Quốc tế DND Sài Gòn"
SOURCE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".heic", ".heif"}
TINY_ENDPOINT = "https://api.tinify.com/shrink"
_REEXEC_FLAG = "DND_OPTIMIZE_REEXEC"


# ---------------------------------------------------------------- bootstrap

def _ensure_deps():
    """Import Pillow/piexif, re-execing once into an interpreter that has them."""
    try:
        import PIL  # noqa: F401
        import piexif  # noqa: F401
        return
    except ImportError:
        pass

    if os.environ.get(_REEXEC_FLAG):
        _die(
            "Pillow and piexif are required but not installed for this interpreter.",
            hint=(
                "Install them for the Python you run this with, e.g. "
                "`python3 -m pip install --user Pillow piexif`, then retry."
            ),
        )

    probe = "import PIL, piexif"
    candidates = [
        "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
        shutil.which("python3.13"),
        shutil.which("python3.12"),
        shutil.which("python3.11"),
        shutil.which("python3"),
    ]
    current = os.path.realpath(sys.executable)
    for cand in candidates:
        if not cand or not os.path.exists(cand) or os.path.realpath(cand) == current:
            continue
        try:
            probed = subprocess.run(
                [cand, "-c", probe], capture_output=True, timeout=30
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if probed.returncode == 0:
            env = dict(os.environ, **{_REEXEC_FLAG: "1"})
            os.execve(cand, [cand, os.path.abspath(__file__)] + sys.argv[1:], env)

    _die(
        "Pillow and piexif are required but no available Python has them.",
        hint="Install with `python3 -m pip install --user Pillow piexif`, then retry.",
    )


def _die(error, hint=None):
    payload = {"ok": False, "error": error}
    if hint:
        payload["hint"] = hint
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(1)


# ---------------------------------------------------------------- helpers

def slugify(text):
    """Lowercase ASCII slug; strips Vietnamese diacritics."""
    text = text.replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def load_manifest(path):
    """Return {source_filename: {alt_text_slug, image_description}}."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        _die(f"Manifest not found: {path}")
    except (OSError, json.JSONDecodeError) as exc:
        _die(f"Cannot read manifest {path}: {exc}")

    if not isinstance(raw, list):
        _die("Manifest must be a JSON array of objects.")

    entries = {}
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            _die(f"Manifest item #{i + 1} is not an object.")
        name = item.get("source_filename")
        if not name:
            _die(f"Manifest item #{i + 1} is missing 'source_filename'.")
        entries[name] = {
            "alt_text_slug": (item.get("alt_text_slug") or "").strip(),
            "image_description": (item.get("image_description") or "").strip(),
        }
    return entries


def find_tinypng_key(folder):
    """Env var first, then a credentials file next to the skill."""
    key = (os.environ.get("TINYPNG_API_KEY") or os.environ.get("TINIFY_API_KEY") or "").strip()
    if key:
        return key
    skill_dir = Path(__file__).resolve().parent.parent
    for cand in (
        skill_dir / "credentials" / "tinypng_api_key.txt",
        Path(folder) / "tinypng_api_key.txt",
    ):
        try:
            found = cand.read_text(encoding="utf-8").strip()
            if found:
                return found
        except OSError:
            continue
    return ""


def unique_path(directory, stem, ext):
    """`stem.ext`, or `stem-2.ext`, `stem-3.ext`... if taken."""
    candidate = directory / f"{stem}{ext}"
    n = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{n}{ext}"
        n += 1
    return candidate


# ---------------------------------------------------------------- steps

def resize_convert(src, dest, width, fmt):
    """Resize (never upscale) and save as fmt. Returns (w, h)."""
    from PIL import Image, ImageOps

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # bake in camera rotation

        if fmt == "jpeg":
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                flat = Image.new("RGB", im.size, (255, 255, 255))
                flat.paste(im, mask=im.split()[-1])
                im = flat
            elif im.mode != "RGB":
                im = im.convert("RGB")
        elif im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")

        if im.width > width:
            height = max(1, round(im.height * width / im.width))
            im = im.resize((width, height), Image.LANCZOS)

        opts = {"quality": 82, "method": 6} if fmt == "webp" else {"quality": 82, "optimize": True}
        im.save(dest, format=fmt.upper(), **opts)
        return im.width, im.height


def tinify_file(path, key):
    """Compress in place via TinyPNG. Returns (ok, status)."""
    auth = base64.b64encode(f"api:{key}".encode()).decode()
    req = urllib.request.Request(
        TINY_ENDPOINT,
        data=path.read_bytes(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/octet-stream"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # 429 = monthly free quota exhausted -> stop trying for the rest of the run
        return False, "disabled_quota" if exc.code == 429 else "skipped_error"
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
        return False, "skipped_error"

    url = (body.get("output") or {}).get("url")
    if not url:
        return False, "skipped_error"
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError):
        return False, "skipped_error"
    if not data:
        return False, "skipped_error"

    path.write_bytes(data)
    return True, "applied"


def write_metadata(path, description, fmt):
    """Write EXIF Description + XPKeywords (Tags) + XPAuthor (Authors)."""
    import piexif
    from PIL import Image

    desc_utf16 = description.encode("utf-16-le") + b"\x00\x00"
    author_utf16 = AUTHOR.encode("utf-16-le") + b"\x00\x00"
    exif = {
        "0th": {
            piexif.ImageIFD.ImageDescription: description.encode("utf-8"),
            piexif.ImageIFD.XPKeywords: desc_utf16,
            piexif.ImageIFD.XPAuthor: author_utf16,
            piexif.ImageIFD.Artist: AUTHOR.encode("utf-8"),
        },
        "Exif": {},
        "GPS": {},
        "1st": {},
        "thumbnail": None,
    }
    exif_bytes = piexif.dump(exif)

    if fmt == "jpeg":
        piexif.insert(exif_bytes, str(path))
    else:
        # WebP/PNG: re-save carrying the EXIF chunk
        with Image.open(path) as im:
            im.load()
            im.save(path, format=fmt.upper(), exif=exif_bytes, quality=82, method=6)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Resize, convert, compress and tag images for DND articles."
    )
    ap.add_argument("--folder", required=True, help="folder holding the source images")
    ap.add_argument("--width", type=int, default=1200, help="target width in px (default 1200)")
    ap.add_argument("--manifest-file", required=True, help="JSON manifest path")
    ap.add_argument(
        "--format",
        default="webp",
        choices=["webp", "jpeg", "png"],
        help="output format (default webp)",
    )
    ap.add_argument("--output-dir", help="where to write results (default <folder>/optimized)")
    ap.add_argument("--no-tinypng", action="store_true", help="skip TinyPNG compression")
    args = ap.parse_args()

    folder = Path(args.folder).expanduser()
    if not folder.is_dir():
        _die(f"Folder not found: {folder}")
    if args.width < 1:
        _die(f"--width must be a positive integer, got {args.width}")

    manifest = load_manifest(args.manifest_file)

    sources = sorted(
        (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SOURCE_EXTS),
        key=lambda p: p.name,
    )
    if not sources:
        _die(f"No images found in {folder}")

    out_dir = Path(args.output_dir).expanduser() if args.output_dir else folder / "optimized"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _die(f"Cannot create output dir {out_dir}: {exc}")

    fmt = args.format
    ext = ".jpg" if fmt == "jpeg" else f".{fmt}"

    tiny_key = "" if args.no_tinypng else find_tinypng_key(folder)
    tiny_enabled = bool(tiny_key)
    tiny_default = "disabled" if args.no_tinypng else ("" if tiny_key else "skipped_no_key")

    results = []
    for i, src in enumerate(sources, start=1):
        entry = manifest.get(src.name, {})
        notes = []
        if src.name not in manifest:
            notes.append("no manifest entry; named from source filename, no description written")

        stem = entry.get("alt_text_slug") or slugify(src.stem) or f"image-{i}"
        if entry.get("alt_text_slug") and slugify(stem) != stem:
            stem = slugify(stem)
            notes.append("alt_text_slug was not a clean slug; normalised")

        description = entry.get("image_description", "")
        record = {
            "index": i,
            "source_filename": src.name,
            "source_path": str(src),
            "alt_text_slug": stem,
            "image_description": description,
            "bytes_in": src.stat().st_size,
            "tinypng": tiny_default or "skipped_no_key",
        }

        dest = unique_path(out_dir, stem, ext)
        try:
            w, h = resize_convert(src, dest, args.width, fmt)
        except Exception as exc:  # unreadable/corrupt source, unsupported codec
            record.update(
                status="failed",
                final_filename=None,
                final_path=None,
                bytes_out=0,
                tinypng="not_reached",
                notes=notes + [f"resize/convert failed: {type(exc).__name__}: {exc}"],
            )
            results.append(record)
            continue

        record.update(final_filename=dest.name, final_path=str(dest), width=w, height=h)
        degraded = False

        if tiny_enabled:
            ok, tiny_status = tinify_file(dest, tiny_key)
            record["tinypng"] = tiny_status
            if not ok:
                degraded = True
                if tiny_status == "disabled_quota":
                    tiny_enabled = False
                    tiny_default = "disabled_quota"
                    notes.append("TinyPNG monthly quota reached; disabled for remaining images")
                else:
                    notes.append("TinyPNG compression failed; local optimisation kept")
        elif tiny_default:
            record["tinypng"] = tiny_default

        if description:
            try:
                write_metadata(dest, description, fmt)
            except Exception as exc:
                degraded = True
                notes.append(f"metadata write failed: {type(exc).__name__}: {exc}")

        record["bytes_out"] = dest.stat().st_size
        record["status"] = "fallback" if degraded else "success"
        record["notes"] = notes
        results.append(record)

    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r["status"] == "success"),
        "fallback": sum(1 for r in results if r["status"] == "fallback"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
    }
    unmatched = [name for name in manifest if name not in {r["source_filename"] for r in results}]

    print(json.dumps(
        {
            "ok": True,
            "folder": str(folder),
            "output_dir": str(out_dir),
            "width": args.width,
            "format": fmt,
            "summary": summary,
            "manifest_entries_unmatched": unmatched,
            "images": results,
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    _ensure_deps()
    main()
