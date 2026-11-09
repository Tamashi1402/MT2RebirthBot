"""MacroForge .macro container format (v3)

A .macro file is now EITHER the legacy text format (still fully
supported) or a ZIP container — sniffed by magic bytes, no extension
change:

    PK\x03\x04
    ├─ manifest.json       format marker + name + versions + save time
    ├─ generated_code.txt  the canonical macro text — ALWAYS regenerated
    │                      on save; what the engine plays (legacy tools
    │                      and hand-editing keep working on this member)
    ├─ blockly.xaml        the editor's exact Blockly workspace XML —
    │                      1:1: layout, strays, groups, mutators, notes.
    │                      Absent = workspace stale (rebuild from steps),
    │                      e.g. after a recording appended steps.
    └─ images/…            every image the macro references, embedded
                           (playback extracts them next to the generated
                           code so relative refs resolve in a clean temp)

The engine and all readers go through the two sniff helpers, so legacy
text .macro files keep loading unchanged and containers read anywhere.
"""

import io
import json
import os
import re
import shutil
import tempfile
import zipfile

CONTAINER_FORMAT = "macroforge-container"
CONTAINER_VERSION = 1
CONTAINER_MAGIC = b"PK\x03\x04"

MANIFEST_NAME = "manifest.json"
CODE_NAME = "generated_code.txt"
BLOCKLY_NAME = "blockly.xaml"
IMAGES_PREFIX = "images/"

_IMAGE_REF_RE = re.compile(
    r'[A-Za-z0-9_\-./\\]{2,200}?\.(?:png|jpg|jpeg|bmp|gif|webp)\b',
    re.IGNORECASE,
)
_MAX_EMBEDDED_IMAGE_BYTES = 32 * 1024 * 1024   # skip absurdly huge files


# ── sniffing ────────────────────────────────────────────────────────────────

def is_container_bytes(data: bytes) -> bool:
    """True when the file content is a container (zip magic up front)."""
    return bool(data) and data[:4] == CONTAINER_MAGIC


def is_container_file(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return is_container_bytes(f.read(4))
    except Exception:
        return False


# ── reading ────────────────────────────────────────────────────────────────

def _zip_from(data: bytes) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(data))


def read_generated_text(data: bytes) -> str:
    """The canonical macro text inside a container."""
    with _zip_from(data) as z:
        try:
            return z.read(CODE_NAME).decode("utf-8", errors="replace")
        except KeyError:
            return ""


def read_blockly_xml(data: bytes):
    """The embedded workspace XML, or None when absent/stale."""
    with _zip_from(data) as z:
        try:
            raw = z.read(BLOCKLY_NAME)
        except KeyError:
            return None
        try:
            return raw.decode("utf-8", errors="replace")
        except Exception:
            return None


def read_manifest(data: bytes) -> dict:
    try:
        with _zip_from(data) as z:
            return json.loads(z.read(MANIFEST_NAME).decode("utf-8"))
    except Exception:
        return {}


def read_macro_text(path: str) -> str:
    """Read a .macro file's canonical text — container OR legacy.

    Every existing text parser call site funnels through here so both
    formats read identically.
    """
    with open(path, "rb") as f:
        data = f.read()
    if is_container_bytes(data):
        return read_generated_text(data)
    return data.decode("utf-8", errors="replace")


# ── image collection ────────────────────────────────────────────────────────

def collect_image_refs(blocks) -> set:
    """Every path-like image reference in any step payload."""
    refs: set = set()
    for step in blocks or []:
        if not isinstance(step, dict):
            continue
        value = str(step.get("value") or "")
        if not value:
            continue
        for m in _IMAGE_REF_RE.finditer(value):
            refs.add(m.group(0).replace("\\", "/").lstrip("/"))
    return refs


def _image_members(blocks, resolve) -> dict:
    """{arcname: absolute source path} for every referenced readable image.

    `resolve(ref)` must return an existing absolute file path or ''.
    Files land flat under images/<basename> (the image picker saves flat
    into <macro folder>/images — subpath refs resolve through the same
    basename fallback the engine uses).
    """
    members: dict = {}
    for ref in collect_image_refs(blocks):
        src = resolve(ref)
        if not src or not os.path.isfile(src):
            continue
        base = os.path.basename(src.replace("\\", "/"))
        if base:
            members[IMAGES_PREFIX + base] = src
    return members


# ── writing ────────────────────────────────────────────────────────────────

def _app_version() -> str:
    try:
        from version import __version__
        return str(__version__)
    except Exception:
        return ""


def pack_container(path: str, name: str, generated_text: str,
                   blockly_xml=None, blocks=None, resolve=None,
                   keep_images_from: str = "") -> None:
    """Write the container atomically.

    keep_images_from: an existing container file whose images/ members
    are carried over first (editing a packed macro whose images live only
    inside the container) — fresh resolved files overwrite by basename.
    """
    import time as _time

    members: dict = {}   # arcname -> ("bytes" | "path", payload)

    if keep_images_from and os.path.isfile(keep_images_from):
        try:
            with open(keep_images_from, "rb") as f:
                data = f.read()
            if is_container_bytes(data):
                with _zip_from(data) as z:
                    for info in z.infolist():
                        if info.filename.startswith(IMAGES_PREFIX) and not info.is_dir():
                            members[info.filename] = ("bytes", z.read(info.filename))
        except Exception:
            pass

    if resolve and blocks:
        for arc, src in _image_members(blocks, resolve).items():
            try:
                if os.path.getsize(src) > _MAX_EMBEDDED_IMAGE_BYTES:
                    continue
                with open(src, "rb") as f:
                    members[arc] = ("bytes", f.read())
            except Exception:
                continue

    manifest = {
        "format": CONTAINER_FORMAT,
        "version": CONTAINER_VERSION,
        "name": name,
        "app_version": _app_version(),
        "saved_at": _time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    folder = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(folder, exist_ok=True)
    tmp_path = os.path.join(folder, f".{os.path.basename(path)}.{os.getpid()}.tmp")
    try:
        with open(tmp_path, "wb") as f:
            with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr(MANIFEST_NAME, json.dumps(manifest, indent=1))
                z.writestr(CODE_NAME, generated_text)
                if blockly_xml:
                    z.writestr(BLOCKLY_NAME, blockly_xml)
                for arc in sorted(members):
                    kind, payload = members[arc]
                    if kind == "bytes":
                        z.writestr(arc, payload)
                    else:
                        z.write(payload, arc)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── playback extraction ──────────────────────────────────────────────────────

def extract_for_playback(container_path: str) -> str:
    """Clean-extract a container and return the generated text's path.

    The temp dir is wiped and rebuilt on EVERY playback (user-requested:
    'on playback clean temp and unzip'). Images are written to
    <dest>/images/<name> AND <dest>/<name> so both 'images/x.png' and
    'x.png' reference styles resolve against the extraction dir.
    """
    import hashlib

    with open(container_path, "rb") as f:
        data = f.read()
    if not is_container_bytes(data):
        return container_path

    digest = hashlib.sha1(os.path.abspath(container_path).encode("utf-8")).hexdigest()[:16]
    dest = os.path.join(tempfile.gettempdir(), "macroforge_pb", digest)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest, exist_ok=True)

    text = read_generated_text(data)
    code_path = os.path.join(dest, CODE_NAME)
    with open(code_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    with _zip_from(data) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.startswith(IMAGES_PREFIX):
                continue
            name = info.filename[len(IMAGES_PREFIX):]
            if not name or "/" in name or "\\" in name:
                continue
            try:
                blob = z.read(info.filename)
            except Exception:
                continue
            try:
                img_dir = os.path.join(dest, "images")
                os.makedirs(img_dir, exist_ok=True)
                with open(os.path.join(img_dir, name), "wb") as f:
                    f.write(blob)
                with open(os.path.join(dest, name), "wb") as f:
                    f.write(blob)
            except Exception:
                continue
    return code_path
