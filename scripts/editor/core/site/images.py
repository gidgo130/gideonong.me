"""Image import (plan Phase 5): web-size, metadata-free files for assets/images/.

process(data, preset) → (bytes, info)
  * JPEG or PNG in (anything else: "convert to JPG or PNG first"), 25 MB max;
  * the phone's orientation tag is applied, an embedded colour profile is
    converted to sRGB, then EVERY tag, comment, XMP block and profile is dropped
    (nothing is passed to save(), so nothing survives);
  * resized with Lanczos by preset, never upscaled:
      main      fit inside 1600 × 1600 (featured / main images, photos, band images)
      thumb     centre-crop 4:3 → 800 × 600 (index thumbnails)
      wide      centre-crop 16:9 → 1600 × 900
      portrait  fit inside 1250 × 1250 (hero tiles, headshot)
      asis      no resize (plots, screenshots); refused above 2400 px wide
  * JPEG out (quality 82, progressive) for photos, PNG stays PNG (RGBA / palette kept).
Existing files under assets/images/ are never re-encoded (image-manifest.md);
inspect() / scan() only read them for the Images panel.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional

MAX_INPUT = 25 * 1024 * 1024
JPEG_QUALITY = 82
PRESETS = {
    "main": {"label": "Main image / photo (fit 1600)", "fit": (1600, 1600)},
    "thumb": {"label": "Index thumbnail (4:3, 800 × 600)", "crop": (4, 3), "size": (800, 600)},
    "wide": {"label": "Wide (16:9, 1600 × 900)", "crop": (16, 9), "size": (1600, 900)},
    "portrait": {"label": "Portrait / hero tile (fit 1250)", "fit": (1250, 1250)},
    "asis": {"label": "As is — strip metadata only (plots, screenshots)", "asis": True, "max_width": 2400},
}
WARN_KB = 600
WARN_PX = 2000
_GPS_IFD = 0x8825
_EXIF_IFD = 0x8769


class ImageError(ValueError):
    pass


def slug_name(stem: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return s or "image"


def output_name(name: str, preset: str, fmt: str) -> str:
    base = slug_name(Path(name).stem)
    if preset == "thumb" and not base.endswith("-thumb"):
        base += "-thumb"
    return base + (".png" if fmt == "png" else ".jpg")


def _crop_fit(im, ratio: tuple[int, int], size: tuple[int, int]):
    """Centre-crop to `ratio`, then downscale to at most `size` (never upscale)."""
    w, h = im.size
    rw, rh = ratio
    if w * rh > h * rw:  # too wide → trim the sides
        cw = h * rw // rh
        box = ((w - cw) // 2, 0, (w - cw) // 2 + cw, h)
    else:  # too tall → trim top and bottom
        ch = w * rh // rw
        box = (0, (h - ch) // 2, w, (h - ch) // 2 + ch)
    out = im.crop(box)
    if out.size[0] > size[0] or out.size[1] > size[1]:
        from PIL import Image

        out.thumbnail(size, Image.Resampling.LANCZOS)
    return out


def process(data: bytes, preset: str) -> tuple[bytes, dict]:
    from PIL import Image, ImageOps

    if preset not in PRESETS:
        raise ImageError(f"unknown preset {preset!r}")
    if len(data) > MAX_INPUT:
        raise ImageError(f"the file is {len(data) // (1024 * 1024)} MB; the limit is 25 MB")
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as e:
        raise ImageError(f"not an image file ({e})") from e
    fmt = (im.format or "").upper()
    if fmt not in ("JPEG", "PNG"):
        raise ImageError(f"{fmt or 'unknown'} is not supported — convert to JPG or PNG first")
    exif = im.getexif()
    info = {
        "sourceWidth": im.size[0],
        "sourceHeight": im.size[1],
        "hadExif": len(exif) > 0,
        "hadGps": bool(exif.get_ifd(_GPS_IFD)) if len(exif) else False,
        "hadIcc": bool(im.info.get("icc_profile")),
        "transposed": False,
    }
    rotated = ImageOps.exif_transpose(im)
    if rotated is not None and rotated is not im:
        info["transposed"] = rotated.size != im.size
        im = rotated
    if info["hadIcc"] and im.mode in ("RGB", "RGBA"):
        try:
            from PIL import ImageCms

            src = ImageCms.ImageCmsProfile(io.BytesIO(im.info["icc_profile"]))
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode=im.mode)
        except Exception:
            pass  # keep the pixels as they are; the profile is dropped either way
    out_fmt = "png" if fmt == "PNG" else "jpg"
    p = PRESETS[preset]
    if p.get("asis"):
        if im.size[0] > p["max_width"]:
            raise ImageError(f"“as is” keeps the pixels, but this image is {im.size[0]} px wide (max {p['max_width']}) — pick a resize preset")
    elif "crop" in p:
        im = _crop_fit(im, p["crop"], p["size"])
    else:
        im.thumbnail(p["fit"], Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    if out_fmt == "jpg":
        if im.mode != "RGB":
            im = im.convert("RGB")
        clean = Image.new("RGB", im.size)  # a fresh image carries no info dict at all
        clean.paste(im)
        clean.save(buf, "JPEG", quality=JPEG_QUALITY, progressive=True, optimize=True)
    else:
        if im.mode not in ("RGB", "RGBA", "L", "LA", "P"):
            im = im.convert("RGBA")
        clean = im.copy()
        clean.info = {}
        clean.save(buf, "PNG", optimize=True)
    out = buf.getvalue()
    info.update({"width": im.size[0], "height": im.size[1], "kb": (len(out) + 1023) // 1024, "format": out_fmt, "preset": preset})
    return out, info


def inspect(path: Path) -> Optional[dict]:
    from PIL import Image

    p = Path(path)
    try:
        with Image.open(p) as im:
            exif = im.getexif()
            tags = sorted(_tag_name(k) for k in exif.keys())
            gps = bool(exif.get_ifd(_GPS_IFD)) if len(exif) else False
            return {
                "width": im.size[0],
                "height": im.size[1],
                "kb": (p.stat().st_size + 1023) // 1024,
                "format": (im.format or "").lower(),
                "exifTags": tags,
                "gps": gps,
                "icc": bool(im.info.get("icc_profile")),
            }
    except Exception:
        return None


def _tag_name(k: int) -> str:
    from PIL.ExifTags import TAGS

    return str(TAGS.get(k, k))


def check(info: Optional[dict]) -> list[str]:
    if not info:
        return ["not a readable image"]
    out = []
    if info["gps"]:
        out.append("has GPS location data")
    if info["exifTags"]:
        out.append("has EXIF metadata (" + ", ".join(info["exifTags"][:4]) + ("…" if len(info["exifTags"]) > 4 else "") + ")")
    if info["icc"]:
        out.append("has an embedded colour profile")
    if info["kb"] > WARN_KB:
        out.append(f"{info['kb']} KB — heavier than {WARN_KB} KB")
    if max(info["width"], info["height"]) > WARN_PX:
        out.append(f"{info['width']} × {info['height']} — larger than {WARN_PX} px")
    return out


IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}


def scan(repo_root: Path) -> list[dict]:
    root = Path(repo_root) / "assets" / "images"
    out = []
    if not root.is_dir():
        return out
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:
            continue
        info = inspect(p)
        out.append({"path": p.relative_to(repo_root).as_posix(), "info": info, "warnings": check(info)})
    return out
