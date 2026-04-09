"""
Image analysis tools for the image_analyst subagent.

Each tool accepts image_data as a base64-encoded string, decodes it via
vision_utils, performs CV analysis, and returns a JSON-serializable dict.
All tools have graceful ImportError fallbacks.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from langchain_core.tools import tool

from eln.providers.vision_utils import decode_to_numpy

# Module-level run path — set by supervisor before building the graph
_image_run_path: Path | None = None


def set_image_run_path(path: Path | None) -> None:
    """Set the active run path for saving image artifacts."""
    global _image_run_path
    _image_run_path = path


# ------------------------------------------------------------------
# classify_image_type
# ------------------------------------------------------------------

@tool
def classify_image_type(image_data: str) -> str:
    """Classify a lab image into one of: western_blot, gel, microscopy, flow_cytometry, graph, unknown.

    Uses color histogram, aspect ratio, and edge density heuristics.

    Args:
        image_data: Base64-encoded image bytes.

    Returns:
        Image type string.
    """
    try:
        import numpy as np
        img = decode_to_numpy({"data": image_data, "mime_type": "image/png", "filename": "img.png"})
        if img is None:
            return "unknown"

        h, w = img.shape[:2]
        aspect = w / h if h > 0 else 1.0

        # Convert to grayscale
        gray = img.mean(axis=2) if img.ndim == 3 else img

        # Edge density
        try:
            import cv2
            edges = cv2.Canny(img, 50, 150)
            edge_density = edges.mean() / 255.0
        except ImportError:
            edge_density = 0.0

        # Color saturation
        try:
            import cv2
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1].mean() / 255.0
        except ImportError:
            saturation = 0.0

        # Brightness variance (uniform vs textured)
        brightness_var = float(np.var(gray)) / (255.0 ** 2)

        # Heuristic rules
        # Western blot / gel: dark background, horizontal bands, low saturation
        is_dark_bg = gray.mean() < 80
        has_bands = aspect > 1.2 and edge_density > 0.05 and is_dark_bg

        # Microscopy: high texture variance, moderate aspect ratio
        is_microscopy = brightness_var > 0.02 and 0.7 < aspect < 1.5 and saturation < 0.3

        # Flow cytometry: scatter plots with colored dots, square-ish
        is_flow = saturation > 0.15 and 0.8 < aspect < 1.3 and edge_density < 0.05

        # Graph / chart: axis lines, high edge density in borders
        try:
            import cv2
            top_strip = gray[:int(h * 0.1), :]
            bottom_strip = gray[int(h * 0.9):, :]
            left_strip = gray[:, :int(w * 0.1)]
            border_intensity = np.mean([top_strip.mean(), bottom_strip.mean(), left_strip.mean()])
            is_graph = border_intensity > 180 and edge_density > 0.03
        except Exception:
            is_graph = False

        if has_bands:
            # Distinguish western blot vs gel by aspect ratio
            if aspect > 1.5:
                return "western_blot"
            return "gel"
        elif is_flow:
            return "flow_cytometry"
        elif is_graph:
            return "graph"
        elif is_microscopy:
            return "microscopy"
        return "unknown"

    except Exception as e:
        return f"unknown (error: {e})"


# ------------------------------------------------------------------
# analyze_western_blot
# ------------------------------------------------------------------

@tool
def analyze_western_blot(image_data: str) -> str:
    """Analyze a western blot image: detect lanes, bands, intensities.

    Args:
        image_data: Base64-encoded image bytes.

    Returns:
        JSON string with lanes, bands list, loading_uniformity, quality.
    """
    try:
        import numpy as np
        img = decode_to_numpy({"data": image_data, "mime_type": "image/png", "filename": "img.png"})
        if img is None:
            return json.dumps({"error": "Could not decode image"})

        try:
            from skimage.filters import gaussian
            from skimage.feature import peak_local_max
        except ImportError:
            return json.dumps({"error": "scikit-image not installed", "quality": "unavailable"})

        # Convert to grayscale and invert (bands are dark on light or light on dark)
        if img.ndim == 3:
            gray = img.mean(axis=2)
        else:
            gray = img.astype(float)

        h, w = gray.shape
        # Invert if background is dark
        if gray.mean() < 128:
            gray = 255 - gray

        # Smooth
        smoothed = gaussian(gray, sigma=2)

        # Estimate number of lanes from column variance peaks
        col_var = np.var(smoothed, axis=0)
        # Rough: divide image into lanes by finding valleys in column variance
        n_lanes = max(1, int(w / (h * 0.4)))  # heuristic

        bands = []
        lane_width = w // max(n_lanes, 1)

        for lane_idx in range(n_lanes):
            x_start = lane_idx * lane_width
            x_end = min(x_start + lane_width, w)
            lane_strip = smoothed[:, x_start:x_end]
            row_profile = lane_strip.mean(axis=1)

            # Find peaks (bands)
            try:
                from scipy.signal import find_peaks
                peaks, props = find_peaks(row_profile, height=row_profile.mean(), distance=10)
                for pk in peaks:
                    intensity_rel = float(row_profile[pk]) / 255.0
                    bands.append({
                        "lane_idx": lane_idx,
                        "y_position_pct": round(float(pk) / h * 100, 1),
                        "intensity_rel": round(intensity_rel, 3),
                        "width_px": int(lane_width),
                    })
            except ImportError:
                pass

        # Loading uniformity: coefficient of variation of peak intensities per lane
        if bands:
            intensities = [b["intensity_rel"] for b in bands]
            mean_i = float(np.mean(intensities))
            std_i = float(np.std(intensities))
            loading_uniformity = round(1 - (std_i / mean_i if mean_i > 0 else 0), 3)
        else:
            loading_uniformity = None

        quality = "Good" if loading_uniformity and loading_uniformity > 0.7 else (
            "Acceptable" if loading_uniformity and loading_uniformity > 0.4 else "Poor"
        )

        return json.dumps({
            "lanes": n_lanes,
            "bands": bands,
            "loading_uniformity": loading_uniformity,
            "quality": quality,
        })

    except Exception as e:
        return json.dumps({"error": str(e), "quality": "unavailable"})


# ------------------------------------------------------------------
# analyze_gel
# ------------------------------------------------------------------

@tool
def analyze_gel(image_data: str) -> str:
    """Analyze an agarose/PAGE gel image: detect lanes, bands, ladder.

    Args:
        image_data: Base64-encoded image bytes.

    Returns:
        JSON string with lanes, bands, ladder_detected, quality.
    """
    try:
        try:
            from gelgenie.core import analyze as gelgenie_analyze  # type: ignore
            result = gelgenie_analyze(base64.b64decode(image_data))
            return json.dumps({**result, "method": "gelgenie"})
        except ImportError:
            pass

        # Fallback: scikit-image
        import numpy as np
        img = decode_to_numpy({"data": image_data, "mime_type": "image/png", "filename": "img.png"})
        if img is None:
            return json.dumps({"error": "Could not decode image"})

        try:
            from skimage.filters import gaussian
        except ImportError:
            return json.dumps({"error": "scikit-image not installed"})

        if img.ndim == 3:
            gray = img.mean(axis=2)
        else:
            gray = img.astype(float)

        h, w = gray.shape
        if gray.mean() < 128:
            gray = 255 - gray

        smoothed = gaussian(gray, sigma=1.5)
        n_lanes = max(1, int(w / (h * 0.3)))
        lane_width = w // n_lanes

        bands = []
        for lane_idx in range(n_lanes):
            x_start = lane_idx * lane_width
            x_end = min(x_start + lane_width, w)
            row_profile = smoothed[:, x_start:x_end].mean(axis=1)
            try:
                from scipy.signal import find_peaks
                peaks, _ = find_peaks(row_profile, height=row_profile.mean(), distance=8)
                for pk in peaks:
                    bands.append({
                        "lane_idx": lane_idx,
                        "y_position_pct": round(float(pk) / h * 100, 1),
                        "intensity_rel": round(float(row_profile[pk]) / 255.0, 3),
                    })
            except ImportError:
                pass

        # Ladder heuristic: first or last lane has many evenly spaced bands
        ladder_detected = False
        if bands:
            first_lane = [b for b in bands if b["lane_idx"] == 0]
            if len(first_lane) >= 5:
                ladder_detected = True

        return json.dumps({
            "lanes": n_lanes,
            "bands": bands,
            "ladder_detected": ladder_detected,
            "quality": "Good" if len(bands) > 0 else "Poor",
            "method": "scikit-image",
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


# ------------------------------------------------------------------
# analyze_microscopy
# ------------------------------------------------------------------

@tool
def analyze_microscopy(image_data: str, model_type: str = "nuclei") -> str:
    """Analyze a microscopy image: count cells, measure area, coverage.

    Uses CellPose for segmentation if available.

    Args:
        image_data: Base64-encoded image bytes.
        model_type: CellPose model type — "nuclei" or "cyto".

    Returns:
        JSON string with cell_count, avg_area_px, coverage_pct, model_used, quality.
    """
    try:
        import numpy as np
        img = decode_to_numpy({"data": image_data, "mime_type": "image/png", "filename": "img.png"})
        if img is None:
            return json.dumps({"error": "Could not decode image"})

        h, w = img.shape[:2]
        total_px = h * w

        try:
            from cellpose import models  # type: ignore

            cp_model = models.Cellpose(model_type=model_type, gpu=False)
            gray = img.mean(axis=2) if img.ndim == 3 else img
            masks, _, _, _ = cp_model.eval(gray, diameter=None, channels=[0, 0])
            cell_ids = np.unique(masks)
            cell_ids = cell_ids[cell_ids != 0]
            cell_count = len(cell_ids)
            areas = [int(np.sum(masks == cid)) for cid in cell_ids]
            avg_area = float(np.mean(areas)) if areas else 0.0
            coverage = float(np.sum(masks > 0)) / total_px * 100

            return json.dumps({
                "cell_count": cell_count,
                "avg_area_px": round(avg_area, 1),
                "coverage_pct": round(coverage, 2),
                "model_used": f"cellpose_{model_type}",
                "quality": "Good",
            })
        except ImportError:
            pass

        # Fallback: threshold-based counting
        try:
            import cv2
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Filter by minimum area
            min_area = total_px * 0.0005
            cells = [c for c in contours if cv2.contourArea(c) > min_area]
            cell_count = len(cells)
            areas_list = [cv2.contourArea(c) for c in cells]
            avg_area = float(sum(areas_list) / len(areas_list)) if areas_list else 0.0
            coverage = sum(areas_list) / total_px * 100

            return json.dumps({
                "cell_count": cell_count,
                "avg_area_px": round(avg_area, 1),
                "coverage_pct": round(coverage, 2),
                "model_used": "opencv_threshold",
                "quality": "Acceptable",
            })
        except ImportError:
            return json.dumps({"error": "cv2 not installed", "model_used": "none"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ------------------------------------------------------------------
# analyze_flow_plot
# ------------------------------------------------------------------

@tool
def analyze_flow_plot(image_data: str) -> str:
    """Analyze a flow cytometry scatter plot image.

    Detects plot type, populations, and axis labels via OpenCV + heuristics.

    Args:
        image_data: Base64-encoded image bytes.

    Returns:
        JSON string with plot_type, populations, axes_detected.
    """
    try:
        import numpy as np
        img = decode_to_numpy({"data": image_data, "mime_type": "image/png", "filename": "img.png"})
        if img is None:
            return json.dumps({"error": "Could not decode image"})

        try:
            import cv2
        except ImportError:
            return json.dumps({"error": "opencv-python not installed"})

        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Count distinct color clusters (populations)
        saturation = hsv[:, :, 1]
        high_sat_mask = saturation > 80
        high_sat_pct = float(high_sat_mask.mean()) * 100

        # Estimate populations by color clustering
        populations = []
        if high_sat_pct > 5:
            # Simple: count distinct hue ranges
            hues = hsv[high_sat_mask, 0]
            if len(hues) > 0:
                import numpy as np
                hist, _ = np.histogram(hues, bins=6, range=(0, 180))
                n_pops = int(np.sum(hist > len(hues) * 0.05))
                populations = [{"population_index": i, "approx_pct": round(float(hist[i]) / len(hues) * 100, 1)}
                               for i in range(6) if hist[i] > len(hues) * 0.05]

        # Detect axes (white borders)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        axes_detected = bool(gray[h - 5:h, :].mean() > 200 or gray[:, :5].mean() > 200)

        # Determine plot type
        if high_sat_pct > 10:
            plot_type = "scatter_colored"
        else:
            plot_type = "density_or_contour"

        return json.dumps({
            "plot_type": plot_type,
            "populations": populations,
            "axes_detected": axes_detected,
            "high_saturation_pct": round(high_sat_pct, 1),
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


# ------------------------------------------------------------------
# extract_plot_data
# ------------------------------------------------------------------

@tool
def extract_plot_data(image_data: str) -> str:
    """Extract metadata from a scientific graph/chart image.

    Detects axes, labels, trend direction, error bars, and statistical annotations.

    Args:
        image_data: Base64-encoded image bytes.

    Returns:
        JSON string with has_axes, x_label, y_label, trend, error_bars_visible,
        statistical_annotations.
    """
    try:
        import numpy as np
        img = decode_to_numpy({"data": image_data, "mime_type": "image/png", "filename": "img.png"})
        if img is None:
            return json.dumps({"error": "Could not decode image"})

        try:
            import cv2
        except ImportError:
            return json.dumps({"error": "opencv-python not installed"})

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

        # Detect axes via Hough lines
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=w // 4, maxLineGap=10)
        has_axes = lines is not None and len(lines) >= 2

        # Estimate trend: compare left-half vs right-half brightness in plot area
        plot_region = gray[int(h * 0.1):int(h * 0.9), int(w * 0.1):int(w * 0.9)]
        left_mean = float(plot_region[:, :plot_region.shape[1] // 2].mean())
        right_mean = float(plot_region[:, plot_region.shape[1] // 2:].mean())
        # Lower pixel value = darker = more data
        if left_mean > right_mean + 10:
            trend = "increasing"
        elif right_mean > left_mean + 10:
            trend = "decreasing"
        else:
            trend = "flat_or_unclear"

        # Error bars: look for short vertical lines clustered above data points
        small_v_lines = 0
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                dx, dy = abs(x2 - x1), abs(y2 - y1)
                if dy > 0 and dx < 5 and 5 < dy < h * 0.1:
                    small_v_lines += 1
        error_bars_visible = small_v_lines >= 3

        # Statistical annotations: look for asterisk-like bright spots
        _, bright = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        statistical_annotations = int(bright[int(h * 0.05):int(h * 0.3), :].mean()) > 5

        return json.dumps({
            "has_axes": has_axes,
            "x_label": None,  # OCR not available without pytesseract
            "y_label": None,
            "trend": trend,
            "error_bars_visible": error_bars_visible,
            "statistical_annotations": statistical_annotations,
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


# ------------------------------------------------------------------
# call_biomedparse
# ------------------------------------------------------------------

@tool
def call_biomedparse(image_data: str, prompt: str = "") -> str:
    """Call BiomedParse endpoint for biomedical image segmentation.

    Requires BIOMEDPARSE_ENDPOINT_URL configured in settings.

    Args:
        image_data: Base64-encoded image bytes.
        prompt: Optional text prompt for guided segmentation.

    Returns:
        JSON string with segments, labels, or error if not configured.
    """
    try:
        from eln.config import settings

        url = settings.biomedparse_endpoint_url
        if not url:
            return json.dumps({
                "error": "BiomedParse endpoint not configured. "
                         "Set BIOMEDPARSE_ENDPOINT_URL in .env to enable this feature."
            })

        import httpx

        payload = {"image": image_data, "prompt": prompt}
        response = httpx.post(url, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.text

    except Exception as e:
        return json.dumps({"error": str(e), "segments": [], "labels": []})


# ------------------------------------------------------------------
# save_image_artifact
# ------------------------------------------------------------------

@tool
def save_image_artifact(
    image_data: str,
    mime_type: str,
    filename: str,
    image_type: str,
    analysis_summary: str,
) -> str:
    """Save an image as a run artifact and register it in the artifact manifest.

    Args:
        image_data: Base64-encoded image bytes.
        mime_type: MIME type (e.g. "image/png").
        filename: Desired filename for the artifact.
        image_type: Classified image type (e.g. "western_blot").
        analysis_summary: One-sentence summary of the CV tool output.

    Returns:
        artifact_id on success, or an error message.
    """
    try:
        import hashlib
        from datetime import datetime
        from eln.models.artifact import ArtifactManifest, ArtifactRecord, ArtifactType, CreatedBy
        from eln.workspace.run_store import RunStore

        run_path = _image_run_path
        if run_path is None:
            return "No active run path set — image artifact not saved."

        raw = base64.b64decode(image_data)
        sha256 = hashlib.sha256(raw).hexdigest()

        artifacts_dir = run_path / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Deduplicate by sha256
        dest = artifacts_dir / filename
        if not dest.exists():
            dest.write_bytes(raw)

        record = ArtifactRecord(
            path=f"artifacts/{filename}",
            artifact_type=ArtifactType.IMAGE,
            sha256=sha256,
            created_by=CreatedBy.AGENT,
            image_type=image_type,
            analysis_summary=analysis_summary,
            tool_provenance={"tool": "image_analyst", "image_type": image_type},
        )

        store = RunStore(run_path)
        manifest = store.load_artifact_manifest()
        # Skip if same sha256 already registered
        if not any(a.sha256 == sha256 for a in manifest.artifacts):
            manifest.add(record)
            store.save_artifact_manifest(manifest)

        return record.artifact_id

    except Exception as e:
        return f"Error saving artifact: {e}"


# Convenience list for supervisor registration
image_tools = [
    classify_image_type,
    analyze_western_blot,
    analyze_gel,
    analyze_microscopy,
    analyze_flow_plot,
    extract_plot_data,
    call_biomedparse,
    save_image_artifact,
]
