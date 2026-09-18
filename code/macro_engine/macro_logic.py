import json
import os
import re
from typing import Any

import cv2
import mss
import numpy as np


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
    else:
        try:
            vars_state[name] = float(data.get("value", 0) or 0)
        except Exception:
            vars_state[name] = 0.0


def set_variable(vars_state: dict[str, Any], data: dict[str, Any]) -> None:
    name = str(data.get("name") or "").strip()
    if not name:
        return
    op = str(data.get("op") or "set").strip().lower()
    raw_value = data.get("value", 0)
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


def evaluate_condition(vars_state: dict[str, Any], data: dict[str, Any]) -> bool:
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


def handle_if(stack: list[dict[str, Any]], vars_state: dict[str, Any], data: dict[str, Any]) -> None:
    parent_active = branch_active(stack)
    active = bool(parent_active and evaluate_condition(vars_state, data))
    stack.append({"parent": parent_active, "active": active, "branch_taken": active})


def handle_else_if(stack: list[dict[str, Any]], vars_state: dict[str, Any], data: dict[str, Any]) -> None:
    if not stack:
        return
    top = stack[-1]
    if not top.get("parent") or top.get("branch_taken"):
        top["active"] = False
        return
    active = bool(evaluate_condition(vars_state, data))
    top["active"] = active
    if active:
        top["branch_taken"] = True


def handle_end_if(stack: list[dict[str, Any]]) -> None:
    if stack:
        stack.pop()


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


def _grab_region(region: tuple[int, int, int, int]) -> np.ndarray | None:
    x1, y1, x2, y2 = region
    if x2 <= x1 or y2 <= y1:
        return None
    with mss.mss() as sct:
        raw = sct.grab({"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1})
        img = np.array(raw)
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def _screen_size() -> tuple[int, int]:
    try:
        with mss.mss() as sct:
            mon = sct.monitors[0]
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


def _runtime_image_scale(data: dict[str, Any], template_path: str | None = None) -> float:
    image_base = _image_base_size_from_filename(template_path or "") if template_path else None
    if image_base is not None:
        base_w, base_h = image_base
    else:
        base_w, base_h = _screen_size()
    cur_w, cur_h = _screen_size()
    sx = cur_w / float(base_w)
    sy = cur_h / float(base_h)
    return max(0.1, (sx + sy) / 2.0)


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
    base_scale = _runtime_image_scale(data, template_path)
    scales = tuple(sorted({0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.15,
                           base_scale * 0.80, base_scale * 0.90, base_scale,
                           base_scale * 1.10, base_scale * 1.20}))
    for scale in scales:
        tpl = template
        if scale != 1.0:
            tw = max(2, int(round(template.shape[1] * scale)))
            th = max(2, int(round(template.shape[0] * scale)))
            tpl = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA)
            tpl_mask = _resize_mask(mask, (tw, th))
        else:
            tpl_mask = mask
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
