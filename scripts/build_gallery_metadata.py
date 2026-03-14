from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageOps
from scipy.fft import dctn
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
PHOTOS_DIR = ROOT / "photos"
OUTPUT_PATH = ROOT / "_data" / "gallery_metadata.json"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SEED = 42
DEFAULT_COUNT = 9
ANALYSIS_SIZE = 128
MODE_ORDER = ("color", "bw")
DEFAULT_COLOR_PROXIMITY = 70
DEFAULT_GEOMETRY_PROXIMITY = 70
DEFAULT_COLOR_ENABLED = True
DEFAULT_GEOMETRY_ENABLED = True
AXIS_HALF_SPAN = 4.0


@dataclass
class PhotoMetadata:
    identifier: str
    src: str
    photo_mode: str
    summary: dict[str, float]
    color_tone_vector: np.ndarray
    geometry_vector: np.ndarray


def open_rgb_array(path: Path, size: int = ANALYSIS_SIZE) -> np.ndarray:
    with Image.open(path) as image:
        rgb = ImageOps.exif_transpose(image).convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
        return np.asarray(rgb, dtype=np.float32) / 255.0


def dct_signature(values: np.ndarray, *, size: int = 32, low_frequency: int = 8) -> np.ndarray:
    if values.ndim != 2:
        raise ValueError("dct_signature expects a 2D array")

    image = Image.fromarray(np.clip(values * 255.0, 0.0, 255.0).astype(np.uint8), mode="L")
    resized = image.resize((size, size), Image.Resampling.LANCZOS)
    normalized = np.asarray(resized, dtype=np.float32) / 255.0
    coefficients = dctn(normalized, type=2, norm="ortho")[:low_frequency, :low_frequency].reshape(-1)

    coefficients = coefficients[1:]
    norm = float(np.linalg.norm(coefficients))
    if norm > 0:
        coefficients = coefficients / norm

    return coefficients.astype(np.float32)


def grid_means(values: np.ndarray, rows: int = 3, cols: int = 3) -> np.ndarray:
    height, width = values.shape[:2]
    row_edges = np.linspace(0, height, rows + 1, dtype=int)
    col_edges = np.linspace(0, width, cols + 1, dtype=int)
    cells: list[float] = []

    for row_index in range(rows):
        for col_index in range(cols):
            cell = values[row_edges[row_index] : row_edges[row_index + 1], col_edges[col_index] : col_edges[col_index + 1]]
            cells.append(float(cell.mean()))

    return np.asarray(cells, dtype=np.float32)


def hue_channel(rgb: np.ndarray) -> np.ndarray:
    red = rgb[:, :, 0]
    green = rgb[:, :, 1]
    blue = rgb[:, :, 2]

    maximum = np.max(rgb, axis=2)
    minimum = np.min(rgb, axis=2)
    delta = maximum - minimum

    hue = np.zeros_like(maximum, dtype=np.float32)
    non_zero = delta > 1e-6

    red_mask = non_zero & (maximum == red)
    green_mask = non_zero & (maximum == green)
    blue_mask = non_zero & (maximum == blue)

    hue[red_mask] = ((green[red_mask] - blue[red_mask]) / delta[red_mask]) % 6.0
    hue[green_mask] = ((blue[green_mask] - red[green_mask]) / delta[green_mask]) + 2.0
    hue[blue_mask] = ((red[blue_mask] - green[blue_mask]) / delta[blue_mask]) + 4.0

    return ((hue / 6.0) % 1.0).astype(np.float32)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    linear = np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4,
    )

    transform = np.asarray(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float32,
    )
    xyz = np.tensordot(linear, transform.T, axes=1)
    xyz /= np.asarray([0.95047, 1.0, 1.08883], dtype=np.float32)

    epsilon = 216 / 24389
    kappa = 24389 / 27
    f_xyz = np.where(
        xyz > epsilon,
        np.cbrt(xyz),
        ((kappa * xyz) + 16.0) / 116.0,
    )

    lab = np.empty_like(xyz, dtype=np.float32)
    lab[:, :, 0] = (116.0 * f_xyz[:, :, 1]) - 16.0
    lab[:, :, 1] = 500.0 * (f_xyz[:, :, 0] - f_xyz[:, :, 1])
    lab[:, :, 2] = 200.0 * (f_xyz[:, :, 1] - f_xyz[:, :, 2])
    return lab


def determine_photo_mode(saturation: np.ndarray, channel_spread: np.ndarray) -> str:
    mean_saturation = float(saturation.mean())
    channel_spread_p95 = float(np.quantile(channel_spread, 0.95))
    return "bw" if mean_saturation <= 0.05 and channel_spread_p95 <= 0.08 else "color"


def extract_features(path: Path) -> PhotoMetadata:
    rgb = open_rgb_array(path)
    flat_rgb = rgb.reshape(-1, 3)
    grayscale = (0.299 * rgb[:, :, 0]) + (0.587 * rgb[:, :, 1]) + (0.114 * rgb[:, :, 2])

    value = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    channel_spread = value - minimum
    saturation = np.divide(channel_spread, value + 1e-6)
    hue = hue_channel(rgb)

    gradient_x = np.zeros_like(grayscale)
    gradient_y = np.zeros_like(grayscale)
    gradient_x[:, 1:-1] = (grayscale[:, 2:] - grayscale[:, :-2]) * 0.5
    gradient_y[1:-1, :] = (grayscale[2:, :] - grayscale[:-2, :]) * 0.5
    gradient_magnitude = np.hypot(gradient_x, gradient_y)
    gradient_orientation = (np.arctan2(gradient_y, gradient_x) + np.pi) / (2 * np.pi)

    orientation_histogram, _ = np.histogram(
        gradient_orientation,
        bins=8,
        range=(0.0, 1.0),
        weights=gradient_magnitude,
        density=True,
    )
    orientation_histogram = np.nan_to_num(orientation_histogram, nan=0.0)

    edge_threshold = float(np.quantile(gradient_magnitude, 0.75))
    edge_density = float((gradient_magnitude >= edge_threshold).mean())

    vertical_symmetry = float(np.mean(np.abs(grayscale - grayscale[:, ::-1])))
    horizontal_symmetry = float(np.mean(np.abs(grayscale - grayscale[::-1, :])))

    energy = gradient_magnitude + 1e-8
    y_coords, x_coords = np.indices(grayscale.shape, dtype=np.float32)
    x_center = float((energy * x_coords).sum() / energy.sum() / max(grayscale.shape[1] - 1, 1))
    y_center = float((energy * y_coords).sum() / energy.sum() / max(grayscale.shape[0] - 1, 1))

    lab = rgb_to_lab(rgb)
    lab_l = lab[:, :, 0] / 100.0
    lab_a = lab[:, :, 1] / 128.0
    lab_b = lab[:, :, 2] / 128.0
    flat_lab = np.stack([lab_l, lab_a, lab_b], axis=2).reshape(-1, 3)
    lab_mean = flat_lab.mean(axis=0)
    lab_std = flat_lab.std(axis=0)
    chroma = np.hypot(lab_a, lab_b)
    chroma_flat = chroma.reshape(-1)

    hue_histogram, _ = np.histogram(
        hue,
        bins=12,
        range=(0.0, 1.0),
        weights=(saturation * value) + 1e-6,
        density=True,
    )
    hue_histogram = np.nan_to_num(hue_histogram, nan=0.0)

    tone_histogram, _ = np.histogram(
        grayscale,
        bins=16,
        range=(0.0, 1.0),
        density=True,
    )
    tone_histogram = np.nan_to_num(tone_histogram, nan=0.0)

    edge_reference = gradient_magnitude / max(float(np.quantile(gradient_magnitude, 0.98)), 1e-6)
    perceptual_vector = dct_signature(grayscale)
    edge_vector = dct_signature(np.clip(edge_reference, 0.0, 1.0))

    photo_mode = determine_photo_mode(saturation, channel_spread)

    color_vector = np.concatenate(
        [
            lab_mean.astype(np.float32),
            lab_std.astype(np.float32),
            np.quantile(flat_lab, [0.1, 0.5, 0.9], axis=0).reshape(-1).astype(np.float32),
            np.asarray(
                [
                    float(chroma_flat.mean()),
                    float(chroma_flat.std()),
                    float(np.quantile(chroma_flat, 0.9)),
                    float(lab_mean[2]),
                ],
                dtype=np.float32,
            ),
            hue_histogram.astype(np.float32),
            grid_means(lab_a),
            grid_means(lab_b),
            grid_means(chroma),
        ]
    ).astype(np.float32)

    tone_vector = np.concatenate(
        [
            tone_histogram.astype(np.float32),
            np.quantile(grayscale, [0.1, 0.5, 0.9]).astype(np.float32),
            np.asarray(
                [
                    float(grayscale.mean()),
                    float(grayscale.std()),
                ],
                dtype=np.float32,
            ),
            grid_means(grayscale),
        ]
    ).astype(np.float32)

    geometry_vector = np.concatenate(
        [
            np.asarray(
                [
                    float(gradient_magnitude.mean()),
                    float(gradient_magnitude.std()),
                    float(np.quantile(gradient_magnitude, 0.9)),
                    edge_density,
                    vertical_symmetry,
                    horizontal_symmetry,
                    x_center,
                    y_center,
                ],
                dtype=np.float32,
            ),
            orientation_histogram.astype(np.float32),
            grid_means(grayscale),
            grid_means(gradient_magnitude),
            perceptual_vector,
            edge_vector,
        ]
    ).astype(np.float32)

    dominant_hue_index = int(np.argmax(hue_histogram))
    dominant_hue_deg = ((dominant_hue_index + 0.5) / len(hue_histogram)) * 360.0

    rgb_mean = flat_rgb.mean(axis=0)
    summary = {
        "brightness": round(float(grayscale.mean()), 6),
        "contrast": round(float(grayscale.std()), 6),
        "saturation": round(float(saturation.mean()), 6),
        "red": round(float(rgb_mean[0]), 6),
        "green": round(float(rgb_mean[1]), 6),
        "blue": round(float(rgb_mean[2]), 6),
        "warmth": round(float(lab_mean[2]), 6),
        "hue_peak_deg": round(float(dominant_hue_deg), 3),
        "edge_density": round(edge_density, 6),
        "vertical_symmetry": round(vertical_symmetry, 6),
        "horizontal_symmetry": round(horizontal_symmetry, 6),
    }

    return PhotoMetadata(
        identifier=path.name,
        src=f"/photos/{path.name}",
        photo_mode=photo_mode,
        summary=summary,
        color_tone_vector=color_vector if photo_mode == "color" else tone_vector,
        geometry_vector=geometry_vector,
    )


def load_photo_paths() -> list[Path]:
    if not PHOTOS_DIR.exists():
        raise FileNotFoundError(f"Missing photos directory: {PHOTOS_DIR}")

    photo_paths = sorted(
        [
            path
            for path in PHOTOS_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    )

    if not photo_paths:
        raise FileNotFoundError(f"No supported image files found in {PHOTOS_DIR}")

    return photo_paths


def standardize_feature_matrix(feature_matrix: np.ndarray) -> np.ndarray:
    if feature_matrix.shape[0] <= 1:
        return np.zeros_like(feature_matrix, dtype=np.float32)
    return StandardScaler().fit_transform(feature_matrix).astype(np.float32)


def project_semantic_axis(feature_matrix: np.ndarray) -> np.ndarray:
    if feature_matrix.shape[0] <= 1:
        return np.zeros(feature_matrix.shape[0], dtype=np.float32)

    projection = PCA(n_components=1).fit_transform(feature_matrix).reshape(-1)
    projection = projection - projection.mean()
    max_abs = float(np.max(np.abs(projection)))
    if max_abs <= 1e-6:
        return np.zeros_like(projection, dtype=np.float32)
    return (projection / max_abs * AXIS_HALF_SPAN).astype(np.float32)


def euclidean_distances(points: np.ndarray) -> np.ndarray:
    deltas = points[:, None, :] - points[None, :, :]
    return np.sqrt(np.sum(deltas * deltas, axis=2))


def nearest_neighbor_ids(identifiers: list[str], points: np.ndarray) -> dict[str, list[str]]:
    if not identifiers:
        return {}

    distances = euclidean_distances(points)
    neighbor_map: dict[str, list[str]] = {}

    for index, identifier in enumerate(identifiers):
        ordered_indices = np.argsort(distances[index]).tolist()
        neighbor_map[identifier] = [
            identifiers[neighbor_index]
            for neighbor_index in ordered_indices
            if neighbor_index != index
        ]

    return neighbor_map


def choose_default_anchor(identifiers: list[str], points: np.ndarray) -> str:
    if not identifiers:
        return ""
    if len(identifiers) == 1:
        return identifiers[0]

    centroid = points.mean(axis=0)
    centroid_distances = np.linalg.norm(points - centroid, axis=1)
    return identifiers[int(np.argmin(centroid_distances))]


def clamp_proximity(value: int | float) -> int:
    return int(max(0, min(100, round(float(value)))))


def strictness_window_size(mode_count: int, count: int, proximity: int | float) -> int:
    total_neighbors = max(0, mode_count - 1)
    neighbor_count = max(0, count - 1)
    if total_neighbors == 0 or neighbor_count == 0:
        return 0

    strictness = clamp_proximity(proximity) / 100.0
    window_fraction = 0.06 + ((1.0 - strictness) ** 2) * 0.44
    window_size = int(round(window_fraction * total_neighbors))
    return max(neighbor_count, min(total_neighbors, window_size))


def sort_candidates(
    candidate_ids: Iterable[str],
    color_rank: dict[str, int],
    geometry_rank: dict[str, int],
    color_norm: int,
    geometry_norm: int,
) -> list[str]:
    max_color_norm = max(color_norm, 1)
    max_geometry_norm = max(geometry_norm, 1)

    def score(identifier: str) -> tuple[int, float, int, str]:
        has_color = identifier in color_rank
        has_geometry = identifier in geometry_rank
        hit_count = int(has_color) + int(has_geometry)
        total = 0.0
        best_rank = 10**9

        if has_color:
            total += color_rank[identifier] / max_color_norm
            best_rank = min(best_rank, color_rank[identifier])
        else:
            total += 1.35

        if has_geometry:
            total += geometry_rank[identifier] / max_geometry_norm
            best_rank = min(best_rank, geometry_rank[identifier])
        else:
            total += 1.35

        return (-hit_count, total, best_rank, identifier)

    return sorted(dict.fromkeys(candidate_ids), key=score)


def stable_shuffle_ids(identifiers: list[str], seed_text: str) -> list[str]:
    def score(identifier: str) -> str:
        digest = hashlib.blake2b(f"{seed_text}:{identifier}".encode("utf-8"), digest_size=8).hexdigest()
        return digest

    return sorted(identifiers, key=score)


def evenly_spaced_selection(ordered_ids: list[str], count: int) -> list[str]:
    if count <= 0 or not ordered_ids:
        return []
    if len(ordered_ids) <= count:
        return ordered_ids[:count]
    if count == 1:
        return [ordered_ids[0]]

    chosen: list[tuple[int, str]] = []
    used_ids: set[str] = set()

    for slot in range(count):
        raw_index = int(round((slot * (len(ordered_ids) - 1)) / (count - 1)))
        candidate_index = raw_index

        while candidate_index < len(ordered_ids) and ordered_ids[candidate_index] in used_ids:
            candidate_index += 1

        if candidate_index >= len(ordered_ids):
            candidate_index = raw_index - 1
            while candidate_index >= 0 and ordered_ids[candidate_index] in used_ids:
                candidate_index -= 1

        if candidate_index < 0:
            continue

        identifier = ordered_ids[candidate_index]
        chosen.append((candidate_index, identifier))
        used_ids.add(identifier)

    return [identifier for _, identifier in sorted(chosen, key=lambda item: item[0])]


def build_selection(
    anchor_id: str,
    mode_identifiers: list[str],
    color_neighbors: dict[str, list[str]],
    geometry_neighbors: dict[str, list[str]],
    count: int,
    color_proximity: int | float,
    geometry_proximity: int | float,
    *,
    color_enabled: bool = True,
    geometry_enabled: bool = True,
    shuffle_seed: str = "",
) -> list[str]:
    if not anchor_id or anchor_id not in mode_identifiers:
        return []

    bounded_count = max(1, min(count, len(mode_identifiers)))
    if bounded_count == 1:
        return [anchor_id]

    neighbor_count = bounded_count - 1
    mode_set = set(mode_identifiers)
    ordered_color = [identifier for identifier in color_neighbors.get(anchor_id, []) if identifier in mode_set and identifier != anchor_id]
    ordered_geometry = [identifier for identifier in geometry_neighbors.get(anchor_id, []) if identifier in mode_set and identifier != anchor_id]

    if not color_enabled and not geometry_enabled:
        random_candidates = stable_shuffle_ids(
            [identifier for identifier in mode_identifiers if identifier != anchor_id],
            f"{anchor_id}|{shuffle_seed or 'default'}",
        )
        return [anchor_id, *evenly_spaced_selection(random_candidates, neighbor_count)]

    if color_enabled and not geometry_enabled:
        color_window_size = strictness_window_size(len(mode_identifiers), bounded_count, color_proximity)
        return [anchor_id, *evenly_spaced_selection(ordered_color[:color_window_size], neighbor_count)]

    if geometry_enabled and not color_enabled:
        geometry_window_size = strictness_window_size(len(mode_identifiers), bounded_count, geometry_proximity)
        return [anchor_id, *evenly_spaced_selection(ordered_geometry[:geometry_window_size], neighbor_count)]

    color_window_size = strictness_window_size(len(mode_identifiers), bounded_count, color_proximity)
    geometry_window_size = strictness_window_size(len(mode_identifiers), bounded_count, geometry_proximity)
    color_window = ordered_color[:color_window_size]
    geometry_window = ordered_geometry[:geometry_window_size]

    color_window_rank = {identifier: index for index, identifier in enumerate(color_window)}
    geometry_window_rank = {identifier: index for index, identifier in enumerate(geometry_window)}
    color_full_rank = {identifier: index for index, identifier in enumerate(ordered_color)}
    geometry_full_rank = {identifier: index for index, identifier in enumerate(ordered_geometry)}

    core_candidates = [identifier for identifier in color_window if identifier in geometry_window_rank]
    ordered_candidates = sort_candidates(core_candidates, color_full_rank, geometry_full_rank, len(ordered_color), len(ordered_geometry))

    if len(ordered_candidates) < neighbor_count:
        union_candidates = color_window + geometry_window
        ordered_candidates = sort_candidates(union_candidates, color_full_rank, geometry_full_rank, len(ordered_color), len(ordered_geometry))

    if len(ordered_candidates) < neighbor_count:
        full_candidates = [identifier for identifier in ordered_color + ordered_geometry + mode_identifiers if identifier != anchor_id]
        ordered_candidates = sort_candidates(full_candidates, color_full_rank, geometry_full_rank, len(ordered_color), len(ordered_geometry))

    return [anchor_id, *evenly_spaced_selection(ordered_candidates, neighbor_count)]


def serialize_manifest(photos: Iterable[dict[str, object]], default_mode: str, modes_payload: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        "version": 4,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "default_mode": default_mode,
        "feature_spec": {
            "resize": ANALYSIS_SIZE,
            "viewer_axes": {
                "x": "1D PCA projection of the color space for color photos, or the tone space for B&W photos",
                "y": "1D PCA projection of the geometry/composition space",
            },
            "selection_model": "Same-mode selectable color-or-tone and geometry gates produce ordered distance ladders with anchor-first output",
            "descriptive_only": ["brightness", "contrast", "saturation"],
            "photo_modes": {
                "color": "Default color photographs and muted-but-not-grayscale images",
                "bw": "Strict grayscale/near-grayscale photographs tagged from saturation and channel-spread thresholds",
            },
            "components": {
                "color": [
                    "Lab-like channel statistics",
                    "hue histogram weighted by chroma",
                    "chroma and warmth summaries",
                    "3x3 chroma and Lab color layout",
                ],
                "tone": [
                    "luminance histogram",
                    "luminance quantiles",
                    "3x3 tone layout",
                ],
                "geometry": [
                    "edge orientation histogram",
                    "symmetry and composition metrics",
                    "3x3 luminance and edge-energy grids",
                    "grayscale perceptual DCT signature",
                    "edge DCT signature",
                ],
            },
        },
        "modes": modes_payload,
        "photos": list(photos),
    }


def main() -> None:
    photo_paths = load_photo_paths()
    photo_metadata = [extract_features(path) for path in photo_paths]

    photos_by_mode: dict[str, list[PhotoMetadata]] = {mode: [] for mode in MODE_ORDER}
    for photo in photo_metadata:
        photos_by_mode.setdefault(photo.photo_mode, []).append(photo)

    color_neighbor_map: dict[str, list[str]] = {}
    geometry_neighbor_map: dict[str, list[str]] = {}
    semantic_points_by_id: dict[str, np.ndarray] = {}
    modes_payload: dict[str, dict[str, object]] = {}

    for mode in MODE_ORDER:
        mode_photos = photos_by_mode.get(mode, [])
        identifiers = [photo.identifier for photo in mode_photos]

        if not mode_photos:
            modes_payload[mode] = {
                "count": 0,
                "default_anchor": "",
                "default_selection": [],
                "default_color_proximity": DEFAULT_COLOR_PROXIMITY,
                "default_geometry_proximity": DEFAULT_GEOMETRY_PROXIMITY,
                "default_color_enabled": DEFAULT_COLOR_ENABLED,
                "default_geometry_enabled": DEFAULT_GEOMETRY_ENABLED,
            }
            continue

        color_tone_matrix = standardize_feature_matrix(np.vstack([photo.color_tone_vector for photo in mode_photos]))
        geometry_matrix = standardize_feature_matrix(np.vstack([photo.geometry_vector for photo in mode_photos]))

        x_axis = project_semantic_axis(color_tone_matrix)
        y_axis = project_semantic_axis(geometry_matrix)
        semantic_points = np.column_stack([x_axis, y_axis]).astype(np.float32)

        color_neighbor_map.update(nearest_neighbor_ids(identifiers, color_tone_matrix))
        geometry_neighbor_map.update(nearest_neighbor_ids(identifiers, geometry_matrix))

        default_anchor = choose_default_anchor(identifiers, semantic_points)
        default_selection = build_selection(
            default_anchor,
            identifiers,
            color_neighbor_map,
            geometry_neighbor_map,
            min(DEFAULT_COUNT, len(mode_photos)),
            DEFAULT_COLOR_PROXIMITY,
            DEFAULT_GEOMETRY_PROXIMITY,
            color_enabled=DEFAULT_COLOR_ENABLED,
            geometry_enabled=DEFAULT_GEOMETRY_ENABLED,
        )

        modes_payload[mode] = {
            "count": len(mode_photos),
            "default_anchor": default_anchor,
            "default_selection": default_selection,
            "default_color_proximity": DEFAULT_COLOR_PROXIMITY,
            "default_geometry_proximity": DEFAULT_GEOMETRY_PROXIMITY,
            "default_color_enabled": DEFAULT_COLOR_ENABLED,
            "default_geometry_enabled": DEFAULT_GEOMETRY_ENABLED,
        }

        for identifier, point in zip(identifiers, semantic_points):
            semantic_points_by_id[identifier] = point

    default_mode = "color" if modes_payload.get("color", {}).get("count", 0) > 0 else "bw"

    photos_payload = []
    for photo in photo_metadata:
        point = semantic_points_by_id.get(photo.identifier, np.zeros(2, dtype=np.float32))
        photos_payload.append(
            {
                "id": photo.identifier,
                "src": photo.src,
                "photo_mode": photo.photo_mode,
                "x": round(float(point[0]), 6),
                "y": round(float(point[1]), 6),
                "summary": photo.summary,
                "color_neighbors": color_neighbor_map.get(photo.identifier, []),
                "geometry_neighbors": geometry_neighbor_map.get(photo.identifier, []),
            }
        )

    manifest = serialize_manifest(photos_payload, default_mode, modes_payload)
    manifest["default_anchor"] = modes_payload[default_mode]["default_anchor"]
    manifest["default_selection"] = modes_payload[default_mode]["default_selection"]
    manifest["default_color_proximity"] = modes_payload[default_mode]["default_color_proximity"]
    manifest["default_geometry_proximity"] = modes_payload[default_mode]["default_geometry_proximity"]
    manifest["default_color_enabled"] = modes_payload[default_mode]["default_color_enabled"]
    manifest["default_geometry_enabled"] = modes_payload[default_mode]["default_geometry_enabled"]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Analyzed {len(photo_metadata)} photos.")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    for mode in MODE_ORDER:
        print(f"{mode}: {modes_payload[mode]['count']} photos")


if __name__ == "__main__":
    main()
