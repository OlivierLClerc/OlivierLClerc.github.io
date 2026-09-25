"""Remove the white export frame from photos/Selection for the future gallery set."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "photos" / "Selection"
OUTPUT_DIR = ROOT / "photos" / "Selection_processed"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def first_nonwhite_line(profile: np.ndarray) -> int | None:
    indices = np.flatnonzero(profile < 0.90)
    return int(indices[0]) if indices.size else None


def measure_frame(path: Path) -> tuple[int | None, int | None, int | None, int | None]:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        width, height = image.size
        if width != height:
            raise ValueError(f"Expected a square image: {path.name} ({width}x{height})")

        pixels = np.asarray(image)
    return measure_frame_pixels(pixels)


def measure_frame_pixels(pixels: np.ndarray) -> tuple[int | None, int | None, int | None, int | None]:
    width = pixels.shape[1]
    scan_depth = max(2, round(width * 0.12))
    middle = slice(round(width * 0.2), round(width * 0.8))
    white = np.min(pixels, axis=2) >= 245
    profiles = (
        white[:scan_depth, middle].mean(axis=1),
        white[-scan_depth:, middle].mean(axis=1)[::-1],
        white[middle, :scan_depth].mean(axis=0),
        white[middle, -scan_depth:].mean(axis=0)[::-1],
    )

    depths: list[int | None] = []
    for profile in profiles:
        if float(profile[0]) < 0.98:
            depths.append(None)
            continue
        depth = first_nonwhite_line(profile)
        depths.append(depth if depth is not None and 2 <= depth < scan_depth else None)
    return tuple(depths)


def detect_shared_frame(paths: list[Path]) -> int:
    sample_count = min(32, len(paths))
    sample_indices = np.linspace(0, len(paths) - 1, sample_count, dtype=int)
    measurements = [depth for index in sample_indices for depth in measure_frame(paths[index]) if depth is not None]
    if len(measurements) < sample_count * 2:
        raise ValueError("Could not reliably detect the white frame. Try --border PIXELS.")

    middle = float(np.median(measurements))
    consistent = [depth for depth in measurements if abs(depth - middle) <= 3]
    if len(consistent) < sample_count * 2:
        raise ValueError("Frame widths vary too much to use one crop. Try --border PIXELS.")

    # Crop through the last nearly-white edge pixel so no one-pixel line remains.
    return int(np.ceil(np.percentile(consistent, 90)))


def detect_photo_frame(path: Path, shared_border: int) -> int:
    return detect_photo_frame_depths(measure_frame(path), shared_border)


def detect_photo_frame_depths(
    depths: tuple[int | None, int | None, int | None, int | None], shared_border: int
) -> int:
    top, bottom, left, right = depths
    border = shared_border
    for first, second in ((top, bottom), (left, right)):
        if first is None or second is None or abs(first - second) > 3:
            continue
        candidate = max(first, second)
        if shared_border + 3 < candidate <= shared_border * 2:
            border = max(border, candidate)
    return border


def prepare_photo(source_path: Path, output_path: Path, border: int) -> None:
    with Image.open(source_path) as source:
        icc_profile = source.info.get("icc_profile")
        image = ImageOps.exif_transpose(source)
        width, height = image.size
        if width != height or border <= 0 or border * 2 >= width:
            raise ValueError(f"Invalid square crop for {source_path.name}: {width}x{height}, border {border}")

        cropped = image.crop((border, border, width - border, height - border))
        resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
        save_options: dict[str, object] = {}
        if icc_profile:
            save_options["icc_profile"] = icc_profile

        suffix = source_path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            resized = resized.convert("RGB")
            save_options.update(quality=92, optimize=True, subsampling=0)
        elif suffix == ".png":
            save_options["optimize"] = True
        elif suffix == ".webp":
            save_options["quality"] = 92

        resized.save(output_path, **save_options)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--border", type=int, help="Crop this many pixels on each side instead of detecting the frame")
    parser.add_argument("--limit", type=int, help="Process only the first N photos for inspection")
    parser.add_argument("--only", action="append", metavar="NAME", help="Process only this filename (repeatable)")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing processed copies")
    args = parser.parse_args()

    if not SOURCE_DIR.is_dir():
        parser.error(f"Missing source folder: {SOURCE_DIR}")
    paths = sorted(path for path in SOURCE_DIR.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)
    if not paths:
        parser.error(f"No supported photos found in {SOURCE_DIR}")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")

    border = args.border if args.border is not None else detect_shared_frame(paths)
    if border <= 0:
        parser.error("--border must be positive")
    print(f"Crop width: {border}px per side (source: {SOURCE_DIR.relative_to(ROOT)})")

    if args.only:
        names = set(args.only)
        missing = names - {path.name for path in paths}
        if missing:
            parser.error(f"Unknown source photo(s): {', '.join(sorted(missing))}")
        selected = [path for path in paths if path.name in names]
    else:
        selected = paths[: args.limit] if args.limit else paths
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    for source_path in selected:
        output_path = OUTPUT_DIR / source_path.name
        if (ARCHIVE_DIR / source_path.name).exists():
            skipped += 1
            continue
        if output_path.exists() and not args.overwrite:
            skipped += 1
            continue
        photo_border = border if args.border is not None else detect_photo_frame(source_path, border)
        if photo_border != border:
            print(f"Wider frame: {source_path.name}: {photo_border}px per side")
        prepare_photo(source_path, output_path, photo_border)
        written += 1
        if written % 25 == 0:
            print(f"Processed {written}/{len(selected)} photos")

    print(f"Wrote {written} photos to {OUTPUT_DIR.relative_to(ROOT)}; skipped {skipped} existing files.")


if __name__ == "__main__":
    main()
