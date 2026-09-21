import json
import logging
import math
import os
import re
import tempfile
import threading
import time
from typing import Any

import cv2
import mss
import numpy as np

log = logging.getLogger(__name__)


def parse_payload(raw: str, prefix: str) -> dict[str, Any]:
    text = raw[len(prefix):].strip()
    if text.startswith(":"):
        text = text[1:].strip()
    try:
        data = json.loads(text) if text else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value) != 0.0
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def define_variable(vars_state: dict[str, Any], data: dict[str, Any]) -> None:
    name = str(data.get("name") or "").strip()
    if not name:
        return
    vtype = str(data.get("var_type") or "number").strip().lower()
    if vtype == "boolean":
        vars_state[name] = truthy(data.get("value", False))
    elif vtype == "text" or vtype in ("image", "resloc"):
        vars_state[name] = str(data.get("value", "") or "")
    else:
        try:
            vars_state[name] = float(data.get("value", 0) or 0)
        except Exception:
            vars_state[name] = 0.0


def set_variable(vars_state: dict[str, Any], data: dict[str, Any],
                bot_root: str = "", macro_dir: str | None = None) -> None:
    name = str(data.get("name") or "").strip()
    if not name:
        return
    op = str(data.get("op") or "set").strip().lower()
    raw_value = data.get("value", 0)
    if isinstance(raw_value, dict):
        # expanded format: expression tree (get / compare / math / image)
        vars_state[name] = eval_expr(raw_value, vars_state, bot_root, macro_dir)
        return
    cur = vars_state.get(name, False if isinstance(raw_value, bool) else 0.0)
    if op == "toggle":
        vars_state[name] = not truthy(cur)
        return
    if isinstance(cur, bool) or str(raw_value).strip().lower() in {"true", "false", "yes", "no", "on", "off"}:
        vars_state[name] = truthy(raw_value)
        return
    try:
        val = float(raw_value or 0)
    except Exception:
        val = 0.0
    try:
        cur_num = float(cur or 0)
    except Exception:
        cur_num = 0.0
    if op == "add":
        vars_state[name] = cur_num + val
    elif op == "subtract":
        vars_state[name] = cur_num - val
    else:
        vars_state[name] = val


def _expr_to_num(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


# ── Resolution scaling (1:1 with engine/pcr_runtime._pcr_res_scale) ────────
# A recorded coordinate can carry a resolution spec: the point/box was
# recorded at dw x dh with content aspect ratio rw:rh. At playback the
# values are mapped into the centered rw:rh content area of the CURRENT
# screen (letterbox/pillarbox, like a fullscreen game) — no window
# anchoring needed.

def _macro_res_spec(rw, rh, dw, dh):
    """(rw, rh, dw, dh) ints, sanitized — mirrors _pcr_res_spec."""
    try:
        rw, rh, dw, dh = int(rw), int(rh), int(dw), int(dh)
    except Exception:
        rw, rh, dw, dh = 16, 9, 1920, 1080
    if rw <= 0 or rh <= 0:
        rw, rh = 16, 9
    if dw <= 0 or dh <= 0:
        dw, dh = 1920, 1080
    return (rw, rh, dw, dh)


def _macro_res_scale(value, spec=(16, 9, 1920, 1080)):
    """Scale a recorded point/box to the current screen — mirrors
    _pcr_res_scale 1:1 (same letterbox math, same clamping)."""
    rw, rh, dw, dh = _macro_res_spec(spec[0], spec[1], spec[2], spec[3])
    ratio = rw / float(rh)

    try:
        from engine.pcr_runtime import _pcr_screen_size
        cur_w, cur_h = _pcr_screen_size()
    except Exception:
        try:
            from macro_logic import _screen_size   # bot layout (config RUNTIME_*)
            cur_w, cur_h = _screen_size()
        except Exception:
            cur_w, cur_h = dw, dh

    # Largest rw:rh content rect, centered on the current screen.
    if cur_w / float(cur_h) > ratio:
        ch = cur_h
        cw = int(round(cur_h * ratio))
        ox = (cur_w - cw) // 2
        oy = 0
    else:
        cw = cur_w
        ch = int(round(cur_w / ratio))
        ox = 0
        oy = (cur_h - ch) // 2

    sx = cw / float(dw)
    sy = ch / float(dh)

    try:
        vals = [float(v) for v in list(value)[:4]]
    except Exception:
        return value
    if len(vals) >= 4:
        x1, y1, x2, y2 = vals
        x1 = max(0, min(cur_w - 1, ox + int(round(x1 * sx))))
        y1 = max(0, min(cur_h - 1, oy + int(round(y1 * sy))))
        x2 = max(1, min(cur_w, ox + int(round(x2 * sx))))
        y2 = max(1, min(cur_h, oy + int(round(y2 * sy))))
        if x2 <= x1:
            x2 = min(cur_w, x1 + 1)
        if y2 <= y1:
            y2 = min(cur_h, y1 + 1)
        return (x1, y1, x2, y2)
    x, y = vals[0], vals[1]
    x = max(0, min(cur_w - 1, ox + int(round(x * sx))))
    y = max(0, min(cur_h - 1, oy + int(round(y * sy))))
    return (x, y)


def _expr_res_scale(d: dict[str, Any], vars_state: dict[str, Any]):
    """{res_scale: {a, spec}} -> scaled (x, y) or (x1, y1, x2, y2)."""
    a = eval_expr(d.get("a"), vars_state)
    if not isinstance(a, (tuple, list)):
        a = (a, a)
    spec = (16, 9, 1920, 1080)
    if d.get("spec") is not None:
        s = eval_expr(d.get("spec"), vars_state)
        if isinstance(s, (tuple, list)) and len(s) >= 4:
            spec = (s[0], s[1], s[2], s[3])
    return _macro_res_scale(a, spec)


def _coord_val(v: Any, vars_state: dict[str, Any], idx: int) -> int:
    """A coordinate value: plain number or expression tree.

    A {res_scale} (or {point}/{box}) node evaluates to a tuple — idx picks
    the element (x→0, y→1, x2→2, y2→3). Old payloads pass numbers and stay
    on the fast path.
    """
    if isinstance(v, dict):
        try:
            r = eval_expr(v, vars_state)
        except Exception:
            return 0
        if isinstance(r, (tuple, list)):
            try:
                return int(round(float(r[idx])))
            except Exception:
                return 0
        try:
            return int(round(float(r)))
        except Exception:
            return 0
    try:
        return int(round(float(v)))
    except Exception:
        return 0


def resolve_region_exprs(data: dict[str, Any], vars_state: dict[str, Any]) -> dict[str, Any]:
    """IMAGE payloads / img_on_screen conditions may carry expression trees
    in their region keys (a scaled search box). Resolve them to ints before
    matching; plain numbers pass through untouched."""
    d = dict(data)
    names = ("x1", "y1", "x2", "y2")
    for prefix in ("", "search_"):
        for i, n in enumerate(names):
            k = prefix + n
            v = d.get(k)
            if isinstance(v, dict):
                d[k] = _coord_val(v, vars_state, i)
    return d


def _img_operand_path(v: Any, vars_state: dict[str, Any],
                       bot_root: str, macro_dir: str | None) -> str:
    """Path value ('' | str | {get}) -> filesystem path ('' if none).

    {get} looks up an image VARIABLE (set by set image) and uses whatever
    path/text it currently holds.
    """
    if isinstance(v, dict):
        v = eval_expr(v, vars_state, bot_root, macro_dir)
    return _resolve_image_path(str(v or ""), bot_root, macro_dir)


def _parse_color_rgb(v: Any):
    """'#RRGGBB' / 'rgb(r,g,b)' / 'rgba(r,g,b,a)' / [r,g,b] -> (r, g, b), or None.

    1:1 with the flow engine's _pcr_parse_hex_color semantics (plus the
    rgba()/list forms the color blocks emit).
    """
    if isinstance(v, (list, tuple)):
        try:
            nums = [float(x) for x in list(v)[:3]]
        except Exception:
            return None
        if len(nums) < 3:
            return None
        return (max(0.0, min(255.0, nums[0])), max(0.0, min(255.0, nums[1])), max(0.0, min(255.0, nums[2])))
    if not isinstance(v, str):
        return None
    s = v.strip()
    m = re.match(r"^rgba?\(\s*([\d.]+)\s*[,\s]\s*([\d.]+)\s*[,\s]\s*([\d.]+)", s)
    if m:
        try:
            return (float(m.group(1)), float(m.group(2)), float(m.group(3)))
        except ValueError:
            return None
    h = s.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) < 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def _expr_color_diff(d: dict[str, Any], vars_state: dict[str, Any],
                     bot_root: str, macro_dir: str | None) -> float:
    """get color difference between [] and [] — 0.0 (identical) to 1.0.

    1:1 with the flow engine's _pcr_color_diff; -1.0 when either operand
    is not a color.
    """
    a = eval_expr(d.get("a"), vars_state, bot_root, macro_dir)
    b = eval_expr(d.get("b"), vars_state, bot_root, macro_dir)
    ca, cb = _parse_color_rgb(a), _parse_color_rgb(b)
    if ca is None or cb is None:
        return -1.0
    dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(ca, cb)))
    return round(dist / (255.0 * math.sqrt(3.0)), 3)


# Decoded-image cache, keyed (abspath, mtime_ns, size) -> float32 RGB.
# Tight WHILE/UNTIL image conditions re-read the SAME template every
# pass — decoding a 1080p PNG + converting to float32 costs 30-60ms PER
# PASS. With the cache it's a one-time cost (grab buffers are unique
# temp files, so they always miss and re-decode — correct, they change
# every pass). Byte-budgeted so a few big templates can't eat RAM.
_IMG_DECODE_CACHE: dict[tuple, np.ndarray] = {}
_IMG_DECODE_CACHE_MAX_BYTES = 128 * 1024 * 1024


def _cached_rgb_f32(path: str) -> np.ndarray | None:
    """Decoded float32 RGB array for an image path, cached by mtime+size."""
    try:
        st = os.stat(path)
        key = (path, st.st_mtime_ns, st.st_size)
    except OSError:
        return None
    hit = _IMG_DECODE_CACHE.get(key)
    if hit is not None:
        return hit
    try:
        from PIL import Image  # noqa: TID252 — runtime dep
        arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
    except Exception:
        return None
    if arr.size == 0:
        return None
    _IMG_DECODE_CACHE[key] = arr
    _total = 0
    for _k, _v in reversed(list(_IMG_DECODE_CACHE.items())):
        _total += int(_v.nbytes)
        if _total > _IMG_DECODE_CACHE_MAX_BYTES:
            _IMG_DECODE_CACHE.pop(_k)
    return arr


def _expr_img_diff(d: dict[str, Any], vars_state: dict[str, Any],
                   bot_root: str, macro_dir: str | None) -> float:
    """get image difference between [] and [] — mean pixel difference of
    two image files, 0.0 (identical) to 1.0 (max).

    1:1 with the flow engine's _pcr_img_diff (sizes auto-matched, -1.0 on
    failure).
    """
    pa = _img_operand_path(d.get("a"), vars_state, bot_root, macro_dir)
    pb = _img_operand_path(d.get("b"), vars_state, bot_root, macro_dir)
    if not pa or not pb or not os.path.isfile(pa) or not os.path.isfile(pb):
        return -1.0
    try:
        from PIL import Image  # noqa: TID252 — runtime dep (resize path)
        arr_a = _cached_rgb_f32(pa)
        arr_b = _cached_rgb_f32(pb)
        if arr_a is None or arr_b is None:
            return -1.0
        if arr_a.shape != arr_b.shape:
            arr_b = np.asarray(
                Image.fromarray(arr_b.astype(np.uint8)).resize((arr_a.shape[1], arr_a.shape[0])),
                dtype=np.float32,
            )
        if arr_a.shape != arr_b.shape:
            return -1.0
        return float(round(float(np.mean(np.abs(arr_a - arr_b))) / 255.0, 3))
    except Exception:
        return -1.0


def _expr_img_eq(d: dict[str, Any], vars_state: dict[str, Any],
                 bot_root: str, macro_dir: str | None) -> bool:
    """[image] = [image] — pixel-by-pixel compare of two image files."""
    pa = _img_operand_path(d.get("a"), vars_state, bot_root, macro_dir)
    pb = _img_operand_path(d.get("b"), vars_state, bot_root, macro_dir)
    if not pa or not pb or not os.path.isfile(pa) or not os.path.isfile(pb):
        return False
    try:
        arr_a, arr_b = _cached_rgb_f32(pa), _cached_rgb_f32(pb)
        if arr_a is None or arr_b is None:
            return False
        eq = bool(arr_a.shape == arr_b.shape and np.array_equal(arr_a, arr_b))
        return (not eq) if bool(d.get("neq")) else eq
    except Exception:
        return False


def _expr_color_eq(d: dict[str, Any], vars_state: dict[str, Any] | None = None) -> bool:
    """[color] = [color] — screen color at a point vs an rgba literal.

    x/y are plain numbers (old payloads) or expression trees — a
    {res_scale} node evaluates to a (x, y) tuple, element 0/1 is the coord.
    """
    vs = vars_state if vars_state is not None else {}
    x, y = _coord_val(d.get("x"), vs, 0), _coord_val(d.get("y"), vs, 1)
    rgba = d.get("rgba") or [255, 255, 255, 255]
    tol = int(_expr_to_num(d.get("tol")))
    px = None
    try:
        from engine import screen as _screen
        img = _screen.grab_region(x, y, x + 1, y + 1)
        if img is not None:
            px = list(img.convert("RGB").getdata())[0]
    except Exception:
        px = None
    if px is None:
        try:
            from PIL import ImageGrab
            px = ImageGrab.grab(bbox=(x, y, x + 1, y + 1)).convert("RGB").getpixel((0, 0))
        except Exception:
            return False
    want = (int(_expr_to_num(rgba[0])), int(_expr_to_num(rgba[1])), int(_expr_to_num(rgba[2])))
    return all(abs(int(a) - int(b)) <= tol for a, b in zip(px, want))


def eval_expr(expr: Any, vars_state: dict[str, Any],
              bot_root: str = "", macro_dir: str | None = None) -> Any:
    """Evaluate an expression tree from the expanded .macro format.

    Nodes: {lit}, {get}, {cmp}, {and}/{or}, {not}, {arith},
    {img_eq}, {img_on_screen}, {color_eq}, {color_diff}, {img_diff},
    {point}, {box}, {res_spec}, {res_scale}.
    Plain values pass through.
    """
    if not isinstance(expr, dict):
        return expr
    if "lit" in expr:
        return expr.get("lit")
    if "get" in expr:
        return vars_state.get(str(expr.get("get") or ""), False)
    if "grab" in expr:
        return _grab_expr_path(expr.get("grab") or {}, vars_state)
    if "screen_color" in expr:
        return _screen_color_expr(expr.get("screen_color") or {}, vars_state)
    if "cmp" in expr:
        c = expr.get("cmp") or {}
        a = eval_expr(c.get("a"), vars_state, bot_root, macro_dir)
        b = eval_expr(c.get("b"), vars_state, bot_root, macro_dir)
        op = str(c.get("op") or "EQ").upper()
        # numeric compare first — bools coerce (True==1), so an img_eq/color
        # watcher flipping a variable reads correctly as `var == 1`
        try:
            na, nb = float(a), float(b)
            if op == "EQ": return na == nb
            if op == "NEQ": return na != nb
            if op == "LT": return na < nb
            if op == "LTE": return na <= nb
            if op == "GT": return na > nb
            if op == "GTE": return na >= nb
            return na >= nb
        except Exception:
            pass
        sa, sb = str(a), str(b)
        if op == "EQ": return sa == sb
        if op == "NEQ": return sa != sb
        return truthy(a)
    if "and" in expr:
        e = expr.get("and") or {}
        return truthy(eval_expr(e.get("a"), vars_state, bot_root, macro_dir)) and \
               truthy(eval_expr(e.get("b"), vars_state, bot_root, macro_dir))
    if "or" in expr:
        e = expr.get("or") or {}
        return truthy(eval_expr(e.get("a"), vars_state, bot_root, macro_dir)) or \
               truthy(eval_expr(e.get("b"), vars_state, bot_root, macro_dir))
    if "not" in expr:
        return not truthy(eval_expr(expr.get("not"), vars_state, bot_root, macro_dir))
    if "arith" in expr:
        e = expr.get("arith") or {}
        a = _expr_to_num(eval_expr(e.get("a"), vars_state, bot_root, macro_dir))
        b = _expr_to_num(eval_expr(e.get("b"), vars_state, bot_root, macro_dir))
        op = str(e.get("op") or "+")
        try:
            if op == "+": return a + b
            if op == "-": return a - b
            if op == "*": return a * b
            if op == "^": return a ** b
            if op == "/": return a / b if b else 0.0
        except Exception:
            return 0.0
        return a + b
    if "img_eq" in expr:
        try:
            return _expr_img_eq(expr.get("img_eq") or {}, vars_state, bot_root, macro_dir)
        except Exception:
            return False
    if "img_on_screen" in expr:
        d = dict(expr.get("img_on_screen") or {})
        d.setdefault("var", "__expr_img")
        d.setdefault("result_mode", "bool")
        try:
            return bool(run_image_check(vars_state, d, bot_root, macro_dir))
        except Exception:
            return False
    if "color_eq" in expr:
        try:
            return _expr_color_eq(expr.get("color_eq") or {}, vars_state)
        except Exception:
            return False
    if "color_diff" in expr:
        try:
            return _expr_color_diff(expr.get("color_diff") or {}, vars_state, bot_root, macro_dir)
        except Exception:
            return -1.0
    if "img_diff" in expr:
        try:
            return _expr_img_diff(expr.get("img_diff") or {}, vars_state, bot_root, macro_dir)
        except Exception:
            return -1.0
    # ── resolution blocks (1:1 with the flow editor's ratio/scale) ──
    if "point" in expr:
        d = expr.get("point") or {}
        return (_coord_val(d.get("x"), vars_state, 0),
                _coord_val(d.get("y"), vars_state, 1))
    if "box" in expr:
        d = expr.get("box") or {}
        return (_coord_val(d.get("x1"), vars_state, 0),
                _coord_val(d.get("y1"), vars_state, 1),
                _coord_val(d.get("x2"), vars_state, 2),
                _coord_val(d.get("y2"), vars_state, 3))
    if "res_spec" in expr:
        d = expr.get("res_spec") or {}
        vals = [_coord_val(d.get(k), vars_state, i) for i, k in enumerate(("rw", "rh", "dw", "dh"))]
        return _macro_res_spec(*vals)
    if "res_scale" in expr:
        try:
            return _expr_res_scale(expr.get("res_scale") or {}, vars_state)
        except Exception:
            return (0, 0)
    return truthy(expr)


def evaluate_condition(vars_state: dict[str, Any], data: dict[str, Any],
                    bot_root: str = "", macro_dir: str | None = None) -> bool:
    # expanded format: {expr: {...}} — typed comparisons, image/color checks
    if isinstance(data, dict) and "expr" in data:
        return truthy(eval_expr(data.get("expr"), vars_state, bot_root, macro_dir))
    mode = str(data.get("mode") or "boolean").strip().lower()
    name = str(data.get("name") or "").strip()
    cur = vars_state.get(name, False)
    if mode == "number":
        try:
            left = float(cur or 0)
        except Exception:
            left = 0.0
        try:
            right = float(data.get("value", 0) or 0)
        except Exception:
            right = 0.0
        op = str(data.get("op") or ">=").strip()
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        return left >= right
    expected = truthy(data.get("value", True))
    return truthy(cur) is expected


def branch_active(stack: list[dict[str, Any]]) -> bool:
    return all(bool(item.get("active")) for item in stack)


def handle_if(stack: list[dict[str, Any]], vars_state: dict[str, Any], data: dict[str, Any],
               bot_root: str = "", macro_dir: str | None = None) -> None:
    parent_active = branch_active(stack)
    active = bool(parent_active and evaluate_condition(vars_state, data, bot_root, macro_dir))
    stack.append({"parent": parent_active, "active": active, "branch_taken": active})


def handle_else_if(stack: list[dict[str, Any]], vars_state: dict[str, Any], data: dict[str, Any],
                   bot_root: str = "", macro_dir: str | None = None) -> None:
    if not stack:
        return
    top = stack[-1]
    if not top.get("parent") or top.get("branch_taken"):
        top["active"] = False
        return
    active = bool(evaluate_condition(vars_state, data, bot_root, macro_dir))
    top["active"] = active
    if active:
        top["branch_taken"] = True


def handle_else(stack: list[dict[str, Any]]) -> None:
    """Plain ELSE branch — runs when no earlier branch of this IF ran."""
    if not stack:
        return
    top = stack[-1]
    if not top.get("parent") or top.get("branch_taken"):
        top["active"] = False
        return
    top["active"] = True
    top["branch_taken"] = True


def handle_end_if(stack: list[dict[str, Any]]) -> None:
    if stack:
        stack.pop()


# ── WHILE / UNTIL loops ────────────────────────────────────────────────
# WHILE:<cond> / UNTIL:<cond> ... END_WHILE / END_UNTIL. The loop entry rides
# the same if_stack as IF branches (so nesting + parent-branch gating work
# identically); handle_end_while re-evaluates the condition and either returns
# the body start pc (loop again) or None (exit + pop).
WHILE_MAX_ITERATIONS = 100_000  # safety net against a never-false condition


def handle_while(stack: list[dict[str, Any]], vars_state: dict[str, Any], data: dict[str, Any],
                 bot_root: str = "", macro_dir: str | None = None,
                 invert: bool = False) -> None:
    parent_active = branch_active(stack)
    cond = evaluate_condition(vars_state, data, bot_root, macro_dir)
    active = bool(parent_active and (cond != invert))
    stack.append({"parent": parent_active, "active": active, "branch_taken": active,
                  "payload": data, "invert": invert, "iters": 0})


def handle_end_while(stack: list[dict[str, Any]], while_stack: list[int],
                     vars_state: dict[str, Any], bot_root: str = "",
                     macro_dir: str | None = None) -> int | None:
    """Close one WHILE/UNTIL loop. Returns the body start pc to loop again,
    or None when the loop exits (or was never entered)."""
    if not stack:
        return None
    top = stack[-1]
    if not top.get("active"):
        stack.pop()          # condition was false at entry — body was skipped
        return None
    top["iters"] = int(top.get("iters") or 0) + 1
    cond = evaluate_condition(vars_state, top.get("payload") or {}, bot_root, macro_dir)
    keep_looping = bool(cond) != bool(top.get("invert"))
    if keep_looping and top["iters"] < WHILE_MAX_ITERATIONS:
        return while_stack[-1] if while_stack else None
    if keep_looping:
        log.warning("WHILE/UNTIL loop hit the %s-iteration safety cap — exiting",
                    WHILE_MAX_ITERATIONS)
    stack.pop()
    if while_stack:
        while_stack.pop()
    return None


def _resolve_image_path(path: str, bot_root: str, macro_dir: str | None = None) -> str:
    path = str(path or "").strip()
    if not path:
        return ""
    if os.path.isabs(path):
        return path

    clean = path.replace("\\", "/").lstrip("/")
    variants = [clean]
    for prefix in ("macros/images/", "images/"):
        if clean.lower().startswith(prefix):
            variants.append(clean[len(prefix):])
    variants = [v for i, v in enumerate(variants) if v and v not in variants[:i]]

    candidates = []
    # macro file's own folder (workspace resources) first — a macro stored in
    # <workspace>/resources/macros/ with images in <workspace>/resources/images
    if macro_dir:
        for variant in variants:
            candidates.append(os.path.join(macro_dir, variant))
        for variant in variants:
            candidates.append(os.path.normpath(os.path.join(macro_dir, "..", variant)))
    for variant in variants:
        candidates.append(os.path.join(bot_root, "macros", "images", variant))
    for variant in variants:
        candidates.append(os.path.join(bot_root, "data", "macro_images", variant))
    for variant in variants:
        candidates.append(os.path.join(bot_root, variant))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    basename = os.path.basename(clean)
    if basename and not re.match(r"^\d{3,5}x\d{3,5}_", basename, flags=re.I):
        for candidate in candidates:
            folder = os.path.dirname(candidate)
            if not os.path.isdir(folder):
                continue
            try:
                matches = sorted(
                    name for name in os.listdir(folder)
                    if re.match(rf"^\d{{3,5}}x\d{{3,5}}_{re.escape(basename)}$", name, flags=re.I)
                )
            except Exception:
                matches = []
            if matches:
                return os.path.join(folder, matches[0])
    return candidates[0] if candidates else path


_MSS_TLS = threading.local()   # one mss per THREAD (mss is not thread-safe)


def _grab_region(region: tuple[int, int, int, int]) -> np.ndarray | None:
    x1, y1, x2, y2 = region
    if x2 <= x1 or y2 <= y1:
        return None
    # one mss instance per THREAD — mss.mss() per grab costs 10-30ms of
    # Win32 setup EVERY screen read (image conditions in tight WHILE/UNTIL
    # loops grab once per pass; background watchers get their own handle
    # so main-thread + watcher grabs never share an mss instance)
    sct = getattr(_MSS_TLS, "handle", None)
    if sct is None:
        sct = _MSS_TLS.handle = mss.mss()
    raw = sct.grab({"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1})
    img = np.array(raw)
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def _screen_size() -> tuple[int, int]:
    """Primary-monitor pixels — same source as HUD scaling (not the virtual desktop)."""
    try:
        import config as _cfg
        w = int(getattr(_cfg, "RUNTIME_WIDTH", 0) or 0)
        h = int(getattr(_cfg, "RUNTIME_HEIGHT", 0) or 0)
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    try:
        import ctypes
        w = int(ctypes.windll.user32.GetSystemMetrics(0))
        h = int(ctypes.windll.user32.GetSystemMetrics(1))
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    try:
        with mss.mss() as sct:
            mons = sct.monitors
            mon = mons[1] if len(mons) > 1 else mons[0]
            return int(mon["width"]), int(mon["height"])
    except Exception:
        return 1920, 1080


def _base_size_from_data(data: dict[str, Any]) -> tuple[int, int]:
    try:
        base_w = int(round(float(data.get("base_w", 1920) or 1920)))
        base_h = int(round(float(data.get("base_h", 1080) or 1080)))
    except Exception:
        base_w, base_h = 1920, 1080
    return max(1, base_w), max(1, base_h)


def _scale_region_to_screen(region: tuple[int, int, int, int], data: dict[str, Any]) -> tuple[int, int, int, int]:
    base_w, base_h = _base_size_from_data(data)
    cur_w, cur_h = _screen_size()
    if cur_w == base_w and cur_h == base_h:
        return region
    sx = cur_w / float(base_w)
    sy = cur_h / float(base_h)
    x1, y1, x2, y2 = region
    scaled = (
        int(round(x1 * sx)),
        int(round(y1 * sy)),
        int(round(x2 * sx)),
        int(round(y2 * sy)),
    )
    sx1, sy1, sx2, sy2 = scaled
    sx1 = max(0, min(max(0, cur_w - 1), sx1))
    sy1 = max(0, min(max(0, cur_h - 1), sy1))
    sx2 = max(1, min(cur_w, sx2))
    sy2 = max(1, min(cur_h, sy2))
    if sx2 <= sx1:
        sx2 = min(cur_w, sx1 + 1)
    if sy2 <= sy1:
        sy2 = min(cur_h, sy1 + 1)
    return sx1, sy1, sx2, sy2


def _region_from_data(data: dict[str, Any], prefix: str = "") -> tuple[int, int, int, int] | None:
    keys = [f"{prefix}x1", f"{prefix}y1", f"{prefix}x2", f"{prefix}y2"]
    try:
        x1, y1, x2, y2 = [int(round(float(data.get(k)))) for k in keys]
    except Exception:
        return None
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    if x2 <= x1 or y2 <= y1:
        return None
    return _scale_region_to_screen((x1, y1, x2, y2), data)


def effective_region(data: dict[str, Any]) -> tuple[int, int, int, int] | None:
    fixed = truthy(data.get("fixed", True))
    region = _region_from_data(data, "" if fixed else "search_")
    if region is None:
        region = _region_from_data(data, "")
    return region


def _image_base_size_from_filename(path: str) -> tuple[int, int] | None:
    match = re.match(r"^(\d{3,5})x(\d{3,5})_", os.path.basename(path), flags=re.I)
    if not match:
        return None
    try:
        base_w = int(match.group(1))
        base_h = int(match.group(2))
    except Exception:
        return None
    if base_w <= 0 or base_h <= 0:
        return None
    return base_w, base_h


def _runtime_image_scale_xy(data: dict[str, Any], template_path: str | None = None) -> tuple[float, float]:
    image_base = _image_base_size_from_filename(template_path or "") if template_path else None
    if image_base is not None:
        base_w, base_h = image_base
    elif data:
        base_w, base_h = _base_size_from_data(data)
    else:
        base_w, base_h = 1920, 1080
    cur_w, cur_h = _screen_size()
    sx = max(0.1, cur_w / float(max(1, base_w)))
    sy = max(0.1, cur_h / float(max(1, base_h)))
    return sx, sy


def _runtime_image_scale(data: dict[str, Any], template_path: str | None = None) -> float:
    sx, sy = _runtime_image_scale_xy(data, template_path)
    # Prefer uniform scale from the match-to-screen axes. Independent X/Y
    # stretch is applied when searching (see match loop) via both factors.
    return max(0.1, min(sx, sy))


def _load_template(path: str) -> tuple[np.ndarray | None, np.ndarray | None]:
    raw = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if raw is None or raw.size == 0:
        return None, None
    if len(raw.shape) == 3 and raw.shape[2] == 4:
        alpha = raw[:, :, 3]
        mask = (alpha > 8).astype(np.uint8) * 255
        bgr = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        if int(np.count_nonzero(mask)) < 4:
            mask = None
        return bgr, mask
    if len(raw.shape) == 2:
        return cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR), None
    return raw, None


def _resize_mask(mask: np.ndarray | None, size: tuple[int, int]) -> np.ndarray | None:
    if mask is None:
        return None
    return cv2.resize(mask, size, interpolation=cv2.INTER_NEAREST)


def _safe_match_score(live: np.ndarray, template: np.ndarray, mask: np.ndarray | None = None) -> float:
    if live.shape[:2] != template.shape[:2]:
        live = cv2.resize(live, (template.shape[1], template.shape[0]), interpolation=cv2.INTER_AREA)
    diff = cv2.absdiff(live.astype(np.float32), template.astype(np.float32))
    if mask is not None:
        visible = mask > 0
        if int(np.count_nonzero(visible)) < 4:
            return 0.0
        diff_score = 1.0 - float(diff[visible].mean()) / 255.0
    else:
        diff_score = 1.0 - float(diff.mean()) / 255.0
    scores = [diff_score]
    pairs = (
        (live, template, mask),
        (cv2.cvtColor(live, cv2.COLOR_BGR2GRAY), cv2.cvtColor(template, cv2.COLOR_BGR2GRAY), mask),
    )
    for left, right, pair_mask in pairs:
        try:
            if pair_mask is not None:
                result = cv2.matchTemplate(left, right, cv2.TM_CCORR_NORMED, mask=pair_mask)
            else:
                result = cv2.matchTemplate(left, right, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if np.isfinite(max_val):
                scores.append(float(max_val))
        except Exception:
            pass
    return max(0.0, min(1.0, max(scores)))


def _edge_image(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.Canny(gray, 45, 135)


def _edge_overlap_score(live: np.ndarray, template: np.ndarray) -> float:
    if live.shape[:2] != template.shape[:2]:
        live = cv2.resize(live, (template.shape[1], template.shape[0]), interpolation=cv2.INTER_AREA)
    live_edges = _edge_image(live)
    tpl_edges = _edge_image(template)
    live_count = int(np.count_nonzero(live_edges))
    tpl_count = int(np.count_nonzero(tpl_edges))
    if live_count < 20 or tpl_count < 20:
        return 0.0
    kernel = np.ones((3, 3), np.uint8)
    live_dilated = cv2.dilate(live_edges, kernel, iterations=1)
    tpl_dilated = cv2.dilate(tpl_edges, kernel, iterations=1)
    tpl_hit = np.count_nonzero((tpl_edges > 0) & (live_dilated > 0)) / float(tpl_count)
    live_hit = np.count_nonzero((live_edges > 0) & (tpl_dilated > 0)) / float(live_count)
    return max(0.0, min(1.0, (tpl_hit * live_hit) ** 0.5))


def _edge_search_score(live: np.ndarray, template: np.ndarray) -> float:
    live_edges = _edge_image(live)
    tpl_edges = _edge_image(template)
    if np.count_nonzero(live_edges) < 20 or np.count_nonzero(tpl_edges) < 20:
        return 0.0
    if tpl_edges.shape[0] > live_edges.shape[0] or tpl_edges.shape[1] > live_edges.shape[1]:
        return 0.0
    result = cv2.matchTemplate(live_edges.astype(np.float32), tpl_edges.astype(np.float32), cv2.TM_CCORR_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return float(max_val) if np.isfinite(max_val) else 0.0


def image_match_result(data: dict[str, Any], bot_root: str, macro_dir: str | None = None) -> dict[str, Any]:
    template_path = _resolve_image_path(str(data.get("path") or ""), bot_root, macro_dir)
    if not template_path:
        return {"score": 0.0, "matched": False, "x": None, "y": None, "box": None, "path": ""}
    template, mask = _load_template(template_path)
    if template is None or template.size == 0:
        return {"score": 0.0, "matched": False, "x": None, "y": None, "box": None, "path": template_path}
    fixed = truthy(data.get("fixed", True))
    region = effective_region(data)
    live = _grab_region(region) if region is not None else None
    if live is None or live.size == 0:
        return {"score": 0.0, "matched": False, "x": None, "y": None, "box": None, "path": template_path}
    threshold = max(0.0, min(100.0, float(data.get("threshold", 85) or 85))) / 100.0

    if fixed:
        score = _safe_match_score(live, template, mask)
        if mask is None:
            score = max(score, _edge_overlap_score(live, template))
        x1, y1, x2, y2 = region
        return {
            "score": max(0.0, min(1.0, score)),
            "matched": score >= threshold,
            "x": int((x1 + x2) // 2),
            "y": int((y1 + y2) // 2),
            "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "path": template_path,
        }

    best = 0.0
    best_box = None
    sx, sy = _runtime_image_scale_xy(data, template_path)
    base_scale = min(sx, sy)
    scale_pairs = [(base_scale, base_scale), (sx, sy), (1.0, 1.0)]
    for f in (0.75, 0.85, 0.92, 1.08, 1.15, 1.25, 0.85, 0.90, 0.95, 1.05, 1.10, 1.15):
        scale_pairs.append((base_scale * f, base_scale * f))
        scale_pairs.append((sx * f, sy * f))
    seen_hw = set()
    for scx, scy in scale_pairs:
        tw = max(2, int(round(template.shape[1] * scx)))
        th = max(2, int(round(template.shape[0] * scy)))
        if (tw, th) in seen_hw:
            continue
        seen_hw.add((tw, th))
        if abs(scx - 1.0) < 1e-6 and abs(scy - 1.0) < 1e-6:
            tpl = template
            tpl_mask = mask
        else:
            tpl = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA)
            tpl_mask = _resize_mask(mask, (tw, th))
        if tpl.shape[0] > live.shape[0] or tpl.shape[1] > live.shape[1]:
            continue
        for left, right in (
            (live, tpl),
            (cv2.cvtColor(live, cv2.COLOR_BGR2GRAY), cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)),
        ):
            if tpl_mask is not None:
                result = cv2.matchTemplate(left, right, cv2.TM_CCORR_NORMED, mask=tpl_mask)
            else:
                result = cv2.matchTemplate(left, right, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if np.isfinite(max_val):
                score = float(max_val)
                if score > best:
                    _, _, _, max_loc = cv2.minMaxLoc(result)
                    best = score
                    lx, ly = int(max_loc[0]), int(max_loc[1])
                    best_box = (region[0] + lx, region[1] + ly, region[0] + lx + tpl.shape[1], region[1] + ly + tpl.shape[0])
        if tpl_mask is None:
            edge_score = _edge_search_score(live, tpl)
            if edge_score > best:
                best = edge_score
    score = max(0.0, min(1.0, best))
    if best_box is None:
        box_obj = None
        cx = cy = None
    else:
        x1, y1, x2, y2 = best_box
        box_obj = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        cx, cy = int((x1 + x2) // 2), int((y1 + y2) // 2)
    return {"score": score, "matched": score >= threshold, "x": cx, "y": cy, "box": box_obj, "path": template_path}


def image_match_score(data: dict[str, Any], bot_root: str, macro_dir: str | None = None) -> float:
    return float(image_match_result(data, bot_root, macro_dir).get("score", 0.0) or 0.0)


def run_image_check(vars_state: dict[str, Any], data: dict[str, Any], bot_root: str, macro_dir: str | None = None) -> bool:
    name = str(data.get("var") or "").strip()
    data = dict(data)
    # scaled search regions ({res_scale} exprs) -> plain ints for matching
    data = resolve_region_exprs(data, vars_state)
    path = data.get("path")
    if isinstance(path, dict):
        # image variable: {get: name} → resolve to the stored path string
        data["path"] = eval_expr(path, vars_state, bot_root, macro_dir)
    result = image_match_result(data, bot_root, macro_dir)
    matched = bool(result.get("matched"))
    mode = str(data.get("result_mode") or "bool").strip().lower()
    if mode not in {"bool", "coords", "both"}:
        mode = "bool"
    if name and mode in {"bool", "both"}:
        vars_state[name] = matched
    if mode in {"coords", "both"}:
        x_name = str(data.get("x_var") or (f"{name}_x" if name else "image_x")).strip()
        y_name = str(data.get("y_var") or (f"{name}_y" if name else "image_y")).strip()
        if x_name:
            vars_state[x_name] = int(result["x"]) if matched and result.get("x") is not None else -1
        if y_name:
            vars_state[y_name] = int(result["y"]) if matched and result.get("y") is not None else -1
    return matched


def _grab_save_target(target: str, bot_root: str, macro_dir: str | None = None) -> str:
    """Resolve a GRAB_IMAGE save path for WRITING.

    Mirrors _resolve_image_path's read order (macro folder first) so a
    later IMAGE check / img diff finds the file where it was written.
    """
    target = str(target or "").strip().replace("\\", "/")
    if not target:
        return ""
    if os.path.isabs(target):
        return target
    if not target.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
        target += ".png"
    if macro_dir:
        return os.path.normpath(os.path.join(macro_dir, target))
    return os.path.join(bot_root, "data", "macro_images", target)


def _grab_expr_path(d: dict[str, Any], vars_state: dict[str, Any]) -> str:
    """Capture a {grab: …} expression node and return its buffer path.

    "get image from screen at [point] size [box]": the region is grabbed
    from the screen live and buffered in a temp PNG (logic only — never
    the user's macro folders). The operand/variable receives the buffer
    path. Empty string on failure.

    Point+size form ({x, y, w, h}) — the point may be plain numbers (base
    resolution, scaled to the screen like image-check regions) or a
    {res_scale} point (already runtime pixels). Size may carry {get}
    expressions. The legacy region form ({search_…}, 2.1.208) still plays.
    """
    d = dict(d)
    if d.get("x") is not None or d.get("w") is not None:
        x = _coord_val(d.get("x") or 0, vars_state, 0)
        y = _coord_val(d.get("y") or 0, vars_state, 1)
        w = int(round(float(eval_expr(d.get("w") or 0, vars_state) or 0)))
        h = int(round(float(eval_expr(d.get("h") or 0, vars_state) or 0)))
        if w <= 0 or h <= 0:
            return ""
        region = (x, y, x + w, y + h)
        if not isinstance(d.get("x"), dict):
            # plain base-resolution coords → current screen (1:1 with image checks)
            region = _scale_region_to_screen(region, d)
    else:
        # legacy region form (2.1.208 payloads)
        d = resolve_region_exprs(d, vars_state)
        region = effective_region(d)
        if region is None:
            region = (0, 0) + _screen_size()
    img = _grab_region(region)
    if img is None:
        return ""
    target = _grab_temp_target(d.get("var") or "shot")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        cv2.imwrite(target, img)
        return target
    except Exception:
        return ""


def _screen_color_expr(d: dict[str, Any], vars_state: dict[str, Any]) -> str:
    """{screen_color: {x, y}} — read the pixel at the point as '#RRGGBB'.

    "get color from screen at [point]": 1:1 with the old color-at-point
    condition's read — plain numbers are runtime pixels, a {res_scale}
    point evaluates live. Empty string on failure.
    """
    x = _coord_val(d.get("x") or 0, vars_state, 0)
    y = _coord_val(d.get("y") or 0, vars_state, 1)
    try:
        img = _grab_region((x, y, x + 1, y + 1))
        if img is None or img.size == 0:
            return ""
        b, g, r = int(img[0][0][0]), int(img[0][0][1]), int(img[0][0][2])
        return "#%02X%02X%02X" % (r, g, b)
    except Exception:
        return ""


def _grab_temp_target(name: str) -> str:
    """Buffer target for a logic-only capture: mfm_grab_*.png in TEMP.

    Same policy as the flow engine's _pcr_screenshot_box fallback — temp
    is disposable scratch space, never the user's macro folders. Stale
    grabs older than a day are purged best-effort on every capture.
    """
    folder = tempfile.gettempdir()
    try:
        now = time.time()
        for fn in os.listdir(folder):
            if fn.startswith("mfm_grab_") and fn.endswith(".png"):
                fp = os.path.join(folder, fn)
                if now - os.path.getmtime(fp) > 86400:
                    os.remove(fp)
    except Exception:
        pass
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", str(name or "shot")).strip("_")[:40] or "shot"
    return os.path.join(folder, f"mfm_grab_{safe}_{int(time.time() * 1000)}.png")


def run_grab_image(vars_state: dict[str, Any], data: dict[str, Any],
                   bot_root: str, macro_dir: str | None = None) -> bool:
    """GRAB_IMAGE — get image of a box region, for logic only.

    The region defined by the block's box is grabbed from the screen and
    buffered in a temp PNG (never in the user's macro folders); the image
    variable receives the buffer path, so IMAGE checks, img diff and image
    compare blocks can consume it right after. An explicit "path" key in
    a hand-written payload still wins (write where you say), but the
    block itself never emits one.
    """
    data = dict(data)
    # scaled grab regions ({res_scale} exprs) -> plain ints
    data = resolve_region_exprs(data, vars_state)
    region = effective_region(data)
    if region is None:
        region = (0, 0) + _screen_size()
    img = _grab_region(region)
    if img is None:
        return False
    path = data.get("path")
    if isinstance(path, dict):
        path = eval_expr(path, vars_state, bot_root, macro_dir)
    target = _grab_save_target(str(path or ""), bot_root, macro_dir)
    if not target:
        target = _grab_temp_target(data.get("var"))
    try:
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        if not cv2.imwrite(target, img):
            return False
    except Exception:
        return False
    name = str(data.get("var") or "").strip()
    if name:
        vars_state[name] = target
    return True


# ── Background watchers (WATCH / STOP WATCH) ─────────────────────────────
#
# WATCH <var> WHEN (<condition>) EVERY <ms>
#
# Runs the condition on a BACKGROUND thread at the given cadence and keeps
# the variable live: 1 while the condition holds, 0 while it doesn't. The
# main macro never pays screen-grab / image-diff cost inside its own hot
# loops — UNTIL/WHILE/IF just read the variable (a dict lookup, ~free).
#
# Screen grabs happen on the watcher's own thread with its own mss handle
# (thread-local since 2.1.221), so main-thread grabs and watcher grabs
# never share state. The decoded-image cache is shared — the template PNG
# is decoded once no matter which thread asks first.
#
# A watcher lives until:
#   - STOP WATCH <var> runs in the macro, or
#   - the playback's stop_event fires (Stop button / macro end), or
#   - a new WATCH on the same var replaces it (re-arm).
# All watchers of a playback are joined on exit, so no thread ever
# outlives its macro.

class BackgroundWatcher(threading.Thread):
    """One background condition watcher. Writes 1/0 into vars_state[var]."""

    def __init__(self, var: str, cond: Any, every_ms: int,
                 vars_state: dict[str, Any],
                 stop_event: threading.Event,
                 bot_root: str, macro_dir: str | None = None):
        super().__init__(daemon=True, name=f"mfm-watch-{var}")
        self.var = var
        self.cond = cond
        self.every_ms = max(1, int(every_ms or 100))
        self.vars_state = vars_state
        self.stop_event = stop_event          # playback-wide (macro end/stop)
        self.done_event = threading.Event()   # this watcher's own off switch
        self.bot_root = bot_root
        self.macro_dir = macro_dir

    def stop(self, timeout: float = 2.0) -> None:
        self.done_event.set()
        self.join(timeout=timeout)

    def run(self) -> None:
        import time as _time
        while not self.done_event.is_set() and not self.stop_event.is_set():
            try:
                val = truthy(eval_expr(self.cond, self.vars_state,
                                       self.bot_root, self.macro_dir))
            except Exception:
                val = False
            try:
                self.vars_state[self.var] = 1 if val else 0
            except Exception:
                pass
            # slice the wait so STOP WATCH / macro end is near-instant
            waited = 0.0
            while waited < self.every_ms / 1000.0:
                if self.done_event.is_set() or self.stop_event.is_set():
                    return
                _time.sleep(0.005)
                waited += 0.005


def start_watcher(data: dict[str, Any], vars_state: dict[str, Any],
                  stop_event: threading.Event,
                  registry: dict[str, BackgroundWatcher],
                  bot_root: str = "", macro_dir: str | None = None) -> None:
    """WATCH: payload {var, expr, every_ms} — arm (or re-arm) a watcher."""
    name = str(data.get("var") or "").strip()
    if not name:
        return
    # auto-declare the flag so IF/UNTIL see 0 immediately, not "undefined"
    if name not in vars_state:
        vars_state[name] = 0
    old = registry.get(name)
    if old is not None:
        old.done_event.set()          # re-arm: retire the previous thread
    try:
        every_ms = max(1, int(float(eval_expr(data.get("every_ms"), vars_state,
                                              bot_root, macro_dir) or 100)))
    except Exception:
        every_ms = 100
    w = BackgroundWatcher(name, data.get("expr"), every_ms,
                          vars_state, stop_event, bot_root, macro_dir)
    registry[name] = w
    w.start()


def stop_watcher(name: str,
                 registry: dict[str, BackgroundWatcher]) -> None:
    """STOP_WATCH: <var> — retire one watcher."""
    w = registry.pop(str(name or "").strip(), None)
    if w is not None:
        w.stop()


def stop_all_watchers(registry: dict[str, BackgroundWatcher]) -> None:
    """Playback exit hook — retire every watcher this run armed."""
    for name in list(registry.keys()):
        stop_watcher(name, registry)


# ── Background loop arms (UNTIL/WHILE ... BACKGROUND { ... }) ────────────
#
# A WHILE/UNTIL with a background arm runs the arm's steps on a side
# thread, REPEATEDLY, for as long as the loop lives:
#
#   UNTIL (ready == 1) {
#     ... hot main body — clicks cost ~2ms each ...
#   } BACKGROUND {
#     SET ready = (img_diff("images/tpl.png", grab_at(0, 0, 100, 40)) == 0)
#     DELAY 100
#   }
#
# The arm typically watches the screen (IMAGE / img_diff condition) and
# keeps a variable updated; the loop condition reads that variable — a
# dict lookup — so the hot body never pays grab/decode cost. The thread
# stops the moment the loop exits, the macro ends, or Stop is pressed.
#
# The arm interpreter supports the side-effect-free step subset:
# VARIABLE / SET_VARIABLE / IMAGE / GRAB_IMAGE / DELAY / PRINT /
# IF-ELSE / REPEAT / WHILE / UNTIL. Mouse/keyboard ops are skipped
# (warned once) — they make no sense off the input thread.

def _bg_sliced_sleep(seconds: float, stop_events: tuple) -> None:
    """Sleep in 5ms slices so STOP / loop exit is near-instant."""
    waited = 0.0
    while waited < seconds:
        for ev in stop_events:
            if ev is not None and ev.is_set():
                return
        time.sleep(min(0.005, max(0.0, seconds - waited)))
        waited += 0.005


class BackgroundLoop(threading.Thread):
    """Runs a step list on repeat, on its own thread, until stopped."""

    def __init__(self, lines: list[str], vars_state: dict[str, Any],
                 stop_event: threading.Event,
                 bot_root: str = "", macro_dir: str | None = None,
                 print_cb=None, min_pass_s: float = 0.005):
        super().__init__(daemon=True, name="mfm-bg-loop")
        self.lines = list(lines or [])
        self.vars_state = vars_state
        self.stop_event = stop_event          # playback-wide stop
        self.done_event = threading.Event()    # this loop's own off switch
        self.bot_root = bot_root
        self.macro_dir = macro_dir
        self.print_cb = print_cb
        self.min_pass_s = max(0.001, float(min_pass_s))
        self._warned: set[str] = set()

    def stop(self, timeout: float = 2.0) -> None:
        self.done_event.set()
        if self.is_alive():
            self.join(timeout=timeout)

    def _stopped(self) -> bool:
        return self.done_event.is_set() or self.stop_event.is_set()

    def _warn_skip(self, raw: str) -> None:
        head = raw.split(":", 1)[0]
        if head not in self._warned:
            self._warned.add(head)
            try:
                logging.getLogger(__name__).warning(
                    "BACKGROUND arm: %s is not supported on a background "
                    "thread — skipped (supported: variables, IMAGE, "
                    "GRAB_IMAGE, DELAY, PRINT, IF/ELSE, REPEAT, WHILE/UNTIL)",
                    head)
            except Exception:
                pass

    def run(self) -> None:
        while not self._stopped():
            t0 = time.perf_counter()
            try:
                self._pass()
            except Exception:
                logging.getLogger(__name__).exception("BACKGROUND arm error")
            # hot-loop floor: an arm with no DELAY of its own must not
            # spin the CPU at full speed — pace passes to >= 5ms
            rest = self.min_pass_s - (time.perf_counter() - t0)
            if rest > 0:
                _bg_sliced_sleep(rest, (self.done_event, self.stop_event))

    def _pass(self) -> None:
        vars_state = self.vars_state
        if_stack: list[dict[str, Any]] = []
        while_stack: list[int] = []
        repeat_stack: list[tuple[int, int]] = []
        pc = 0
        lines = self.lines
        n = len(lines)
        while pc < n:
            if self._stopped():
                return
            raw = lines[pc]
            pc += 1
            if not raw or raw.startswith("#"):
                continue
            if raw == "LOCK:" or raw.startswith("LOCK_END:"):
                continue
            if raw == "BG_BEGIN:" or raw.startswith("BG_END"):
                continue  # nested arms are not a thing — plain markers
            if raw.startswith("VARIABLE:"):
                if branch_active(if_stack):
                    define_variable(vars_state, parse_payload(raw, "VARIABLE"))
                continue
            if raw.startswith("SET_VARIABLE:"):
                if branch_active(if_stack):
                    set_variable(vars_state, parse_payload(raw, "SET_VARIABLE"),
                                 self.bot_root, self.macro_dir)
                continue
            if raw.startswith("IMAGE:"):
                if branch_active(if_stack):
                    run_image_check(vars_state, parse_payload(raw, "IMAGE"),
                                    self.bot_root, self.macro_dir)
                continue
            if raw.startswith("GRAB_IMAGE:"):
                if branch_active(if_stack):
                    run_grab_image(vars_state, parse_payload(raw, "GRAB_IMAGE"),
                                   self.bot_root, self.macro_dir)
                continue
            if raw.startswith("IF:"):
                handle_if(if_stack, vars_state, parse_payload(raw, "IF"),
                          self.bot_root, self.macro_dir)
                continue
            if raw.startswith("ELSE_IF:"):
                handle_else_if(if_stack, vars_state, parse_payload(raw, "ELSE_IF"),
                               self.bot_root, self.macro_dir)
                continue
            if raw == "ELSE" or raw.startswith("ELSE:"):
                handle_else(if_stack)
                continue
            if raw == "END_IF" or raw.startswith("END_IF:"):
                handle_end_if(if_stack)
                continue
            if raw.startswith("WHILE:"):
                handle_while(if_stack, vars_state, parse_payload(raw, "WHILE"),
                             self.bot_root, self.macro_dir)
                if if_stack[-1]["active"]:
                    while_stack.append(pc)
                continue
            if raw.startswith("UNTIL:"):
                handle_while(if_stack, vars_state, parse_payload(raw, "UNTIL"),
                             self.bot_root, self.macro_dir, invert=True)
                if if_stack[-1]["active"]:
                    while_stack.append(pc)
                continue
            if raw == "END_WHILE" or raw.startswith("END_WHILE:") or raw == "END_UNTIL" or raw.startswith("END_UNTIL:"):
                jump = handle_end_while(if_stack, while_stack, vars_state,
                                        self.bot_root, self.macro_dir)
                if jump is not None:
                    pc = jump
                continue
            if raw.startswith("REPEAT:"):
                try:
                    repeat_stack.append((pc, max(1, int(round(
                        eval_expr(_macro_number_expr(raw[7:]), vars_state,
                                  self.bot_root, self.macro_dir) or 1)))))
                except Exception:
                    repeat_stack.append((pc, 1))
                continue
            if raw == "ENDREPEAT":
                if repeat_stack:
                    start, rem = repeat_stack[-1]
                    rem -= 1
                    if rem > 0:
                        repeat_stack[-1] = (start, rem)
                        pc = start
                    else:
                        repeat_stack.pop()
                continue
            if raw.startswith("DELAY:"):
                try:
                    ms = float(eval_expr(_macro_number_expr(raw[6:]), vars_state,
                                         self.bot_root, self.macro_dir) or 0)
                except Exception:
                    ms = 0.0
                if ms > 0:
                    _bg_sliced_sleep(ms / 1000.0,
                                     (self.done_event, self.stop_event))
                continue
            if raw == "PRINT" or raw.startswith("PRINT:"):
                if branch_active(if_stack) and self.print_cb is not None:
                    try:
                        self.print_cb(raw[6:] if raw.startswith("PRINT:") else "",
                                      vars_state)
                    except Exception:
                        pass
                continue
            # anything else (mouse/keyboard/GOTO/PLAY_MACRO/unknown) —
            # not supported off the input thread; skip + warn once
            if raw.startswith(("MOUSE_", "KEY_", "SMOOTH_MOVE:", "LOOK:",
                              "GOTO:", "PLAY_MACRO:", "LABEL:")):
                self._warn_skip(raw)
                continue
            self._warn_skip(raw)


def _macro_number_expr(text: str) -> Any:
    """A bare DELAY/REPEAT payload into an eval_expr node."""
    t = str(text or "").strip()
    if not t:
        return {"lit": 0}
    try:
        return {"lit": int(float(t))}
    except ValueError:
        pass
    try:
        return expr_from_str(t)
    except Exception:
        return {"lit": 0}


def start_background_loop(lines: list[str], vars_state: dict[str, Any],
                          stop_event: threading.Event,
                          bot_root: str = "", macro_dir: str | None = None,
                          print_cb=None) -> BackgroundLoop:
    loop = BackgroundLoop(lines, vars_state, stop_event,
                          bot_root=bot_root, macro_dir=macro_dir,
                          print_cb=print_cb)
    loop.start()
    return loop


def scan_loop_background(lines: list[str], pc: int) -> list[str] | None:
    """From a WHILE/UNTIL line already consumed (body starts at pc), find
    the loop's END marker (nesting-aware) and return the BACKGROUND arm's
    step lines if one follows it, else None. Arm lines come AFTER the
    END marker in v1 order:
        WHILE: / body... / END_WHILE: / BG_BEGIN: / arm... / BG_END:
    """
    n = len(lines)
    i = pc
    depth = 0
    end_idx = None
    while i < n:
        raw = lines[i]
        if raw.startswith("WHILE:") or raw.startswith("UNTIL:"):
            depth += 1
        elif raw == "END_WHILE" or raw.startswith("END_WHILE:") or \
                raw == "END_UNTIL" or raw.startswith("END_UNTIL:"):
            if depth <= 0:
                end_idx = i
                break
            depth -= 1
        i += 1
    if end_idx is None or end_idx + 1 >= n or lines[end_idx + 1] != "BG_BEGIN:":
        return None
    j = end_idx + 2
    arm: list[str] = []
    while j < n and lines[j] != "BG_END:" and not lines[j].startswith("BG_END:"):
        arm.append(lines[j])
        j += 1
    return arm
