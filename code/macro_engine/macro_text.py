"""MacroForge .macro text format — v2 ("pretty") reader/writer.

Two on-disk formats:

  v1 (legacy): line-based ``TYPE:VALUE`` instructions::

      IF:{"expr":{"lit":true}}
      DELAY:50
      END_IF

  v2 (pretty): C-style braces + readable conditions::

      IF (true) {
        DELAY 50
      }

Everything reads through :func:`canonicalize_lines` — v2 lines are
translated to the exact v1 instruction list the engine already runs,
and v1 lines pass through untouched. Old files keep loading forever;
the engine never had to change.

The writer (:func:`pretty_body`) emits v2. Conditions are rendered by
:func:`expr_to_str` and read back by :func:`expr_from_str` as a
lossless pair (see tests).
"""

from __future__ import annotations

import json
import re

__all__ = [
    "expr_to_str",
    "expr_from_str",
    "canonicalize_lines",
    "canonicalize_text",
    "pretty_body",
    "MacroTextError",
]


class MacroTextError(ValueError):
    """Raised when a pretty-format line cannot be parsed."""


# ─────────────────────────────────────────────────────────────────────────
# Expression tree  <->  readable text
#
# Nodes (macro/macro_logic.eval_expr):
#   {lit: bool|number|string}   {get: name}
#   {cmp: {op, a, b}}           op: EQ NEQ LT LTE GT GTE
#   {and:{a,b}} {or:{a,b}} {not: x}
#   {arith: {op, a, b}}         op: + - * / ^
#   {img_eq: {a, b, neq}}       a/b: '' | str | {get}
#   {img_on_screen: {path, threshold, [search_x1..y2]}}
#   {color_eq: {x, y, rgba: [r,g,b(,a)], tol}}
#   {color_diff: {a, b}}      a/b: color expression (hex/rgba lit, {get})
#   {res_spec: {rw, rh, dw, dh}}    resolution spec (flow editor's ratio block)
#   {point: {x, y}} / {box: {x1..y2}}   recorded point/box
#   {res_scale: {a, spec}}     scale a point/box to the current screen (spec optional)
#   {img_diff: {a, b}}        a/b: '' | str | {get}
# ─────────────────────────────────────────────────────────────────────────

# precedence levels (higher binds tighter)
_P_OR, _P_AND, _P_EQ, _P_REL, _P_ADD, _P_MUL, _P_POW, _P_UNARY, _P_ATOM = 1, 2, 3, 4, 5, 6, 7, 8, 9

_CMP_OPS = {"EQ": "==", "NEQ": "!=", "LT": "<", "LTE": "<=", "GT": ">", "GTE": ">="}
_CMP_OPS_REV = {v: k for k, v in _CMP_OPS.items()}
_ARITH_OPS = {"+", "-", "*", "/", "^"}
_FUNC_NAMES = ("get", "img_eq", "img_on_screen", "color_eq", "color_diff", "img_diff",
               "ratio", "point", "box", "scale", "grab", "grab_at", "screen_color")
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _fmt_num(v) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if f.is_integer() and abs(f) < 1e15:
        return str(int(f))
    return repr(f)


def _q(s: str) -> str:
    out = str(s).replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return '"' + out + '"'


def _unq(s: str) -> str:
    if len(s) < 2 or s[0] != '"' or s[-1] != '"':
        raise MacroTextError("expected quoted string")
    body = s[1:-1]
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append({"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _render_path(p):
    """'' | str | {get} | {grab} | {lit} → text via the generic renderer."""
    if isinstance(p, dict) and "get" in p:
        return _render({"get": p["get"]})
    if isinstance(p, dict):
        # {grab}, {lit}, {screen_color}… — render the node itself; wrapping
        # it in another {lit: …} rendered the dict repr as a string
        return _render(p)
    return _render({"lit": p})


def _render(node):
    """expr tree → (text, precedence). Falls back to `true` on garbage."""
    if node is None:
        node = {"lit": True}
    if not isinstance(node, dict):
        node = {"lit": node}

    def sub(child, my_p, right: bool, right_assoc: bool = False):
        if child is None:
            child = {"lit": True}
        text, p = _render(child)
        if right:
            wrap = p < my_p if right_assoc else p <= my_p
        else:
            wrap = p <= my_p if right_assoc else p < my_p
        return "(" + text + ")" if wrap else text

    if "lit" in node:
        v = node["lit"]
        if isinstance(v, bool):
            return ("true" if v else "false"), _P_ATOM
        if isinstance(v, (int, float)):
            return _fmt_num(v), _P_ATOM
        return _q(str(v)), _P_ATOM

    if "get" in node:
        name = str(node["get"] or "")
        if _IDENT_RE.match(name) and name not in ("true", "false") and name not in _FUNC_NAMES:
            return name, _P_ATOM
        return "get(%s)" % _q(name), _P_ATOM

    if "cmp" in node:
        c = node.get("cmp") or {}
        op = str(c.get("op") or "EQ").upper()
        if op not in _CMP_OPS:
            op = "EQ"
        a = sub(c.get("a"), _P_EQ, False)
        b = sub(c.get("b"), _P_EQ, False)
        return "%s %s %s" % (a, _CMP_OPS[op], b), _P_EQ

    if "and" in node or "or" in node:
        is_and = "and" in node
        d = node.get("and" if is_and else "or") or {}
        p = _P_AND if is_and else _P_OR
        a = sub(d.get("a"), p, False)
        b = sub(d.get("b"), p, True)
        return "%s %s %s" % (a, "&&" if is_and else "||", b), p

    if "not" in node:
        inner = node["not"]
        if inner is None:
            inner = {"lit": True}
        text, p = _render(inner)
        if p < _P_UNARY:
            text = "(" + text + ")"
        return "!" + text, _P_UNARY

    if "arith" in node:
        e = node.get("arith") or {}
        op = str(e.get("op") or "+")
        if op not in _ARITH_OPS:
            op = "+"
        if op in ("+", "-"):
            p = _P_ADD
        elif op in ("*", "/"):
            p = _P_MUL
        else:
            p = _P_POW
        a = sub(e.get("a"), p, False, right_assoc=(op == "^"))
        b = sub(e.get("b"), p, True, right_assoc=(op == "^"))
        return "%s %s %s" % (a, op, b), p

    if "img_eq" in node:
        d = node.get("img_eq") or {}
        args = [
            _render_path(d.get("a", ""))[0],
            _render_path(d.get("b", ""))[0],
        ]
        if d.get("neq"):
            args.append("neq")
        return "img_eq(%s)" % ", ".join(args), _P_ATOM

    if "img_on_screen" in node:
        d = node.get("img_on_screen") or {}
        thr = d.get("threshold")
        args = [_render_path(d.get("path", ""))[0], _fmt_num(85 if thr is None else thr)]
        box = [d.get("search_x1"), d.get("search_y1"), d.get("search_x2"), d.get("search_y2")]
        if all(v is not None for v in box):
            args.extend(_coord_render(v) for v in box)
        return "img_on_screen(%s)" % ", ".join(args), _P_ATOM

    if "color_eq" in node:
        d = node.get("color_eq") or {}
        rgba = d.get("rgba") or [255, 255, 255, 255]
        args = [_coord_render(d.get("x"), 0), _coord_render(d.get("y"), 0)]
        args.extend(_fmt_num(v) for v in rgba)
        tol = d.get("tol")
        args.append(_fmt_num(10 if tol is None else tol))
        return "color_eq(%s)" % ", ".join(args), _P_ATOM

    # ── resolution blocks (1:1 with the flow editor's ratio/scale) ──
    if "res_spec" in node:
        d = node.get("res_spec") or {}
        args = [sub(d.get(k) or {"lit": 0}, _P_ATOM, False) for k in ("rw", "rh", "dw", "dh")]
        return "ratio(%s)" % ", ".join(args), _P_ATOM

    if "point" in node:
        d = node.get("point") or {}
        args = [sub(d.get(k) or {"lit": 0}, _P_ATOM, False) for k in ("x", "y")]
        return "point(%s)" % ", ".join(args), _P_ATOM

    if "box" in node:
        d = node.get("box") or {}
        args = [sub(d.get(k) or {"lit": 0}, _P_ATOM, False) for k in ("x1", "y1", "x2", "y2")]
        return "box(%s)" % ", ".join(args), _P_ATOM

    if "grab" in node:
        # get image from screen — grab_at(x, y, w, h) point+size form (new),
        # grab(x1, y1, x2, y2) region form (legacy). Coords may be scale()s.
        d = node.get("grab") or {}
        if "w" in d or "x" in d:
            args = []
            for k in ("x", "y", "w", "h"):
                v = d.get(k, 0)
                args.append(sub(v, _P_ATOM, False) if isinstance(v, dict) else _fmt_num(int(v or 0)))
            return "grab_at(%s)" % ", ".join(args), _P_ATOM
        args = []
        for k in ("search_x1", "search_y1", "search_x2", "search_y2"):
            v = d.get(k, 0)
            if isinstance(v, dict):
                args.append(sub(v, _P_ATOM, False))
            else:
                args.append(_fmt_num(int(v or 0)))
        return "grab(%s)" % ", ".join(args), _P_ATOM

    if "screen_color" in node:
        # get color from screen at point — screen_color(x, y)
        d = node.get("screen_color") or {}
        args = []
        for k in ("x", "y"):
            v = d.get(k, 0)
            args.append(sub(v, _P_ATOM, False) if isinstance(v, dict) else _fmt_num(int(v or 0)))
        return "screen_color(%s)" % ", ".join(args), _P_ATOM

    if "res_scale" in node:
        d = node.get("res_scale") or {}
        a = sub(d.get("a") or {"lit": True}, _P_ATOM, False)
        if d.get("spec") is not None:
            s = sub(d.get("spec"), _P_ATOM, False)
            return "scale(%s, %s)" % (a, s), _P_ATOM
        return "scale(%s)" % a, _P_ATOM

    if "color_diff" in node:
        d = node.get("color_diff") or {}
        a = sub(d.get("a") or {"lit": "#FFFFFF"}, _P_ATOM, False)
        b = sub(d.get("b") or {"lit": "#FFFFFF"}, _P_ATOM, False)
        return "color_diff(%s, %s)" % (a, b), _P_ATOM

    if "img_diff" in node:
        d = node.get("img_diff") or {}
        args = [
            _render_path(d.get("a", ""))[0],
            _render_path(d.get("b", ""))[0],
        ]
        return "img_diff(%s)" % ", ".join(args), _P_ATOM

    # unknown node → literal true so output stays runnable
    return "true", _P_ATOM


def _coord_render(v, dflt=0):
    """A coordinate value: plain number or a full expression tree
    (e.g. {res_scale}) — exprs render as their call text."""
    if isinstance(v, dict):
        return _render(v)[0]
    return _fmt_num(v if v is not None else dflt)


def expr_to_str(node) -> str:
    """Expression tree → readable text (lossless via expr_from_str)."""
    return _render(node)[0]


# ── tokenizer / parser ────────────────────────────────────────────────────

_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (?P<num>\d+\.\d+|\d+)
      | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<op>\|\||&&|==|!=|<=|>=|<|>|\+|-|\*|/|\^|!|\(|\)|,)
      | (?P<str>"(?:[^"\\]|\\.)*")
    )""",
    re.VERBOSE,
)


def _tokenize(s: str):
    toks, i = [], 0
    while i < len(s):
        if s[i:].strip() == "":
            break
        m = _TOKEN_RE.match(s, i)
        if not m or m.end() == i:
            raise MacroTextError("bad character in expression: %r" % s[i : i + 4])
        i = m.end()
        if m.group("num"):
            toks.append(("num", m.group("num")))
        elif m.group("ident"):
            toks.append(("ident", m.group("ident")))
        elif m.group("op"):
            toks.append(("op", m.group("op")))
        elif m.group("str"):
            toks.append(("str", m.group("str")))
    toks.append(("end", ""))
    return toks


class _P:
    """Recursive-descent parser: text → expression tree (C precedence)."""

    def __init__(self, s: str):
        self.toks = _tokenize(s)
        self.i = 0

    def peek(self):
        return self.toks[self.i]

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def eat_op(self, *ops):
        k, v = self.peek()
        if k == "op" and v in ops:
            self.i += 1
            return v
        return None

    def expect_op(self, op):
        if not self.eat_op(op):
            raise MacroTextError("expected %r" % op)

    def parse(self):
        node = self.p_or()
        if self.peek()[0] != "end":
            raise MacroTextError("trailing tokens in expression")
        return node

    def p_or(self):
        node = self.p_and()
        while self.eat_op("||"):
            node = {"or": {"a": node, "b": self.p_and()}}
        return node

    def p_and(self):
        node = self.p_eq()
        while self.eat_op("&&"):
            node = {"and": {"a": node, "b": self.p_eq()}}
        return node

    def p_eq(self):
        node = self.p_rel()
        while True:
            op = self.eat_op("==", "!=")
            if not op:
                return node
            node = {"cmp": {"op": _CMP_OPS_REV[op], "a": node, "b": self.p_rel()}}

    def p_rel(self):
        node = self.p_add()
        while True:
            op = self.eat_op("<", "<=", ">", ">=")
            if not op:
                return node
            node = {"cmp": {"op": _CMP_OPS_REV[op], "a": node, "b": self.p_add()}}

    def p_add(self):
        node = self.p_mul()
        while True:
            op = self.eat_op("+", "-")
            if not op:
                return node
            node = {"arith": {"op": op, "a": node, "b": self.p_mul()}}

    def p_mul(self):
        node = self.p_pow()
        while True:
            op = self.eat_op("*", "/")
            if not op:
                return node
            node = {"arith": {"op": op, "a": node, "b": self.p_pow()}}

    def p_pow(self):
        node = self.p_unary()
        if self.eat_op("^"):
            # right associative
            return {"arith": {"op": "^", "a": node, "b": self.p_pow()}}
        return node

    def p_unary(self):
        if self.eat_op("!"):
            return {"not": self.p_unary()}
        if self.eat_op("-"):
            inner = self.p_unary()
            if isinstance(inner, dict) and "lit" in inner and isinstance(inner["lit"], (int, float)) and not isinstance(inner["lit"], bool):
                return {"lit": -inner["lit"]}
            return {"arith": {"op": "-", "a": {"lit": 0}, "b": inner}}
        return self.p_atom()

    def p_atom(self):
        k, v = self.peek()
        if k == "num":
            self.i += 1
            return {"lit": float(v) if "." in v else int(v)}
        if k == "str":
            self.i += 1
            return {"lit": _unq(v)}
        if k == "ident":
            self.i += 1
            if v == "true":
                return {"lit": True}
            if v == "false":
                return {"lit": False}
            nk, nv = self.peek()
            if nk == "op" and nv == "(":
                self.i += 1
                return self.p_call(v)
            return {"get": v}
        if k == "op" and v == "(":
            self.i += 1
            node = self.p_or()
            self.expect_op(")")
            return node
        raise MacroTextError("unexpected token %r" % (v or "end"))

    def p_call(self, name: str):
        args = []
        if self.peek() != ("op", ")"):
            while True:
                args.append(self.p_or())
                if not self.eat_op(","):
                    break
        self.expect_op(")")
        if name == "get":
            if len(args) != 1 or not (isinstance(args[0], dict) and "lit" in args[0] and isinstance(args[0]["lit"], str)):
                raise MacroTextError("get() needs one string")
            return {"get": args[0]["lit"]}
        if name == "grab":
            if len(args) != 4:
                raise MacroTextError("grab() needs 4 args")
            return {"grab": {
                "fixed": False,
                "search_x1": _coord_arg(args[0]),
                "search_y1": _coord_arg(args[1]),
                "search_x2": _coord_arg(args[2]),
                "search_y2": _coord_arg(args[3]),
            }}
        if name == "grab_at":
            if len(args) != 4:
                raise MacroTextError("grab_at() needs 4 args")
            return {"grab": {
                "x": _coord_arg(args[0]),
                "y": _coord_arg(args[1]),
                "w": _coord_arg(args[2]),
                "h": _coord_arg(args[3]),
            }}
        if name == "screen_color":
            if len(args) != 2:
                raise MacroTextError("screen_color() needs 2 args")
            return {"screen_color": {
                "x": _coord_arg(args[0]),
                "y": _coord_arg(args[1]),
            }}
        if name == "img_eq":
            if len(args) not in (2, 3):
                raise MacroTextError("img_eq() needs 2 or 3 args")
            neq = False
            if len(args) == 3:
                if args[2] != {"get": "neq"}:
                    raise MacroTextError("img_eq() third arg must be neq")
                neq = True
            return {"img_eq": {"a": _path_val(args[0]), "b": _path_val(args[1]), "neq": neq}}
        if name == "img_on_screen":
            if len(args) not in (2, 6):
                raise MacroTextError("img_on_screen() needs 2 or 6 args")
            d = {"path": _path_val(args[0]), "threshold": _num_val(args[1])}
            if len(args) == 6:
                d["search_x1"] = _coord_arg(args[2])
                d["search_y1"] = _coord_arg(args[3])
                d["search_x2"] = _coord_arg(args[4])
                d["search_y2"] = _coord_arg(args[5])
            return {"img_on_screen": d}
        if name == "color_eq":
            if len(args) not in (6, 7):
                raise MacroTextError("color_eq() needs 6 or 7 args")
            rgba = [_num_val(a) for a in args[2 : len(args) - 1]]
            return {"color_eq": {
                "x": _coord_arg(args[0]), "y": _coord_arg(args[1]),
                "rgba": rgba, "tol": _num_val(args[-1]),
            }}
        if name == "ratio":
            if len(args) != 4:
                raise MacroTextError("ratio() needs 4 args")
            return {"res_spec": {"rw": args[0], "rh": args[1], "dw": args[2], "dh": args[3]}}
        if name == "point":
            if len(args) != 2:
                raise MacroTextError("point() needs 2 args")
            return {"point": {"x": args[0], "y": args[1]}}
        if name == "box":
            if len(args) != 4:
                raise MacroTextError("box() needs 4 args")
            return {"box": {"x1": args[0], "y1": args[1], "x2": args[2], "y2": args[3]}}
        if name == "scale":
            if len(args) not in (1, 2):
                raise MacroTextError("scale() needs 1 or 2 args")
            return {"res_scale": {"a": args[0], "spec": args[1] if len(args) > 1 else None}}
        if name == "color_diff":
            if len(args) != 2:
                raise MacroTextError("color_diff() needs 2 args")
            return {"color_diff": {"a": args[0], "b": args[1]}}
        if name == "img_diff":
            if len(args) != 2:
                raise MacroTextError("img_diff() needs 2 args")
            return {"img_diff": {"a": _path_val(args[0]), "b": _path_val(args[1])}}
        raise MacroTextError("unknown function %r" % name)


def _path_val(a):
    if isinstance(a, dict) and "get" in a:
        return {"get": a["get"]}
    if isinstance(a, dict) and "grab" in a:
        return a
    if isinstance(a, dict) and "lit" in a:
        return a["lit"]
    raise MacroTextError("bad path argument")


def _num_val(a):
    if isinstance(a, dict) and "lit" in a:
        v = a["lit"]
        if isinstance(v, (bool, int, float)):
            return v
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0
    raise MacroTextError("bad numeric argument")


def _coord_arg(a):
    """Parser side of _coord_render: an expression node stays a tree, a
    literal number unwraps to plain (render/parse round trips exactly),
    anything else coerces to a number (old payloads stay plain)."""
    if isinstance(a, dict):
        if "lit" in a and isinstance(a["lit"], (int, float)) and not isinstance(a["lit"], bool):
            return a["lit"]
        return a
    return _num_val(a)


def expr_from_str(s: str):
    """Readable text → expression tree."""
    if not str(s or "").strip():
        return {"lit": True}
    return _P(str(s)).parse()


# ─────────────────────────────────────────────────────────────────────────
# canonicalize: any .macro text → v1 engine instruction lines
# ─────────────────────────────────────────────────────────────────────────

_BARE_OPS = {
    "MOUSE_LEFT_DOWN", "MOUSE_LEFT_UP", "MOUSE_LEFT_CLICK",
    "MOUSE_RIGHT_DOWN", "MOUSE_RIGHT_UP", "MOUSE_RIGHT_CLICK",
    "MOUSE_MIDDLE_DOWN", "MOUSE_MIDDLE_UP", "MOUSE_MIDDLE_CLICK",
}
_COORD_OPS = {"MOUSE_MOVE_ABS", "MOUSE_REL", "SMOOTH_MOVE", "LOOK"}
_KEY_OPS = {"KEY_DOWN", "KEY_UP", "KEY_PRESS"}


def _strip_brace(v: str) -> str:
    v = v.strip()
    if v.endswith("{"):
        v = v[:-1].strip()
    return v.strip()


def _cond_json(text: str) -> str:
    try:
        return json.dumps({"expr": expr_from_str(text)}, separators=(",", ":"))
    except MacroTextError:
        return json.dumps({"expr": {"lit": True}}, separators=(",", ":"))


def _key_hex(v: str) -> str:
    v = v.strip()
    try:
        return format(int(v, 16), "x")
    except ValueError:
        return v


def _parse_kv_args(rest: str) -> dict:
    """IMAGE-style ``k=v k="v" k=true k=[..]`` → dict."""
    out = {}
    pat = re.compile(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
        r'("(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|true|false|\{.*?\}|\[.*?\]|[^\s]+)'
    )
    for m in pat.finditer(rest):
        k, raw = m.group(1), m.group(2)
        if raw.startswith('"'):
            out[k] = _unq(raw)
        elif raw == "true":
            out[k] = True
        elif raw == "false":
            out[k] = False
        elif raw.startswith("{") or raw.startswith("["):
            try:
                out[k] = json.loads(raw)
            except Exception:
                out[k] = raw
        else:
            try:
                out[k] = int(raw)
            except ValueError:
                try:
                    out[k] = float(raw)
                except ValueError:
                    out[k] = raw
    return out


def _emit_kv(d: dict) -> str:
    parts = []
    for k, v in d.items():
        if isinstance(v, bool):
            sv = "true" if v else "false"
        elif isinstance(v, (int, float)):
            sv = _fmt_num(v)
        elif isinstance(v, str):
            sv = _q(v)
        else:
            sv = json.dumps(v, separators=(",", ":"))
        parts.append("%s=%s" % (k, sv))
    return " ".join(parts)


_VAR_TYPE_MAP = {"number": "number", "text": "text", "boolean": "boolean", "bool": "boolean", "image": "image", "resloc": "resloc", "color": "color"}


def _variable_line(d: dict) -> str:
    name = str(d.get("name") or "")
    vtype = str(d.get("var_type") or "number")
    value = d.get("value")
    if value is None or value == "":
        if vtype in ("text", "image", "resloc", "color"):
            value = ""
        elif vtype == "boolean":
            value = False
        else:
            value = 0
    if isinstance(value, bool):
        sv = "true" if value else "false"
    elif isinstance(value, (int, float)):
        sv = _fmt_num(value)
    else:
        sv = _q(str(value))
    return "VARIABLE %s : %s = %s" % (name, vtype, sv)


_VAR_RE = re.compile(r"^VARIABLE\s+(.+?)\s*:\s*(\w+)\s*=\s*(.*)$")


def _variable_payload(rest: str) -> str:
    m = _VAR_RE.match("VARIABLE " + rest.strip())
    if not m:
        return json.dumps({"name": "", "var_type": "number", "value": 0}, separators=(",", ":"))
    name, vtype, raw = m.group(1).strip(), m.group(2).strip().lower(), m.group(3).strip()
    vtype = _VAR_TYPE_MAP.get(vtype, "number")
    if vtype == "boolean":
        value = raw.lower() == "true"
    elif vtype in ("text", "image", "resloc", "color"):
        value = _unq(raw) if raw.startswith('"') else raw
    else:
        try:
            value = float(raw)
            if value.is_integer():
                value = int(value)
        except ValueError:
            value = 0
    return json.dumps({"name": name, "var_type": vtype, "value": value}, separators=(",", ":"))


_SET_RE = re.compile(r"^SET\s+(.+?)\s*=\s*(.+)$", re.DOTALL)


def _set_variable_payload(rest: str) -> str:
    m = _SET_RE.match("SET " + rest.strip())
    if not m:
        return json.dumps({"name": "", "value": {"lit": True}}, separators=(",", ":"))
    name = m.group(1).strip()
    if name.startswith('"'):
        name = _unq(name)
    return json.dumps({"name": name, "value": expr_from_str(m.group(2))}, separators=(",", ":"))


def canonicalize_lines(lines) -> list:
    """Any .macro line list (v1 or v2) → the v1 instruction list.

    v1 lines pass through unchanged. v2 pretty lines are translated.
    Unknown lines pass through untouched (the engine ignores them).
    """
    out = []
    stack = []  # 'IF' | 'REPEAT' | 'GROUP' | 'SECTION' | 'LOCK'
    # expand combined close+open lines ("} ELSE IF (…) {", "} ELSE {")
    flat = []
    for raw in lines:
        line = raw.strip() if isinstance(raw, str) else str(raw).strip()
        while line.startswith("}") and line != "}":
            rest = line[1:].strip()
            if re.match(r"(ELSE\s*IF|ELSEIF|ELSE)\b", rest):
                # "} ELSE IF (…) {" is a branch separator — the IF stays open
                line = rest
                break
            flat.append("}")
            line = rest
        if line:
            flat.append(line)
    for line in flat:
        if line.startswith("//"):
            comment = line[2:].strip()
            out.append("# " + comment if comment else "#")
            continue
        if line.startswith("#"):
            out.append(line)  # machine meta / legacy markers / STRAY
            continue
        if line == "}":
            if stack:
                kind = stack.pop()
                if kind == "IF":
                    out.append("END_IF")
                elif kind == "REPEAT":
                    out.append("ENDREPEAT")
                elif kind == "WHILE":
                    out.append("END_WHILE:")
                elif kind == "UNTIL":
                    out.append("END_UNTIL:")
                elif kind == "GROUP":
                    out.append("# GROUP_END")
                elif kind == "LOCK":
                    out.append("LOCK_END:")
                elif kind == "UNTIL_BG":
                    out.append("BG_END:")
                else:
                    out.append("# SECTION_END")
            continue
        if re.match(r"^BACKGROUND\s*\{\s*$", line):
            # "} BACKGROUND {" arm of a WHILE/UNTIL loop — steps after it
            # run on a background thread until the loop exits
            out.append("BG_BEGIN:")
            stack.append("UNTIL_BG")
            continue
        m = re.match(r"^(IF|ELSE\s*IF|ELSEIF)\s*\((.*)\)\s*\{?\s*$", line)
        if m:
            kw = re.sub(r"\s+", "_", m.group(1).upper())
            out.append(("%s:" % kw) + _cond_json(m.group(2)))
            if m.group(1).upper().replace(" ", "") == "IF":
                stack.append("IF")
            elif not (stack and stack[-1] == "IF"):
                stack.append("IF")  # tolerate stray ELSE IF without IF
            continue
        if re.match(r"^ELSE\b\s*\{?\s*$", line):
            out.append("ELSE:")
            continue
        # pretty REPEAT always has whitespace after the keyword ("REPEAT 10 {"),
        # legacy is "REPEAT:10" — colon keeps it on the passthrough path
        m = re.match(r"^REPEAT\s+\(?\s*(.+?)\s*\)?\s*\{?\s*$", line)
        if m:
            v = _strip_brace(m.group(1))
            if v:
                out.append("REPEAT:" + v)
                stack.append("REPEAT")
                continue
        # pretty WHILE (cond) { / UNTIL (cond) { — repeat-while/until loops
        m = re.match(r"^(WHILE|UNTIL)\s*\((.*)\)\s*\{?\s*$", line)
        if m:
            out.append("%s:%s" % (m.group(1), _cond_json(m.group(2))))
            stack.append(m.group(1))
            continue
        m = re.match(r'^(GROUP|SECTION)\s+"((?:[^"\\]|\\.)*)"\s*\{\s*$', line)
        if m:
            out.append("# %s:%s" % (m.group(1), _unq('"' + m.group(2) + '"')))
            stack.append(m.group(1))
            continue
        if re.match(r"^LOCK\s*\{\s*$", line):
            # Lock is a VISIBLE envelope (not a # marker): the engine
            # skips LOCK:/LOCK_END: explicitly, and F5 re-record keeps
            # everything between them
            out.append("LOCK:")
            stack.append("LOCK")
            continue
        # bare scalar keyword with no rest — pretty emits e.g. a bare
        # "PRINT" when the value is empty; keep it a real instruction
        # ("PRINT:") so the runner prints the empty line instead of
        # silently dropping it on the passthrough path
        if re.match(r"^(PRINT|LABEL)$", line):
            out.append(line + ":")
            continue
        # pretty keyword instructions: KEYWORD <rest>  (no colon → not v1)
        m = re.match(r"^([A-Z][A-Z_0-9]*)\s+(.*)$", line)
        if m and ":" not in line.split()[0]:
            kw, rest = m.group(1), m.group(2)
            if kw == "WATCH":
                # WATCH <var> WHEN (<cond>) EVERY <ms> — background watcher
                wm = re.match(r"^([A-Za-z0-9_]+)\s+WHEN\s*\((.*)\)\s+EVERY\s+(.+?)\s*$", rest)
                if wm:
                    try:
                        every = int(float(wm.group(3)))
                    except Exception:
                        every = 100
                    try:
                        wexpr = expr_from_str(wm.group(2))
                    except MacroTextError:
                        wexpr = {"lit": True}
                    out.append("WATCH:" + json.dumps(
                        {"var": wm.group(1), "expr": wexpr, "every_ms": every},
                        separators=(",", ":")))
                else:
                    out.append("WATCH:" + rest.strip())
                continue
            if kw == "STOP" and rest.upper().startswith("WATCH"):
                out.append("STOP_WATCH:" + rest[5:].strip())
                continue
            if kw == "VARIABLE":
                out.append("VARIABLE:" + _variable_payload(rest))
            elif kw == "SET":
                out.append("SET_VARIABLE:" + _set_variable_payload(rest))
            elif kw == "IMAGE":
                out.append("IMAGE:" + json.dumps(_parse_kv_args(rest), separators=(",", ":")))
            elif kw == "GRAB_IMAGE":
                out.append("GRAB_IMAGE:" + json.dumps(_parse_kv_args(rest), separators=(",", ":")))
            elif kw == "PLAY_MACRO":
                v = rest.strip()
                out.append("PLAY_MACRO:" + (_unq(v) if len(v) >= 2 and v.startswith('"') and v.endswith('"') else v))
            elif kw in _KEY_OPS:
                out.append("%s:%s" % (kw, _key_hex(rest)))
            elif kw in _COORD_OPS:
                if rest.strip().startswith("scale("):
                    # scale(x, y, rw, rh, dw, dh) — the flat scaled-coord form;
                    # its commas belong to the call, not to the coord list
                    out.append("%s:%s" % (kw, rest.strip()))
                else:
                    out.append("%s:%s" % (kw, ",".join(p.strip() for p in rest.split(","))))
            else:  # DELAY / LABEL / GOTO / anything scalar
                out.append("%s:%s" % (kw, rest.strip()))
            continue
        # v1 or unknown → passthrough
        out.append(line)
    return out


def canonicalize_text(text) -> list:
    if isinstance(text, str):
        return canonicalize_lines(text.splitlines())
    return canonicalize_lines(text)


# ─────────────────────────────────────────────────────────────────────────
# pretty_body: editor step list → v2 text body (no header/meta lines)
# ─────────────────────────────────────────────────────────────────────────

def _pretty_instr(t: str, v: str) -> str:
    if t == "PLAY_MACRO":
        return "PLAY_MACRO %s" % _q(v)
    if t in _KEY_OPS:
        return "%s 0x%s" % (t, _key_hex(v))
    if t in _COORD_OPS:
        if v.strip().startswith("scale("):
            return "%s %s" % (t, v.strip())
        return "%s %s" % (t, ", ".join(p.strip() for p in v.split(",")))
    if t == "VARIABLE":
        try:
            return _variable_line(json.loads(v or "{}"))
        except Exception:
            return "VARIABLE %s" % (v or "")
    if t == "SET_VARIABLE":
        try:
            d = json.loads(v or "{}")
            return "SET %s = %s" % (d.get("name") or "", expr_to_str(d.get("value")))
        except Exception:
            return "SET_VARIABLE:%s" % v
    if t == "IMAGE":
        try:
            return "IMAGE %s" % _emit_kv(json.loads(v or "{}"))
        except Exception:
            return "IMAGE:%s" % v
    if t == "GRAB_IMAGE":
        try:
            return "GRAB_IMAGE %s" % _emit_kv(json.loads(v or "{}"))
        except Exception:
            return "GRAB_IMAGE:%s" % v
    return ("%s %s" % (t, v)).strip()


def _pretty_cond(v: str) -> str:
    try:
        d = json.loads(v or "{}")
        return expr_to_str(d.get("expr", {"lit": True}))
    except Exception:
        return "true"


def pretty_body(steps) -> list:
    """Editor step list ({type, value, locked}) → pretty v2 body lines."""
    out = []
    depth = 0

    def ind():
        return "  " * depth

    sts = [s for s in (steps or []) if isinstance(s, dict)]
    i = 0
    while i < len(sts):
        st = sts[i]
        i += 1
        t = str(st.get("type") or "").strip()
        v = str(st.get("value") if st.get("value") is not None else "").strip()
        if not t:
            continue
        if t == "GROUP":
            out.append('%sGROUP %s {' % (ind(), _q(v)))
            depth += 1
        elif t == "GROUP_END":
            depth = max(0, depth - 1)
            out.append(ind() + "}")
        elif t == "SECTION":
            out.append('%sSECTION %s {' % (ind(), _q(v)))
            depth += 1
        elif t == "SECTION_END":
            depth = max(0, depth - 1)
            out.append(ind() + "}")
        elif t == "LOCK":
            out.append(ind() + "LOCK {")
            depth += 1
        elif t == "LOCK_END":
            depth = max(0, depth - 1)
            out.append(ind() + "}")
        elif t == "COMMENT":
            if v.startswith("STRAY:"):
                out.append(ind() + "# " + v)
            elif v:
                out.append(ind() + "// " + v)
        elif t == "IF":
            out.append("%sIF (%s) {" % (ind(), _pretty_cond(v)))
            depth += 1
        elif t == "ELSE_IF":
            if depth > 0:
                depth -= 1
                out.append("%s} ELSE IF (%s) {" % (ind(), _pretty_cond(v)))
            else:
                out.append("ELSE IF (%s) {" % _pretty_cond(v))
            depth += 1
        elif t == "ELSE":
            if depth > 0:
                depth -= 1
                out.append(ind() + "} ELSE {")
            else:
                out.append("ELSE {")
            depth += 1
        elif t == "END_IF":
            depth = max(0, depth - 1)
            out.append(ind() + "}")
        elif t == "REPEAT":
            out.append("%sREPEAT %s {" % (ind(), v or "1"))
            depth += 1
        elif t == "ENDREPEAT":
            depth = max(0, depth - 1)
            out.append(ind() + "}")
        elif t in ("WHILE", "UNTIL"):
            out.append("%s%s (%s) {" % (ind(), t, _pretty_cond(v)))
            depth += 1
        elif t in ("END_WHILE", "END_UNTIL"):
            depth = max(0, depth - 1)
            if i < len(sts) and str(sts[i].get("type") or "") == "BG_BEGIN":
                # loop carries a BACKGROUND arm: "} BACKGROUND {" keeps the
                # loop open — the arm's steps render next, BG_END closes it
                out.append(ind() + "} BACKGROUND {")
                depth += 1
                i += 1                      # consume the BG_BEGIN marker
            else:
                out.append(ind() + "}")
        elif t in _BARE_OPS:
            out.append(ind() + t)
        elif t == "WATCH":
            # background watcher: WATCH <var> WHEN (<cond>) EVERY <ms>
            try:
                d = json.loads(v or "{}")
                out.append("%sWATCH %s WHEN (%s) EVERY %s" % (
                    ind(), d.get("var") or "",
                    expr_to_str(d.get("expr") or {"lit": True}),
                    d.get("every_ms") if d.get("every_ms") is not None else 100))
            except Exception:
                out.append(ind() + _pretty_instr(t, v))
        elif t == "STOP_WATCH":
            out.append("%sSTOP WATCH %s" % (ind(), v or ""))
        elif t == "BG_END":
            depth = max(0, depth - 1)
            out.append(ind() + "}")
        else:
            out.append(ind() + _pretty_instr(t, v))
    while depth > 0:  # unbalanced safety net
        depth -= 1
        out.append("  " * depth + "}")
    return out
