"""
Utilities for encoding/decoding images for LLM vision APIs and CV tools.
"""
from __future__ import annotations

import base64
import hashlib
import io
import mimetypes


_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


def encode_image_bytes(raw: bytes, filename: str) -> dict:
    """Encode raw image bytes into a portable dict.

    - Auto-converts TIFF → PNG via Pillow.
    - Resizes to fit within 20 MB if needed.
    - Returns {data, mime_type, filename, sha256}.
    """
    mime_type = mimetypes.guess_type(filename)[0] or "image/png"

    # Convert TIFF to PNG
    if mime_type in ("image/tiff", "image/tif") or filename.lower().endswith((".tif", ".tiff")):
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(raw))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            raw = buf.getvalue()
            mime_type = "image/png"
            filename = filename.rsplit(".", 1)[0] + ".png"
        except ImportError:
            pass  # Keep original if Pillow not available

    # Resize if too large
    if len(raw) > _MAX_BYTES:
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(raw))
            # Halve dimensions until under limit
            while len(raw) > _MAX_BYTES:
                w, h = img.size
                img = img.resize((w // 2, h // 2), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format=img.format or "PNG")
                raw = buf.getvalue()
        except ImportError:
            pass  # Keep original if Pillow not available

    data = base64.b64encode(raw).decode("utf-8")
    sha256 = hashlib.sha256(raw).hexdigest()
    return {"data": data, "mime_type": mime_type, "filename": filename, "sha256": sha256}


def to_langchain_image_block(img: dict) -> dict:
    """Build a LangChain image_url content block from an encoded image dict.

    Works for Anthropic / OpenAI / Gemini via LangChain's HumanMessage.
    """
    mime = img["mime_type"]
    data = img["data"]
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{data}"},
    }


def decode_to_numpy(img: dict):
    """Decode a base64 image dict to a numpy ndarray (BGR, OpenCV convention)."""
    import numpy as np

    raw = base64.b64decode(img["data"])
    buf = np.frombuffer(raw, dtype=np.uint8)
    try:
        import cv2
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)
    except ImportError:
        # Fallback via Pillow
        from PIL import Image
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
        arr = np.array(pil)
        return arr[:, :, ::-1]  # RGB → BGR


def decode_to_pil(img: dict):
    """Decode a base64 image dict to a PIL Image."""
    from PIL import Image

    raw = base64.b64decode(img["data"])
    return Image.open(io.BytesIO(raw))
