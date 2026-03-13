from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import umap
from PIL import Image, ImageOps
from scipy.fft import dctn
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
PHOTOS_DIR = ROOT / "photos"
OUTPUT_PATH = ROOT / "_data" / "gallery_metadata.json"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SEED = 42
DEFAULT_COUNT = 9
ANALYSIS_SIZE = 128


@dataclass
class PhotoMetadata:
    identifier: str
    src: str
    summary: dict[str, float]
    appearance_vector: np.ndarray
    color_vector: np.ndarray
    perceptual_vector: np.ndarray
    edge_vector: np.ndarray


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

    # Drop the DC component and normalize the remaining low-frequency structure.
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

    hue = (hue / 6.0) % 1.0
    return hue.astype(np.float32)


def extract_features(path: Path) -> PhotoMetadata:
    rgb = open_rgb_array(path)
    flat_rgb = rgb.reshape(-1, 3)
    grayscale = (0.299 * rgb[:, :, 0]) + (0.587 * rgb[:, :, 1]) + (0.114 * rgb[:, :, 2])

    rgb_mean = flat_rgb.mean(axis=0)
    rgb_std = flat_rgb.std(axis=0)
    rgb_quantiles = np.quantile(flat_rgb, [0.1, 0.5, 0.9], axis=0).reshape(-1)

    value = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    saturation = np.divide(value - minimum, value + 1e-6)
    hue = hue_channel(rgb)

    gray_quantiles = np.quantile(grayscale, [0.1, 0.5, 0.9])
    gray_histogram, _ = np.histogram(grayscale, bins=12, range=(0.0, 1.0), density=True)
    saturation_histogram, _ = np.histogram(saturation, bins=8, range=(0.0, 1.0), density=True)
    hue_histogram, _ = np.histogram(
        hue,
        bins=12,
        range=(0.0, 1.0),
        weights=(saturation * value) + 1e-6,
        density=True,
    )
    hue_histogram = np.nan_to_num(hue_histogram, nan=0.0)

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

    appearance_vector = np.concatenate(
        [
            rgb_mean,
            rgb_std,
            rgb_quantiles,
            np.asarray(
                [
                    grayscale.mean(),
                    grayscale.std(),
                    gray_quantiles[0],
                    gray_quantiles[1],
                    gray_quantiles[2],
                    gray_quantiles[2] - gray_quantiles[0],
                    saturation.mean(),
                    saturation.std(),
                    float(np.quantile(saturation, 0.9)),
                    gradient_magnitude.mean(),
                    gradient_magnitude.std(),
                    float(np.quantile(gradient_magnitude, 0.9)),
                    edge_density,
                    vertical_symmetry,
                    horizontal_symmetry,
                    x_center,
                    y_center,
                ],
                dtype=np.float32,
            ),
            gray_histogram.astype(np.float32),
            saturation_histogram.astype(np.float32),
            orientation_histogram.astype(np.float32),
            grid_means(grayscale),
            grid_means(saturation),
            grid_means(gradient_magnitude),
        ]
    ).astype(np.float32)

    color_vector = np.concatenate(
        [
            rgb_mean.astype(np.float32),
            rgb_std.astype(np.float32),
            np.asarray(
                [
                    float(rgb_mean[0] - rgb_mean[2]),
                    float(rgb_mean[1] - rgb_mean[2]),
                    float(saturation.mean()),
                    float(np.quantile(saturation, 0.9)),
                ],
                dtype=np.float32,
            ),
            hue_histogram.astype(np.float32),
            grid_means(rgb[:, :, 0]),
            grid_means(rgb[:, :, 1]),
            grid_means(rgb[:, :, 2]),
        ]
    ).astype(np.float32)

    edge_reference = gradient_magnitude / max(float(np.quantile(gradient_magnitude, 0.98)), 1e-6)
    perceptual_vector = dct_signature(grayscale)
    edge_vector = dct_signature(np.clip(edge_reference, 0.0, 1.0))

    dominant_hue_index = int(np.argmax(hue_histogram))
    dominant_hue_deg = ((dominant_hue_index + 0.5) / len(hue_histogram)) * 360.0

    summary = {
        "brightness": round(float(grayscale.mean()), 6),
        "contrast": round(float(grayscale.std()), 6),
        "saturation": round(float(saturation.mean()), 6),
        "red": round(float(rgb_mean[0]), 6),
        "green": round(float(rgb_mean[1]), 6),
        "blue": round(float(rgb_mean[2]), 6),
        "warmth": round(float(rgb_mean[0] - rgb_mean[2]), 6),
        "hue_peak_deg": round(float(dominant_hue_deg), 3),
        "edge_density": round(edge_density, 6),
        "vertical_symmetry": round(vertical_symmetry, 6),
        "horizontal_symmetry": round(horizontal_symmetry, 6),
    }

    return PhotoMetadata(
        identifier=path.name,
        src=f"/photos/{path.name}",
        summary=summary,
        appearance_vector=appearance_vector,
        color_vector=color_vector,
        perceptual_vector=perceptual_vector,
        edge_vector=edge_vector,
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


def combine_feature_groups(photo_metadata: list[PhotoMetadata]) -> np.ndarray:
    appearance_matrix = np.vstack([photo.appearance_vector for photo in photo_metadata])
    color_matrix = np.vstack([photo.color_vector for photo in photo_metadata])
    perceptual_matrix = np.vstack([photo.perceptual_vector for photo in photo_metadata])
    edge_matrix = np.vstack([photo.edge_vector for photo in photo_metadata])

    combined = np.concatenate(
        [
            StandardScaler().fit_transform(appearance_matrix) * 0.72,
            StandardScaler().fit_transform(color_matrix) * 1.15,
            StandardScaler().fit_transform(perceptual_matrix) * 2.4,
            StandardScaler().fit_transform(edge_matrix) * 1.35,
        ],
        axis=1,
    )
    return combined.astype(np.float32)


def compute_embedding(feature_matrix: np.ndarray) -> np.ndarray:
    if feature_matrix.shape[0] == 1:
        return np.zeros((1, 2), dtype=np.float32)

    if feature_matrix.shape[0] == 2:
        return np.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=np.float32)

    n_neighbors = max(2, min(24, feature_matrix.shape[0] - 1))
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=0.04,
        metric="cosine",
        random_state=SEED,
        transform_seed=SEED,
        init="spectral",
    )
    embedding = reducer.fit_transform(feature_matrix)
    return embedding.astype(np.float32)


def euclidean_distances(points: np.ndarray) -> np.ndarray:
    deltas = points[:, None, :] - points[None, :, :]
    return np.sqrt(np.sum(deltas * deltas, axis=2))


def nearest_neighbor_ids(identifiers: list[str], points: np.ndarray) -> dict[str, list[str]]:
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


def select_default_neighbors(anchor_id: str, neighbor_map: dict[str, list[str]], max_count: int) -> list[str]:
    selection = [anchor_id]
    selection.extend(neighbor_map[anchor_id][: max_count - 1])
    return selection


def choose_default_anchor(identifiers: list[str], points: np.ndarray) -> str:
    centroid = points.mean(axis=0)
    centroid_distances = np.linalg.norm(points - centroid, axis=1)
    return identifiers[int(np.argmin(centroid_distances))]


def serialize_manifest(photos: Iterable[dict[str, object]]) -> dict[str, object]:
    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "feature_spec": {
            "resize": ANALYSIS_SIZE,
            "reducer": "UMAP",
            "similarity_space": "Weighted feature space for neighbors, 2D UMAP for coordinates",
            "components": [
                "rgb_statistics",
                "grayscale_histogram",
                "saturation_histogram",
                "edge_orientation_histogram",
                "3x3 spatial grids for luminance, saturation, and edge energy",
                "symmetry and composition metrics",
                "hue histogram",
                "3x3 RGB color layout",
                "perceptual DCT signature",
                "edge DCT signature",
            ],
        },
        "photos": list(photos),
    }


def main() -> None:
    photo_paths = load_photo_paths()
    photo_metadata = [extract_features(path) for path in photo_paths]

    identifiers = [photo.identifier for photo in photo_metadata]
    feature_matrix = combine_feature_groups(photo_metadata)
    embedding = compute_embedding(feature_matrix)
    neighbor_map = nearest_neighbor_ids(identifiers, feature_matrix)

    default_anchor = choose_default_anchor(identifiers, embedding)
    default_selection = select_default_neighbors(
        default_anchor,
        neighbor_map,
        max_count=min(DEFAULT_COUNT, len(photo_metadata)),
    )

    photos_payload = []
    for photo, point in zip(photo_metadata, embedding):
        photos_payload.append(
            {
                "id": photo.identifier,
                "src": photo.src,
                "x": round(float(point[0]), 6),
                "y": round(float(point[1]), 6),
                "summary": photo.summary,
                "neighbors": neighbor_map[photo.identifier],
            }
        )

    manifest = serialize_manifest(photos_payload)
    manifest["default_anchor"] = default_anchor
    manifest["default_selection"] = default_selection

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Analyzed {len(photo_metadata)} photos.")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Default anchor: {default_anchor}")


if __name__ == "__main__":
    main()
