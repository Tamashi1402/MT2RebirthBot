// ═════════════════════════════════════════════════════════════════════════════
// MacroForge — Blockly editor for the .macro format (macro tab).
// NOT Python generators: these blocks serialize to the flat block list
// [{type, value, locked}] that the recorder/player already use.
// ═════════════════════════════════════════════════════════════════════════════

// ── Key name → VK (mirrors macro_runner._binding_to_vk basics) ───────────────
const MFM_KEY_VK = {
  space: 0x20, enter: 0x0D, esc: 0x1B, tab: 0x09, backspace: 0x08,
  shift: 0x10, ctrl: 0x11, alt: 0x12,
  up: 0x26, down: 0x28, left: 0x25, right: 0x27,
};
(function () {
  for (let i = 0; i < 26; i++) MFM_KEY_VK[String.fromCharCode(97 + i)] = 0x41 + i; // a-z
  for (let i = 0; i < 10; i++) MFM_KEY_VK[String(i)] = 0x30 + i;                   // 0-9
  for (let i = 1; i <= 24; i++) MFM_KEY_VK['f' + i] = 0x70 + (i - 1);
  var extra = {
    win: 0x5B, 'caps lock': 0x14, 'num lock': 0x90, 'scroll lock': 0x91,
    'print screen': 0x2C, pause: 0x13, menu: 0x5D, delete: 0x2E, insert: 0x2D,
    home: 0x24, end: 0x23, 'page up': 0x21, 'page down': 0x22,
    comma: 0xBC, period: 0xBE, slash: 0xBF, semicolon: 0xBA, quote: 0xDE,
    'bracket left': 0xDB, 'bracket right': 0xDD, backslash: 0xDC,
    minus: 0xBD, equals: 0xBB, grave: 0xC0
  };
  Object.keys(extra).forEach(function (k) { if (MFM_KEY_VK[k] == null) MFM_KEY_VK[k] = extra[k]; });
  for (var n = 0; n <= 9; n++) MFM_KEY_VK['num ' + n] = 0x60 + n;
})();
const MFM_VK_NAME = {};
Object.keys(MFM_KEY_VK).forEach(function (k) {
  const v = MFM_KEY_VK[k];
  if (!MFM_VK_NAME[v] || k.length < MFM_VK_NAME[v].length) MFM_VK_NAME[v] = k;
});
// left/right modifier VKs the recorder emits (LEFT SHIFT=0xA0 etc.) → the
// generic key names; playback of 0x10/0x11/0x12 sends the LEFT scancode
MFM_VK_NAME[0xA0] = 'shift'; MFM_VK_NAME[0xA1] = 'shift';
MFM_VK_NAME[0xA2] = 'ctrl';  MFM_VK_NAME[0xA3] = 'ctrl';
MFM_VK_NAME[0xA4] = 'alt';   MFM_VK_NAME[0xA5] = 'alt';
const MFM_KEY_OPTIONS = [
  ['space', 'space'], ['enter', 'enter'], ['esc', 'esc'], ['tab', 'tab'],
  ['backspace', 'backspace'], ['shift', 'shift'], ['ctrl', 'ctrl'], ['alt', 'alt'],
  ['up', 'up'], ['down', 'down'], ['left', 'left'], ['right', 'right'],
];
for (let i = 1; i <= 12; i++) MFM_KEY_OPTIONS.push(['f' + i, 'f' + i]);
for (let i = 0; i < 10; i++) MFM_KEY_OPTIONS.push([String(i), String(i)]);
for (let i = 0; i < 26; i++) MFM_KEY_OPTIONS.push([String.fromCharCode(97 + i), String.fromCharCode(97 + i)]);

const MFM_MOUSE_OPTIONS = [['left', 'left'], ['right', 'right'], ['middle', 'middle (wheel)']];
function _mfmSocketKey(block, input) {
  var t = block && block.getInputTargetBlock && block.getInputTargetBlock(input);
  if (t) {
    return t.getFieldValue('KEY') || t.getFieldValue('BUTTON') || '';
  }
  return (block && block.getFieldValue && (block.getFieldValue(input) || block.getFieldValue('KEY') || block.getFieldValue('BUTTON'))) || '';
}
const MFM_OP_OPTIONS = [['set', 'set'], ['add', 'add'], ['subtract', 'subtract'], ['toggle', 'toggle']];

// ── Block definitions ────────────────────────────────────────────────────────

// Math
// ── Hat — 1:1 with the editor's pcr_procedure_hat (flow/procedure_hat.block.js)
Blockly.Blocks['mfm_hat'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('macro')
      .appendField(new Blockly.FieldTextInput('macro'), 'NAME');
    this.appendStatementInput('DO').setCheck(null);
    this.setPreviousStatement(false);
    this.setNextStatement(false);
    this.setDeletable(false);
    this.setMovable(true);
    this.hat = 'cap';
    this.setColour(120);
    this.setTooltip('Entry point of this macro. Everything under this cap runs top to bottom when the macro plays.');
  },
};

// attach the picker field (defined in macro-picker.js; label fallback if absent)
function _mfm_pickfield(kind) {
  if (typeof MfmPickField === 'function') return MfmPickField(kind);
  return new Blockly.FieldLabel(kind === 'smooth' ? '\u2b1a capture (F2)' : '\u2b1a pick (F2)');
}

// Flow — Delay
Blockly.Blocks['mfm_delay'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_delay",
      "message0": "Delay %1 ms",
      "args0": [{ "type": "input_value", "name": "MS", "check": "Number" }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 120,
    });
  },
};

// Flow — Print (app console)
Blockly.Blocks['mfm_print'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_print",
      "message0": "print %1",
      // only a plain string or "create text with" — everything else
      // (numbers, colors, image checks…) composes through text_join
      "args0": [{ "type": "input_value", "name": "TEXT", "check": ["String"] }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 160,
      "tooltip": "One line in the app console (dashboard Console panel). Plug a string or \"create text with\" — any other value (numbers, colors, image/color checks) composes through \"create text with\".",
    });
  },
};

// Flow — Repeat
Blockly.Blocks['mfm_repeat'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_repeat",
      "message0": "Repeat %1 times",
      "args0": [{ "type": "input_value", "name": "TIMES", "check": "Number" }],
      "message1": "do %1",
      "args1": [{ "type": "input_statement", "name": "DO" }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 120,
      "inputsInline": true,
    });
  },
};

// Flow — Label
Blockly.Blocks['mfm_label'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_label",
      "message0": "Label %1",
      "args0": [{ "type": "field_input", "name": "NAME", "text": "start" }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 120,
    });
  },
};

// Flow — Goto
Blockly.Blocks['mfm_goto'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_goto",
      "message0": "Goto label %1",
      "args0": [{ "type": "field_input", "name": "NAME", "text": "start" }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 120,
    });
  },
};

// Flow — Lock (contents survive re-record)
Blockly.Blocks['mfm_lock'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_lock",
      "message0": "Lock %1",
      "args0": [{ "type": "field_label", "name": "TIP", "text": "" }],
      "message1": "%1",
      "args1": [{ "type": "input_statement", "name": "DO" }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Blocks inside survive re-record (recorded blocks are appended around them).",
    });
  },
};

// Flow — Play macro
Blockly.Blocks['mfm_play_macro'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_play_macro",
      "message0": "Play macro %1",
      "args0": [{ "type": "input_value", "name": "PATH", "check": "String" }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 120,
    });
  },
};

// Flow — Group (recording / segment container)
// The steps live as DATA (the flat {type, value, locked} list) inside this
// block — never as child blocks on the canvas. That is the whole perf
// design: a 500k-step recording is ONE block here; its steps only render
// inside the mutator-style popup (edit) in their own workspace.
// File format: # GROUP:name ... # GROUP_END (playback skips # lines, so
// the engine needs zero changes).
Blockly.Blocks['mfm_group'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('Group', 'GROUPLBL')
      .appendField(new Blockly.FieldTextInput('recording'), 'NAME')
      .appendField(mfmGroupEditField(), 'EDIT')
      .appendField('', 'STEPS');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);   // Flow colour — same hue as label/goto (was 265)
    this.setTooltip('Named container for a run of steps (recordings, segments). The steps live inside — click edit to open them in their own editor. Playback runs the steps exactly as if they were on the canvas.');
    this.mfmSteps = [];   // flat list [{type, value, locked}]
  },
  domToMutation: function (el) {
    try { this.mfmSteps = JSON.parse(el.getAttribute('steps') || '[]') || []; }
    catch (e) { this.mfmSteps = []; }
    this.mfmUpdateBadge();
  },
  mutationToDom: function () {
    var m = document.createElement('mutation');
    try { m.setAttribute('steps', JSON.stringify(this.mfmSteps || [])); }
    catch (e) { m.setAttribute('steps', '[]'); }
    return m;
  },
  mfmUpdateBadge: function () {
    var n = (this.mfmSteps || []).filter(function (s) {
      return !(s && s.type === 'COMMENT' && typeof s.value === 'string' && s.value.indexOf('STRAY:') === 0);
    }).length;
    try { this.setFieldValue(n === 1 ? '(1 step)' : ('(' + n + ' steps)'), 'STEPS'); } catch (e) {}
  },
  mfmSetSteps: function (steps) {
    this.mfmSteps = steps || [];
    this.mfmUpdateBadge();
  },
};

// Flow — Repeat While/Until's BACKGROUND arm (mutator) now lives directly
// on the built-in controls_whileUntil block (see blockly/web/blocks/flow/
// while.block.js) instead of a separate mfm_while_bg block — one repeat
// while/until block in the toolbox, gear included.

// clickable 'edit' label — same proven pattern as macro-picker's MfmPickField
function mfmGroupEditField() {
  var field = new Blockly.FieldLabel('\u270e edit');
  field.EDITABLE = true;
  field.SERIALIZABLE = false;
  field.showEditor_ = function () {
    if (window.__mfmOpenGroup) window.__mfmOpenGroup(this.sourceBlock_);
  };
  return field;
}

// Flow — Comment (single # line in the .macro file)
Blockly.Blocks['mfm_comment'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('#', 'HASH')
      .appendField(new Blockly.FieldTextInput('note'), 'TEXT');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('Comment \u2014 stored as a single # line in the macro file. Playback ignores it.');
  },
};

// Section — collapsible "note" container (1:1 with the flow editor's
// pcr_separator). Blocks inside stay REAL blocks on the canvas; it
// serializes as # SECTION: / # SECTION_END comment lines, so playback
// ignores it and old files load unchanged.
Blockly.Blocks['mfm_section'] = {
  init: function () {
    this.appendDummyInput('HEADER')
      .appendField('\u2500\u2500\u2500')
      .appendField(new Blockly.FieldTextInput('note'), 'TEXT')
      .appendField('\u2500\u2500\u2500');
    this.appendStatementInput('DO').setCheck(null);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('A note/section \u2014 blocks inside stay visible on the canvas. Stored as comment lines; playback ignores them.');
  },
};

// Logic — If / Else If (conditions match macro_logic.evaluate_condition)
// If / Else if — 1:1 with the editor's controls_if: the condition is a
// DATA block (pcr_compare_*, image/color checks) plugged into the socket.
Blockly.Blocks['mfm_if'] = {
  init: function () {
    this.appendValueInput('COND').setCheck('Boolean').appendField('if');
    this.appendStatementInput('DO');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#5081b2');
    this.setTooltip('Run the body when the condition is true.');
  },
};
Blockly.Blocks['mfm_elseif'] = {
  init: function () {
    this.appendValueInput('COND').setCheck('Boolean').appendField('else if');
    this.appendStatementInput('DO');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#5081b2');
    this.setTooltip('Next branch, when earlier ones did not run.');
  },
};

// Image on screen — DATA block (Boolean output). Plugs into if / else if.
// Serializes as the expanded .macro expression {img_on_screen: {...}}.
// Group hat — the cap INSIDE the group edit window (says "Group <name>").
// Same shape as mfm_hat; the window syncs its NAME back to the group block.
Blockly.Blocks['mfm_group_hat'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('Group')
      .appendField(new Blockly.FieldTextInput('recording'), 'NAME');
    this.appendStatementInput('DO').setCheck(null);
    this.setPreviousStatement(false);
    this.setNextStatement(false);
    this.setDeletable(false);
    this.setMovable(true);
    this.hat = 'cap';
    this.setColour(120);
    this.setTooltip('Steps inside this group. Drag blocks in or out \u2014 the group on the main canvas updates live.');
  },
};


// Color at point — DATA block (Boolean output), 1:1 with the editor's
// color-data pattern (pcr_color_rgba in, boolean out).

// Image — check: composes the editor's pcr_image_from_res 1:1 (preview,
// pipette F2 crop into the macro images dir, res:// paths). Not a Python
// generator — serializes into the .macro IMAGE payload.

// Get image from screen — image VALUE block: plugs into any image socket
// (set variable, check image, image difference, compare image). At a
// POINT with a SIZE (width/height) box. For LOGIC ONLY: the capture is
// buffered in a temp PNG — nothing is saved in your macro folders.
// Serializes as {grab: {x, y, w, h}} (engine evaluates it live).

// Get color from screen — color VALUE block: reads the pixel at the point
// as #RRGGBB and plugs into any color socket (compare, diff, set var).
// No picker icon needed — the point block carries its own.

// Input / Mouse — Scaled move (ex SMOOTH_MOVE; 1:1 usage, scales with sensitivity)
Blockly.Blocks['mfm_scaled_move'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_scaled_move",
      "message0": "Scaled move %1 over %2 ms",
      "args0": [
        { "type": "input_value", "name": "POINT", "check": "Box" },
        { "type": "field_number", "name": "MS", "value": 0 },
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "inputsInline": true,
      "tooltip": "Relative move, scaled by sensitivity (was Smooth move). Capture the movement with the picker: hold F2, move, release.",
    });
    if (Blockly.icons && Blockly.icons.MFPickIcon) {
      this.addIcon(new Blockly.icons.MFPickIcon('smooth', this));
    }
  },
};

// Input / Mouse — Absolute move
Blockly.Blocks['mfm_abs_move'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_abs_move",
      "message0": "Absolute move %1",
      "args0": [{ "type": "input_value", "name": "POINT", "check": "Box" }],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "inputsInline": true,
      "tooltip": "Move the mouse to an absolute point. Pick it with the crosshair on the point block (F2).",
    });
  },
};

// Input / Mouse — Click / Down / Up
function mfm_makeMouseBlock(name, label, colour) {
  Blockly.Blocks[name] = {
    init: function () {
      this.appendValueInput('BUTTON')
        .setCheck(['Mouse', 'Key', 'String'])
        .appendField(label.replace(' %1', ''));
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setColour(colour);
      this.setInputsInline(true);
    },
  };
}
mfm_makeMouseBlock('mfm_click', 'Mouse click %1', 40);
mfm_makeMouseBlock('mfm_mouse_down', 'Mouse down', 40);
mfm_makeMouseBlock('mfm_mouse_up', 'Mouse up', 40);

function mfm_makeKeyBlock(name, label) {
  Blockly.Blocks[name] = {
    init: function () {
      this.appendValueInput('KEY')
        .setCheck(['Key', 'String'])
        .appendField(label.replace(' %1', ''));
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setColour(40);
      this.setInputsInline(true);
    },
  };
}
mfm_makeKeyBlock('mfm_key_down', 'Key %1 down');
mfm_makeKeyBlock('mfm_key_up', 'Key %1 up');
mfm_makeKeyBlock('mfm_press_key', 'Press key %1');

// Raw passthrough (unknown .macro line)
Blockly.Blocks['mfm_raw'] = {
  init: function () {
    this.jsonInit({
      "type": "mfm_raw",
      "message0": "%1 %2",
      "args0": [
        { "type": "field_input", "name": "TYPE", "text": "" },
        { "type": "field_input", "name": "VALUE", "text": "" },
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 0,
      "tooltip": "Unrecognized .macro line — kept as-is.",
    });
  },
};

// ── Serializer helpers ───────────────────────────────────────────────────────

// ── expression text renderer — JS port of macro_text._render ────────────
// Renders an expression node to the engine's readable call syntax
// (grab_at(…), screen_color(…), img_eq(…), arithmetic…) — exactly what
// expr_from_str parses back server-side, so ${…} refs in PRINT text
// survive the save → load round trip and the runner can evaluate them.
const _MFM_CMP_OPS = { EQ: '==', NEQ: '!=', LT: '<', LTE: '<=', GT: '>', GTE: '>=' };
const _MFM_FUNC_NAMES = ['get', 'img_eq', 'img_on_screen', 'color_eq', 'color_diff',
  'img_diff', 'ratio', 'point', 'box', 'scale', 'grab', 'grab_at', 'screen_color'];

function _mfm_q(s) {
  return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"')
    .replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t') + '"';
}
function _mfm_fmt_num(v) {
  const n = Number(v);
  if (!isFinite(n)) return String(v);
  return String(n);
}
// node -> [text, precedence]; mirrors macro_text._render 1:1
function _mfm_render(node) {
  if (node === null || node === undefined) node = { lit: true };
  if (typeof node !== 'object' || Array.isArray(node)) node = { lit: node };
  function sub(child, myP, right, rightAssoc) {
    if (child === null || child === undefined) child = { lit: true };
    const r = _mfm_render(child);
    const wrap = right ? (rightAssoc ? r[1] < myP : r[1] <= myP)
                        : (rightAssoc ? r[1] <= myP : r[1] < myP);
    return wrap ? '(' + r[0] + ')' : r[0];
  }
  if ('lit' in node) {
    const v = node.lit;
    if (typeof v === 'boolean') return [v ? 'true' : 'false', 9];
    if (typeof v === 'number') return [_mfm_fmt_num(v), 9];
    return [_mfm_q(v === null || v === undefined ? '' : String(v)), 9];
  }
  if ('get' in node) {
    const name = String(node.get || '');
    if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) && name !== 'true' && name !== 'false' &&
        _MFM_FUNC_NAMES.indexOf(name) < 0) return [name, 9];
    return ['get(' + _mfm_q(name) + ')', 9];
  }
  if ('cmp' in node) {
    const c = node.cmp || {};
    const op = _MFM_CMP_OPS[String(c.op || 'EQ').toUpperCase()] || '==';
    return [sub(c.a, 3, false) + ' ' + op + ' ' + sub(c.b, 3, false), 3];
  }
  if ('and' in node || 'or' in node) {
    const isAnd = 'and' in node;
    const e = node[isAnd ? 'and' : 'or'] || {};
    const p = isAnd ? 2 : 1;
    return [sub(e.a, p, false) + (isAnd ? ' && ' : ' || ') + sub(e.b, p, true), p];
  }
  if ('not' in node) {
    const inner = _mfm_render(node.not === null || node.not === undefined ? { lit: true } : node.not);
    return ['!' + (inner[1] < 8 ? '(' + inner[0] + ')' : inner[0]), 8];
  }
  if ('arith' in node) {
    const e = node.arith || {};
    const op = ['+', '-', '*', '/', '^'].indexOf(e.op) >= 0 ? e.op : '+';
    const p = op === '+' || op === '-' ? 5 : (op === '*' || op === '/' ? 6 : 7);
    return [sub(e.a, p, false, op === '^') + ' ' + op + ' ' + sub(e.b, p, true, op === '^'), p];
  }
  if ('img_eq' in node) {
    const d = node.img_eq || {};
    const args = [_mfm_render_path(d.a || ''), _mfm_render_path(d.b || '')];
    if (d.neq) args.push('neq');
    return ['img_eq(' + args.join(', ') + ')', 9];
  }
  if ('img_on_screen' in node) {
    const d = node.img_on_screen || {};
    const args = [_mfm_render_path(d.path || ''),
                  _mfm_fmt_num(d.threshold === null || d.threshold === undefined ? 85 : d.threshold)];
    const box = [d.search_x1, d.search_y1, d.search_x2, d.search_y2];
    if (box.every(function (v) { return v !== null && v !== undefined; }))
      box.forEach(function (v) { args.push(_mfm_coord_render(v)); });
    return ['img_on_screen(' + args.join(', ') + ')', 9];
  }
  if ('color_eq' in node) {
    const d = node.color_eq || {};
    const rgba = (d.rgba && d.rgba.length) ? d.rgba : [255, 255, 255, 255];
    const args = [_mfm_coord_render(d.x, 0), _mfm_coord_render(d.y, 0)];
    rgba.forEach(function (v) { args.push(_mfm_fmt_num(v)); });
    args.push(_mfm_fmt_num(d.tol === null || d.tol === undefined ? 10 : d.tol));
    return ['color_eq(' + args.join(', ') + ')', 9];
  }
  if ('res_spec' in node) {
    const d = node.res_spec || {};
    const args = ['rw', 'rh', 'dw', 'dh'].map(function (k) {
      return sub((d[k] === null || d[k] === undefined) ? { lit: 0 } : d[k], 9, false);
    });
    return ['ratio(' + args.join(', ') + ')', 9];
  }
  if ('point' in node) {
    const d = node.point || {};
    return ['point(' + sub(d.x || { lit: 0 }, 9, false) + ', ' + sub(d.y || { lit: 0 }, 9, false) + ')', 9];
  }
  if ('box' in node) {
    const d = node.box || {};
    const args = ['x1', 'y1', 'x2', 'y2'].map(function (k) {
      return sub((d[k] === null || d[k] === undefined) ? { lit: 0 } : d[k], 9, false);
    });
    return ['box(' + args.join(', ') + ')', 9];
  }
  if ('grab' in node) {
    const d = node.grab || {};
    if ('w' in d || 'x' in d) {
      const args = ['x', 'y', 'w', 'h'].map(function (k) {
        const v = (d[k] === null || d[k] === undefined) ? 0 : d[k];
        return (v && typeof v === 'object') ? sub(v, 9, false) : _mfm_fmt_num(parseInt(v, 10) || 0);
      });
      return ['grab_at(' + args.join(', ') + ')', 9];
    }
    const args = ['search_x1', 'search_y1', 'search_x2', 'search_y2'].map(function (k) {
      const v = (d[k] === null || d[k] === undefined) ? 0 : d[k];
      return (v && typeof v === 'object') ? sub(v, 9, false) : _mfm_fmt_num(parseInt(v, 10) || 0);
    });
    return ['grab(' + args.join(', ') + ')', 9];
  }
  if ('screen_color' in node) {
    const d = node.screen_color || {};
    const args = ['x', 'y'].map(function (k) {
      const v = (d[k] === null || d[k] === undefined) ? 0 : d[k];
      return (v && typeof v === 'object') ? sub(v, 9, false) : _mfm_fmt_num(parseInt(v, 10) || 0);
    });
    return ['screen_color(' + args.join(', ') + ')', 9];
  }
  if ('res_scale' in node) {
    const d = node.res_scale || {};
    const a = sub((d.a === null || d.a === undefined) ? { lit: true } : d.a, 9, false);
    if (d.spec !== null && d.spec !== undefined)
      return ['scale(' + a + ', ' + sub(d.spec, 9, false) + ')', 9];
    return ['scale(' + a + ')', 9];
  }
  if ('color_diff' in node) {
    const d = node.color_diff || {};
    return ['color_diff(' + sub(d.a || { lit: '#FFFFFF' }, 9, false) + ', ' +
      sub(d.b || { lit: '#FFFFFF' }, 9, false) + ')', 9];
  }
  if ('img_diff' in node) {
    const d = node.img_diff || {};
    return ['img_diff(' + _mfm_render_path(d.a || '') + ', ' + _mfm_render_path(d.b || '') + ')', 9];
  }
  return ['true', 9];
}
function _mfm_coord_render(v, dflt) {
  if (v !== null && v !== undefined && typeof v === 'object') return _mfm_render(v)[0];
  return _mfm_fmt_num(v === null || v === undefined ? (dflt || 0) : v);
}
function _mfm_render_path(p) {
  if (p !== null && p !== undefined && typeof p === 'object') {
    if ('get' in p) return _mfm_render({ get: p.get })[0];
    return _mfm_render(p)[0];
  }
  return _mfm_render({ lit: p })[0];
}
function _mfm_expr_text(node) { return _mfm_render(node)[0]; }

// Value block -> composed text, the .macro convention the runner's ${}
// substitution reads: text literals inline, variable getters as ${var},
// numbers/booleans inline, and everything else — "create text with"
// parts like image/color checks, screen reads, arithmetic — rendered in
// the engine's expression syntax inside ${…} (evaluated at playback).
function _mfm_value_text(c) {
  if (!c) return '';
  if (c.type === 'text') return String(c.getFieldValue('TEXT') || '');
  if (c.type === 'text_join') {
    let out = '';
    const n = Number(c.itemCount_ || 0);
    for (let i = 0; i < n; i++) out += _mfm_value_text(c.getInputTargetBlock('ADD' + i));
    return out;
  }
  if (c.type === 'pcr_get_text' || c.type === 'pcr_get_number' ||
      c.type === 'pcr_get_logic' || c.type === 'pcr_get_image' ||
      c.type === 'pcr_get_color' || c.type === 'pcr_get_resloc') {
    return '${' + String(c.getFieldValue('VAR') || '') + '}';
  }
  if (c.type === 'math_number') return String(c.getFieldValue('NUM') || '0');
  if (c.type === 'logic_boolean') return c.getFieldValue('BOOL') === 'TRUE' ? 'true' : 'false';
  // any other value block — serialize the expression node and render it
  return '${' + _mfm_expr_text(_mfm_expr(c)) + '}';
}

function _mfm_num(block, inputName, def) {
  const v = block.getInputTargetBlock ? block.getInputTargetBlock(inputName) : null;
  if (v && v.type === 'math_number') return String(v.getFieldValue('NUM'));
  const field = block.getField && block.getField(inputName);
  if (field) return String(block.getFieldValue(inputName));
  return def === undefined ? '0' : String(def);
}

function _mfm_point(block, inputName) {
  const v = block.getInputTargetBlock(inputName);
  if (v && v.type === 'pcr_point_xy') {
    return _mfm_num(v, 'X') + ',' + _mfm_num(v, 'Y');
  }
  return '0,0';
}

// ratio block -> [rw, rh, dw, dh] number strings (default 16:9 @ 1920x1080)
function _mfm_res_spec_vals(c) {
  if (c && c.type === 'pcr_res_ratio') {
    return [_mfm_num(c, 'RW', 16), _mfm_num(c, 'RH', 9), _mfm_num(c, 'DW', 1920), _mfm_num(c, 'DH', 1080)];
  }
  return ['16', '9', '1920', '1080'];
}

// scale block -> flat "scale(x, y, rw, rh, dw, dh)" coord text
// (only for point inputs — what MOUSE_MOVE_ABS consumes)
function _mfm_scale_point_text(c) {
  if (!c || c.type !== 'pcr_scale_res') return '';
  const inp = c.getInputTargetBlock('INPUT');
  if (!inp || inp.type !== 'pcr_point_xy') return '';
  return 'scale(' + [_mfm_num(inp, 'X', 0), _mfm_num(inp, 'Y', 0)]
    .concat(_mfm_res_spec_vals(c.getInputTargetBlock('DEFAULT'))).join(', ') + ')';
}

// path text from a pcr_image_from_res PATH socket (1:1 with its mfPathText)
// path from a pcr_image_from_res child on any socket — or an image
// VARIABLE (pcr_get_image), which serializes as a {get: name} expression.
// Returns '' | <path string> | {get: <var name>}.
function _mfm_img_path_socket(block, inputName) {
  const c = block && block.getInputTargetBlock ? block.getInputTargetBlock(inputName) : null;
  if (c && c.type === 'pcr_image_from_res') return _mfm_image_path(c);
  if (c && c.type === 'pcr_get_image') return { get: String(c.getFieldValue('VAR') || '') };
  if (c && c.type === 'mfm_grab_image') return _mfm_expr(c);   // {grab: …}
  return '';
}
// same lookup for an already-resolved child block
function _mfm_image_socket_value(c) {
  if (!c) return '';
  if (c.type === 'pcr_image_from_res') return _mfm_image_path(c);
  if (c.type === 'pcr_get_image') return { get: String(c.getFieldValue('VAR') || '') };
  if (c.type === 'mfm_grab_image') return _mfm_expr(c);   // {grab: …}
  return '';
}

// a size/coord socket as number or expression tree (get-number, arith…)
function _mfm_num_expr(block, inputName) {
  const c = block.getInputTargetBlock(inputName);
  if (!c) return 0;
  if (c.type === 'math_number') return Number(c.getFieldValue('NUM')) || 0;
  return _mfm_expr(c);
}

// legacy {grab:{search_…}} payloads (2.1.208) → point/size numbers.
// Scaled boxes carry the base coords inside the {res_scale} point literal.
function _mfm_grab_legacy_coords(d) {
  function num(v, key) {
    if (v == null) return null;
    if (typeof v === 'number') return Number(v) || 0;
    try {
      const pt = v.res_scale && v.res_scale.a && v.res_scale.a.point;
      return pt && pt[key] && Number(pt[key].lit) || 0;
    } catch (e) { return null; }
  }
  const x1 = num(d.search_x1, 'x'), y1 = num(d.search_y1, 'y');
  const x2 = num(d.search_x2, 'x'), y2 = num(d.search_y2, 'y');
  if (x1 == null || y1 == null || x2 == null || y2 == null) return null;
  return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
}

function _mfm_point_vals(block, inputName) {
  const p = block.getInputTargetBlock(inputName);
  if (p && p.type === 'pcr_point_xy') return [_mfm_num(p, 'X', 0), _mfm_num(p, 'Y', 0)];
  return [0, 0];
}

function _mfm_rgba_vals(block, inputName) {
  const c = block.getInputTargetBlock(inputName);
  if (c && c.type === 'pcr_color_rgba') {
    return [_mfm_num(c, 'R', 255), _mfm_num(c, 'G', 255), _mfm_num(c, 'B', 255), _mfm_num(c, 'A', 255)];
  }
  return [255, 255, 255, 255];
}

// expression tree from a value/data block (the expanded .macro format)
function _mfm_expr(b) {
  if (!b) return { lit: true };
  switch (b.type) {
    case 'math_number': return { lit: Number(b.getFieldValue('NUM')) || 0 };
    case 'text': return { lit: String(b.getFieldValue('TEXT') || '') };
    case 'logic_boolean': return { lit: b.getFieldValue('BOOL') === 'TRUE' };
    case 'pcr_get_number': case 'pcr_get_text': case 'pcr_get_logic':
    case 'pcr_get_image': case 'pcr_get_resloc': case 'pcr_get_color':
      return { get: String(b.getFieldValue('VAR') || '') };
    case 'pcr_image_from_res':
      return { lit: _mfm_image_path(b) };
    case 'mfm_grab_image': {
      let raw = {};
      try { raw = JSON.parse(b.mfmRawPayload || '{}'); } catch (e) { raw = {}; }
      const d = Object.assign({}, raw);   // preserves unknown payload keys
      // the old region form (2.1.208) is gone — point + size only
      delete d.fixed; delete d.search_x1; delete d.search_y1;
      delete d.search_x2; delete d.search_y2;
      const pc = b.getInputTargetBlock('POINT');
      if (pc && pc.type === 'pcr_scale_res') {
        // scaled point: x/y both carry the {res_scale} node; the engine
        // evaluates it once per coord and picks element 0 / 1
        const t = _mfm_expr(pc);
        d.x = t; d.y = t;
      } else {
        const p = _mfm_point_vals(b, 'POINT');
        d.x = Number(p[0]) || 0; d.y = Number(p[1]) || 0;
      }
      const sz = b.getInputTargetBlock('SIZE');
      if (sz && sz.type === 'pcr_box_xyxy') {
        // size box: X1/Y1 stay 0 — width = X2, height = Y2 (numbers or exprs).
        // A CORNER-style box (non-zero numeric X1/Y1 — e.g. the one the
        // image block's meta-drop icon drops with the picked region) means
        // X2/Y2 are the bottom-right corner, not w/h: convert to
        // width/height so the grab matches the picked crop pixel-for-pixel.
        const x1 = _mfm_num_expr(sz, 'X1'), y1 = _mfm_num_expr(sz, 'Y1');
        const x2 = _mfm_num_expr(sz, 'X2'), y2 = _mfm_num_expr(sz, 'Y2');
        if (typeof x1 === 'number' && typeof y1 === 'number' &&
            typeof x2 === 'number' && typeof y2 === 'number' &&
            (x1 !== 0 || y1 !== 0)) {
          d.w = Math.max(1, Math.round(Math.abs(x2 - x1)));
          d.h = Math.max(1, Math.round(Math.abs(y2 - y1)));
        } else {
          d.w = x2;
          d.h = y2;
        }
      }
      return { grab: d };
    }
    case 'mfm_grab_color': {
      const pc = b.getInputTargetBlock('POINT');
      if (pc && pc.type === 'pcr_scale_res') {
        const t = _mfm_expr(pc);
        return { screen_color: { x: t, y: t } };
      }
      const p = _mfm_point_vals(b, 'POINT');
      return { screen_color: { x: Number(p[0]) || 0, y: Number(p[1]) || 0 } };
    }
    case 'pcr_res_location':
      return { lit: _mfm_str(b, 'PATH', '') };
    case 'pcr_color_hex':
      return { lit: String(b.getFieldValue('HEX') || '#FFFFFF') };
    // resolution blocks — 1:1 with the flow editor (ratio / scale)
    case 'pcr_point_xy':
      return { point: { x: { lit: Number(_mfm_num(b, 'X', 0)) || 0 }, y: { lit: Number(_mfm_num(b, 'Y', 0)) || 0 } } };
    case 'pcr_box_xyxy':
      return { box: { x1: { lit: Number(_mfm_num(b, 'X1', 0)) || 0 }, y1: { lit: Number(_mfm_num(b, 'Y1', 0)) || 0 },
                     x2: { lit: Number(_mfm_num(b, 'X2', 0)) || 0 }, y2: { lit: Number(_mfm_num(b, 'Y2', 0)) || 0 } } };
    case 'pcr_res_ratio':
      return { res_spec: { rw: { lit: Number(_mfm_num(b, 'RW', 16)) || 16 }, rh: { lit: Number(_mfm_num(b, 'RH', 9)) || 9 },
                           dw: { lit: Number(_mfm_num(b, 'DW', 1920)) || 1920 }, dh: { lit: Number(_mfm_num(b, 'DH', 1080)) || 1080 } } };
    case 'pcr_scale_res': {
      const specChild = b.getInputTargetBlock('DEFAULT');
      return { res_scale: { a: _mfm_expr(b.getInputTargetBlock('INPUT')), spec: specChild ? _mfm_expr(specChild) : null } };
    }
    case 'pcr_color_rgba': {
      const r = Math.round(Number(_mfm_num(b, 'R')) || 0), g = Math.round(Number(_mfm_num(b, 'G')) || 0),
            bl = Math.round(Number(_mfm_num(b, 'B')) || 0), a = Math.round(Number(_mfm_num(b, 'A')) || 255);
      return { lit: 'rgba(' + r + ',' + g + ',' + bl + ',' + a + ')' };
    }
    case 'pcr_compare_number': case 'pcr_compare_text': case 'pcr_compare_logic':
    case 'pcr_compare_color':
      return { cmp: { op: b.getFieldValue('OP') || 'EQ', a: _mfm_expr(b.getInputTargetBlock('A')), b: _mfm_expr(b.getInputTargetBlock('B')) } };
    case 'pcr_compare_image':
      return { img_eq: { a: _mfm_img_path_socket(b, 'A'), b: _mfm_img_path_socket(b, 'B'), neq: b.getFieldValue('OP') === 'NEQ' } };
    // pcr_color_diff / pcr_img_diff — 1:1 with the flow editor's blocks
    // (definition comes in via /blockly/blocks_data); the macro engine
    // evaluates them as {color_diff}/{img_diff} expression nodes.
    case 'pcr_color_diff':
      return { color_diff: { a: _mfm_expr(b.getInputTargetBlock('COLOR1')), b: _mfm_expr(b.getInputTargetBlock('COLOR2')) } };
    case 'pcr_img_diff':
      return { img_diff: { a: _mfm_img_path_socket(b, 'IMG1'), b: _mfm_img_path_socket(b, 'IMG2') } };
    case 'mfm_image_on_screen': {
      const d = { path: _mfm_img_path_socket(b, 'IMAGE'), threshold: Number(_mfm_num(b, 'THRESH', 85)) || 85 };
      const box = b.getInputTargetBlock('REGION');
      if (box && box.type === 'pcr_scale_res') {
        // scaled search box: all four coords carry the {res_scale} node
        const t = _mfm_expr(box);
        d.search_x1 = t; d.search_y1 = t; d.search_x2 = t; d.search_y2 = t;
      } else if (box && box.type === 'pcr_box_xyxy') {
        d.search_x1 = Number(_mfm_num(box, 'X1')) || 0;
        d.search_y1 = Number(_mfm_num(box, 'Y1')) || 0;
        d.search_x2 = Number(_mfm_num(box, 'X2')) || 0;
        d.search_y2 = Number(_mfm_num(box, 'Y2')) || 0;
      }
      return { img_on_screen: d };
    }
    case 'mfm_color_check': {
      const pc = b.getInputTargetBlock('POINT');
      if (pc && pc.type === 'pcr_scale_res') {
        // scaled point: x/y both carry the {res_scale} node; the engine
        // evaluates it once per coord and picks element 0 / 1
        const t = _mfm_expr(pc);
        return { color_eq: { x: t, y: t, rgba: _mfm_rgba_vals(b, 'RGBA'), tol: Number(_mfm_num(b, 'TOL', 10)) || 0 } };
      }
      const p = _mfm_point_vals(b, 'POINT');
      return { color_eq: { x: Number(p[0]) || 0, y: Number(p[1]) || 0, rgba: _mfm_rgba_vals(b, 'RGBA'), tol: Number(_mfm_num(b, 'TOL', 10)) || 0 } };
    }
    case 'logic_operation':
      return b.getFieldValue('OP') === 'OR'
        ? { or: { a: _mfm_expr(b.getInputTargetBlock('A')), b: _mfm_expr(b.getInputTargetBlock('B')) } }
        : { and: { a: _mfm_expr(b.getInputTargetBlock('A')), b: _mfm_expr(b.getInputTargetBlock('B')) } };
    case 'logic_negate':
      return { not: _mfm_expr(b.getInputTargetBlock('BOOL')) };
    case 'math_arithmetic': {
      const ops = { ADD: '+', MINUS: '-', MULTIPLY: '*', DIVIDE: '/', POWER: '^' };
      return { arith: { op: ops[b.getFieldValue('OP')] || '+', a: _mfm_expr(b.getInputTargetBlock('A')), b: _mfm_expr(b.getInputTargetBlock('B')) } };
    }
    default: return { lit: true };
  }
}

// path value ('' | string | {get}) → pcr_image_from_res(+text) or pcr_get_image
function mfmImageXml(pathValue, doc) {
  function mkBlk(t) { const e = doc.createElement('block'); e.setAttribute('type', t); return e; }
  if (pathValue && typeof pathValue === 'object' && !pathValue.grab && !pathValue.get && 'lit' in pathValue) {
    pathValue = pathValue.lit;   // {lit: "res://a.png"} expr node → raw path
  }
  if (pathValue && typeof pathValue === 'object' && pathValue.grab) {
    return _mfm_exprXml(pathValue, doc);   // get-image-of-box value block
  }
  if (pathValue && typeof pathValue === 'object' && pathValue.get) {
    const b = mkBlk('pcr_get_image');
    const f = doc.createElement('field'); f.setAttribute('name', 'VAR');
    f.textContent = String(pathValue.get); b.appendChild(f); return b;
  }
  const img = mkBlk('pcr_image_from_res');
  const wv = doc.createElement('value'); wv.setAttribute('name', 'PATH');
  const t = mkBlk('text'); const tf = doc.createElement('field');
  tf.setAttribute('name', 'TEXT'); tf.textContent = pathValue || ''; t.appendChild(tf);
  wv.appendChild(t); img.appendChild(wv); return img;
}

// reverse: expression tree → block XML (editor blocks 1:1)
function _mfm_condExpr(payload) {
    let d = {};
    try { d = JSON.parse(payload || '{}'); } catch (e) { d = {}; }
    if (d.expr) return d.expr;
    if (d.mode === 'number') {
      return { cmp: { op: d.op || '>=', a: { get: d.name || '' }, b: { lit: Number(d.value) || 0 } } };
    }
    return { cmp: { op: 'EQ', a: { get: d.name || '' }, b: { lit: d.value !== false } } };
  }

// {lit: n} | n → number with default
function _exprLitNum(v, dflt) {
  if (v && typeof v === 'object') return Number(v.lit !== undefined ? v.lit : dflt) || dflt;
  return Number(v) || dflt || 0;
}

function _mfm_exprXml(v, doc) {
  function mkBlk(t) { const e = doc.createElement('block'); e.setAttribute('type', t); return e; }
  function mkImageXml(pathValue, doc2) { return mfmImageXml(pathValue, doc2); }
  function mkNumVal(name, val) {
    const w = doc.createElement('value'); w.setAttribute('name', name);
    const n = mkBlk('math_number'); const f = doc.createElement('field');
    f.setAttribute('name', 'NUM'); f.textContent = String(val); n.appendChild(f);
    w.appendChild(n); return w;
  }
  function mkExprVal(name, exprNode, docArg) {
    // a socket filled with a non-number expression (get-number, arith…)
    const w = doc.createElement('value'); w.setAttribute('name', name);
    w.appendChild(_mfm_exprXml(exprNode, docArg || doc));
    return w;
  }
  function mkLit(lit) {
    if (typeof lit === 'boolean') {
      const b = mkBlk('logic_boolean');
      const f = doc.createElement('field'); f.setAttribute('name', 'BOOL');
      f.textContent = lit ? 'TRUE' : 'FALSE'; b.appendChild(f); return b;
    }
    if (typeof lit === 'string') {
      const b = mkBlk('text');
      const f = doc.createElement('field'); f.setAttribute('name', 'TEXT');
      f.textContent = lit; b.appendChild(f); return b;
    }
    const b = mkBlk('math_number');
    const f = doc.createElement('field'); f.setAttribute('name', 'NUM');
    f.textContent = String(Number(lit) || 0); b.appendChild(f); return b;
  }

  if (v && typeof v === 'object' && !Array.isArray(v)) {
    if ('lit' in v) return mkLit(v.lit);
    if ('get' in v) {
      const t = (window._pcrLocalVars || {})[v.get] || 'number';
      const b = mkBlk(t === 'text' ? 'pcr_get_text' : t === 'logic' ? 'pcr_get_logic'
        : t === 'image' ? 'pcr_get_image' : t === 'resloc' ? 'pcr_get_resloc'
        : t === 'color' ? 'pcr_get_color' : 'pcr_get_number');
      const f = doc.createElement('field'); f.setAttribute('name', 'VAR');
      f.textContent = String(v.get); b.appendChild(f); return b;
    }
    if ('cmp' in v) {
      const a = v.cmp.a || { lit: 0 }, bb = v.cmp.b || { lit: 0 };
      const lv = window._pcrLocalVars || {};
      const isText = typeof (a.lit) === 'string' || typeof (bb.lit) === 'string'
        || lv[a.get] === 'text' || lv[bb.get] === 'text';
      const isLogic = typeof (a.lit) === 'boolean' || typeof (bb.lit) === 'boolean'
        || lv[a.get] === 'logic' || lv[bb.get] === 'logic';
      // color operands (#hex / rgba() literals or color vars) rebuild as the
      // color compare block — text stays text
      const _isColorLit = function (x) { return typeof x.lit === 'string' && /^(#[0-9a-fA-F]{3,8}|rgba?\()/.test(x.lit); };
      const isColor = lv[a.get] === 'color' || lv[bb.get] === 'color' || _isColorLit(a) || _isColorLit(bb);
      const b = mkBlk(isColor ? 'pcr_compare_color' : isText ? 'pcr_compare_text' : isLogic ? 'pcr_compare_logic' : 'pcr_compare_number');
      const f = doc.createElement('field'); f.setAttribute('name', 'OP');
      f.textContent = v.cmp.op || 'EQ'; b.appendChild(f);
      const va = doc.createElement('value'); va.setAttribute('name', 'A');
      va.appendChild(_mfm_exprXml(a, doc)); b.appendChild(va);
      const vb = doc.createElement('value'); vb.setAttribute('name', 'B');
      vb.appendChild(_mfm_exprXml(bb, doc)); b.appendChild(vb);
      return b;
    }
    if ('and' in v || 'or' in v) {
      const isOr = 'or' in v; const e = v[isOr ? 'or' : 'and'];
      const b = mkBlk('logic_operation');
      const f = doc.createElement('field'); f.setAttribute('name', 'OP');
      f.textContent = isOr ? 'OR' : 'AND'; b.appendChild(f);
      const va = doc.createElement('value'); va.setAttribute('name', 'A');
      va.appendChild(_mfm_exprXml(e.a || { lit: true }, doc)); b.appendChild(va);
      const vb = doc.createElement('value'); vb.setAttribute('name', 'B');
      vb.appendChild(_mfm_exprXml(e.b || { lit: true }, doc)); b.appendChild(vb);
      return b;
    }
    if ('not' in v) {
      const b = mkBlk('logic_negate');
      const w = doc.createElement('value'); w.setAttribute('name', 'BOOL');
      w.appendChild(_mfm_exprXml(v.not || { lit: true }, doc)); b.appendChild(w);
      return b;
    }
    if ('arith' in v) {
      const b = mkBlk('math_arithmetic');
      const map = { '+': 'ADD', '-': 'MINUS', '*': 'MULTIPLY', '/': 'DIVIDE', '^': 'POWER' };
      const f = doc.createElement('field'); f.setAttribute('name', 'OP');
      f.textContent = map[v.arith.op] || 'ADD'; b.appendChild(f);
      const va = doc.createElement('value'); va.setAttribute('name', 'A');
      va.appendChild(_mfm_exprXml(v.arith.a || { lit: 0 }, doc)); b.appendChild(va);
      const vb = doc.createElement('value'); vb.setAttribute('name', 'B');
      vb.appendChild(_mfm_exprXml(v.arith.b || { lit: 0 }, doc)); b.appendChild(vb);
      return b;
    }
    // resolution blocks — 1:1 with the flow editor (ratio / scale)
    if ('res_spec' in v) {
      const d = v.res_spec || {};
      const b = mkBlk('pcr_res_ratio');
      b.appendChild(mkNumVal('RW', _exprLitNum(d.rw, 16)));
      b.appendChild(mkNumVal('RH', _exprLitNum(d.rh, 9)));
      b.appendChild(mkNumVal('DW', _exprLitNum(d.dw, 1920)));
      b.appendChild(mkNumVal('DH', _exprLitNum(d.dh, 1080)));
      return b;
    }
    if ('point' in v) {
      const d = v.point || {};
      const b = mkBlk('pcr_point_xy');
      b.appendChild(mkNumVal('X', _exprLitNum(d.x, 0)));
      b.appendChild(mkNumVal('Y', _exprLitNum(d.y, 0)));
      return b;
    }
    if ('box' in v) {
      const d = v.box || {};
      const b = mkBlk('pcr_box_xyxy');
      b.appendChild(mkNumVal('X1', _exprLitNum(d.x1, 0)));
      b.appendChild(mkNumVal('Y1', _exprLitNum(d.y1, 0)));
      b.appendChild(mkNumVal('X2', _exprLitNum(d.x2, 0)));
      b.appendChild(mkNumVal('Y2', _exprLitNum(d.y2, 0)));
      return b;
    }
    if ('res_scale' in v) {
      const d = v.res_scale || {};
      const b = mkBlk('pcr_scale_res');
      const iv = doc.createElement('value'); iv.setAttribute('name', 'INPUT');
      iv.appendChild(_mfm_exprXml(d.a != null ? d.a : { lit: true }, doc));
      b.appendChild(iv);
      if (d.spec != null) {
        const dv = doc.createElement('value'); dv.setAttribute('name', 'DEFAULT');
        dv.appendChild(_mfm_exprXml(d.spec, doc));
        b.appendChild(dv);
      }
      return b;
    }
    if ('img_eq' in v) {
      const b = mkBlk('pcr_compare_image');
      const f = doc.createElement('field'); f.setAttribute('name', 'OP');
      f.textContent = v.img_eq.neq ? 'NEQ' : 'EQ'; b.appendChild(f);
      ['a', 'b'].forEach(function (k) {
        const w = doc.createElement('value'); w.setAttribute('name', k.toUpperCase());
        w.appendChild(mkImageXml(v.img_eq[k], doc)); b.appendChild(w);
      });
      return b;
    }
    if ('img_on_screen' in v) {
      const d = v.img_on_screen || {};
      const b = mkBlk('mfm_image_on_screen');
      const w = doc.createElement('value'); w.setAttribute('name', 'IMAGE');
      w.appendChild(mkImageXml(d.path, doc)); b.appendChild(w);
      b.appendChild(mkNumVal('THRESH', d.threshold != null ? d.threshold : 85));
      if (d.search_x1 != null) {
        const rv = doc.createElement('value'); rv.setAttribute('name', 'REGION');
        if (d.search_x1 && typeof d.search_x1 === 'object') {
          // scaled search box ({res_scale} node) — rebuild the scale block
          rv.appendChild(_mfm_exprXml(d.search_x1, doc));
        } else {
          const rb = mkBlk('pcr_box_xyxy');
          rb.appendChild(mkNumVal('X1', d.search_x1)); rb.appendChild(mkNumVal('Y1', d.search_y1 || 0));
          rb.appendChild(mkNumVal('X2', d.search_x2 || 0)); rb.appendChild(mkNumVal('Y2', d.search_y2 || 0));
          rv.appendChild(rb);
        }
        b.appendChild(rv);
      }
      return b;
    }
    if ('grab' in v) {
      let d = v.grab || {};
      let x = d.x, y = d.y, w = d.w, h = d.h;
      if (x == null && w == null) {
        // legacy region form (2.1.208) → point + size (best effort, 1:1
        // when the coords are plain numbers or scale-literal boxes)
        const lc = _mfm_grab_legacy_coords(d);
        d = Object.assign({}, d);
        delete d.fixed; delete d.search_x1; delete d.search_y1;
        delete d.search_x2; delete d.search_y2;
        x = lc ? lc.x : 0; y = lc ? lc.y : 0;
        w = lc ? lc.w : 0; h = lc ? lc.h : 0;
        d.x = x; d.y = y; d.w = w; d.h = h;
      }
      const b = mkBlk('mfm_grab_image');
      const mut = doc.createElement('mutation');
      mut.setAttribute('raw', JSON.stringify(d));
      b.appendChild(mut);
      const pv = doc.createElement('value'); pv.setAttribute('name', 'POINT');
      if (x && typeof x === 'object') {
        // scaled point ({res_scale} node) — rebuild the scale block
        pv.appendChild(_mfm_exprXml(x, doc));
      } else {
        const pt = mkBlk('pcr_point_xy');
        pt.appendChild(mkNumVal('X', x || 0)); pt.appendChild(mkNumVal('Y', y || 0));
        pv.appendChild(pt);
      }
      b.appendChild(pv);
      const sv = doc.createElement('value'); sv.setAttribute('name', 'SIZE');
      const sb = mkBlk('pcr_box_xyxy');
      sb.appendChild(mkNumVal('X1', 0)); sb.appendChild(mkNumVal('Y1', 0));
      if (w && typeof w === 'object') sb.appendChild(mkExprVal('X2', w, doc));
      else sb.appendChild(mkNumVal('X2', w || 0));
      if (h && typeof h === 'object') sb.appendChild(mkExprVal('Y2', h, doc));
      else sb.appendChild(mkNumVal('Y2', h || 0));
      sv.appendChild(sb);
      b.appendChild(sv);
      return b;
    }
    if ('screen_color' in v) {
      const d = v.screen_color || {};
      const b = mkBlk('mfm_grab_color');
      const mut = doc.createElement('mutation');
      mut.setAttribute('raw', JSON.stringify(d));
      b.appendChild(mut);
      const pv = doc.createElement('value'); pv.setAttribute('name', 'POINT');
      if (d.x && typeof d.x === 'object') {
        // scaled point ({res_scale} node) — rebuild the scale block
        pv.appendChild(_mfm_exprXml(d.x, doc));
      } else {
        const pt = mkBlk('pcr_point_xy');
        pt.appendChild(mkNumVal('X', d.x || 0)); pt.appendChild(mkNumVal('Y', d.y || 0));
        pv.appendChild(pt);
      }
      b.appendChild(pv);
      return b;
    }
    if ('color_eq' in v) {
      const d = v.color_eq || {};
      const b = mkBlk('mfm_color_check');
      const pw = doc.createElement('value'); pw.setAttribute('name', 'POINT');
      if (d.x && typeof d.x === 'object') {
        // scaled point ({res_scale} node) — rebuild the scale block
        pw.appendChild(_mfm_exprXml(d.x, doc));
      } else {
        const pt = mkBlk('pcr_point_xy');
        pt.appendChild(mkNumVal('X', d.x || 0)); pt.appendChild(mkNumVal('Y', d.y || 0));
        pw.appendChild(pt);
      }
      b.appendChild(pw);
      const cw = doc.createElement('value'); cw.setAttribute('name', 'RGBA');
      const ca = mkBlk('pcr_color_rgba');
      const rgba = d.rgba || [255, 255, 255, 255];
      ca.appendChild(mkNumVal('R', rgba[0])); ca.appendChild(mkNumVal('G', rgba[1]));
      ca.appendChild(mkNumVal('B', rgba[2])); ca.appendChild(mkNumVal('A', rgba[3]));
      cw.appendChild(ca); b.appendChild(cw);
      b.appendChild(mkNumVal('TOL', d.tol || 0));
      return b;
    }
    // color value -> pcr_color_hex / pcr_color_rgba / pcr_get_color
    function mkColor(v) {
      if (v && typeof v === 'object' && 'get' in v) {
        const gb = mkBlk('pcr_get_color');
        const f = doc.createElement('field'); f.setAttribute('name', 'VAR');
        f.textContent = String(v.get); gb.appendChild(f); return gb;
      }
      const lit = (v && typeof v === 'object' && 'lit' in v) ? v.lit : null;
      const s = typeof lit === 'string' ? lit.replace(/\s+/g, '') : '';
      const m = /^rgba?\((\d+),(\d+),(\d+)(?:,(\d+))?\)$/.exec(s);
      if (m) {
        const ca = mkBlk('pcr_color_rgba');
        ca.appendChild(mkNumVal('R', +m[1])); ca.appendChild(mkNumVal('G', +m[2]));
        ca.appendChild(mkNumVal('B', +m[3])); ca.appendChild(mkNumVal('A', m[4] != null ? +m[4] : 255));
        return ca;
      }
      if (/^#[0-9a-fA-F]{3,8}$/.test(s)) {
        const hb = mkBlk('pcr_color_hex');
        const f = doc.createElement('field'); f.setAttribute('name', 'HEX');
        f.textContent = s; hb.appendChild(f); return hb;
      }
      return _mfm_exprXml(v, doc);
    }
    if ('color_diff' in v) {
      const d = v.color_diff || {};
      const b = mkBlk('pcr_color_diff');
      ['a', 'b'].forEach(function (k) {
        const w = doc.createElement('value'); w.setAttribute('name', k === 'a' ? 'COLOR1' : 'COLOR2');
        w.appendChild(mkColor(d[k] || { lit: '#FFFFFF' })); b.appendChild(w);
      });
      return b;
    }
    if ('img_diff' in v) {
      const d = v.img_diff || {};
      const b = mkBlk('pcr_img_diff');
      ['a', 'b'].forEach(function (k) {
        const w = doc.createElement('value'); w.setAttribute('name', k === 'a' ? 'IMG1' : 'IMG2');
        w.appendChild(mkImageXml(d[k], doc)); b.appendChild(w);
      });
      return b;
    }
    return mkLit(true);
  }
  if (typeof v === 'boolean') return mkLit(v);
  if (typeof v === 'number') return mkLit(v);
  return mkLit(String(v));
}

function _mfm_image_path(img) {
  const input = img.getInput('PATH');
  if (!input || !input.connection) return '';
  const child = input.connection.targetBlock();
  if (!child) return '';
  if (child.type === 'text') return String(child.getFieldValue('TEXT') || '');
  if (child.type === 'pcr_res_location') {
    const inner = child.getInput && child.getInput('PATH');
    if (inner && inner.connection) {
      const ic = inner.connection.targetBlock();
      if (ic && ic.type === 'text') return String(ic.getFieldValue('TEXT') || '');
    }
    return '';
  }
  return '';
}

function _mfm_str(block, inputName, def) {
  const v = block.getInputTargetBlock(inputName);
  if (v && v.type === 'text') return v.getFieldValue('TEXT');
  return def || '';
}

function _mfm_cond(block) {
  const data = {
    mode: block.getFieldValue('MODE') || 'boolean',
    name: block.getFieldValue('NAME') || '',
    value: true,
  };
  if (data.mode === 'number') {
    data.op = block.getFieldValue('OP') || '>=';
    data.value = Number(block.getFieldValue('VAL') || 0);
  } else {
    data.value = (block.getFieldValue('BOOLVAL') !== 'false');
  }
  return JSON.stringify(data);
}

// Flat block list → Blockly XML (then domToWorkspace).
// Returns {dom, unknown: n} for reporting.
function mfmListToXml(blocks) {
  const xml = document.createElement('xml');
  let unknown = 0;
  const stacks = [{ dom: xml, locked: false }]; // container dom stack

  function _mfm_getterXml(name) {
    // getter typed by the local-variables rail — a number var gets
    // pcr_get_number etc., so the dropdown always accepts it
    const t = (window._pcrLocalVars || {})[name] || 'number';
    const type = t === 'text' ? 'pcr_get_text'
      : t === 'logic' ? 'pcr_get_logic'
      : t === 'image' ? 'pcr_get_image'
      : t === 'color' ? 'pcr_get_color'
      : t === 'resloc' ? 'pcr_get_resloc'
      : 'pcr_get_number';
    const gb = mk(type);
    addField(gb, 'VAR', name);
    return gb;
  }

  function addField(el, name, value) {
    const f = document.createElement('field');
    f.setAttribute('name', name);
    f.textContent = String(value);
    el.appendChild(f);
  }
  function addShadowNum(el, inputName, value) {
    const v = document.createElement('value');
    v.setAttribute('name', inputName);
    const sh = document.createElement('block');
    sh.setAttribute('type', 'math_number');
    addField(sh, 'NUM', value);
    v.appendChild(sh);
    el.appendChild(v);
  }
  function addShadowPoint(el, inputName, x, y) {
    const v = document.createElement('value');
    v.setAttribute('name', inputName);
    const sh = document.createElement('block');
    sh.setAttribute('type', 'pcr_point_xy');
    const vi = document.createElement('value');
    vi.setAttribute('name', 'X');
    const shx = document.createElement('block');
    shx.setAttribute('type', 'math_number');
    addField(shx, 'NUM', x);
    vi.appendChild(shx);
    sh.appendChild(vi);
    const vj = document.createElement('value');
    vj.setAttribute('name', 'Y');
    const shy = document.createElement('block');
    shy.setAttribute('type', 'math_number');
    addField(shy, 'NUM', y);
    vj.appendChild(shy);
    sh.appendChild(vj);
    v.appendChild(sh);
    el.appendChild(v);
  }
  function addShadowText(el, inputName, text) {
    const v = document.createElement('value');
    v.setAttribute('name', inputName);
    const sh = document.createElement('block');
    sh.setAttribute('type', 'text');
    addField(sh, 'TEXT', text);
    v.appendChild(sh);
    el.appendChild(v);
  }
  function addShadowKey(el, inputName, key) {
    const v = document.createElement('value');
    v.setAttribute('name', inputName);
    const sh = document.createElement('block');
    sh.setAttribute('type', 'pcr_key');
    addField(sh, 'KEY', key);
    v.appendChild(sh);
    el.appendChild(v);
  }
  function addShadowMouse(el, inputName, btn) {
    const v = document.createElement('value');
    v.setAttribute('name', inputName);
    const sh = document.createElement('block');
    sh.setAttribute('type', 'pcr_mouse');
    addField(sh, 'BUTTON', btn);
    v.appendChild(sh);
    el.appendChild(v);
  }

  function mk(type) {
    const b = document.createElement('block');
    b.setAttribute('type', type);
    return b;
  }
  function appendTo(parentDom, el) {
    // chain into <next> of the TAIL block of the last chain
    const last = parentDom.lastElementChild;
    if (last && last.tagName.toLowerCase() === 'block') {
      // walk down: block > next > block > next ... to the deepest block
      let tail = last, nx = null;
      for (;;) {
        const n = tail.querySelector(':scope > next');
        if (n && n.firstElementChild && n.firstElementChild.tagName.toLowerCase() === 'block') {
          tail = n.firstElementChild;
        } else { nx = n; break; }
      }
      if (!nx) { nx = document.createElement('next'); tail.appendChild(nx); }
      nx.appendChild(el);
    } else {
      parentDom.appendChild(el);
    }
  }


  // ── Group accumulation: steps inside a group never reach the canvas ──
  // They are kept as raw {type, value, locked} items in the group block's
  // data; the popup editor rebuilds them with this same function (and
  // mfmWorkspaceToList flattens them back out between the GROUP markers).
  // Nested GROUP markers inside a group are stored verbatim as raw items —
  // the popup then shows a real Group block inside.
  const groupStack = [];   // each: {steps: [], el, depth: 0}
  const ifStack = [];      // open controls_if: {el, branches, hasElse}
  const awaitingBg = [];   // controls_whileUntil blocks whose BG_BEGIN arm hasn't arrived yet

  // ── Lock reconstruction ──────────────────────────────────────────
  // New format: a visible LOCK { ... } envelope (LOCK:/LOCK_END: markers)
  // becomes a real mfm_lock whose statement is pushed as a container on
  // `stacks` — Groups, IFs and everything else inside the envelope then
  // nest into it naturally (a flag only caught plain statements, so a
  // Group inside a Lock escaped the envelope and autosave then wrote it
  // out of the lock).
  // Old format: consecutive locked lines (# LOCKED: indices) wrap the
  // same way via lockBuf.
  let lockBuf = [];
  let cur = null;   // current container (live-read by flushLock)
  function flushLock() {
    if (!lockBuf.length) return;
    const lockEl = mk('mfm_lock');
    const st = document.createElement('statement');
    st.setAttribute('name', 'DO');
    lockBuf.forEach(function (e, i) { if (i === 0) st.appendChild(e); else appendTo(st, e); });
    lockEl.appendChild(st);
    appendTo(cur.dom, lockEl);
    lockBuf = [];
  }

  const _items = blocks || [];
  for (let _bi = 0; _bi < _items.length; _bi++) {
    const item = _items[_bi];
    const type = String((item && item.type) || '').trim();
    const value = String((item && item.value) != null ? item.value : '');
    const locked = !!(item && item.locked);
    cur = stacks[stacks.length - 1];

    // LOCK { ... } envelope — statement container on stacks, so nested
    // Groups/IFs stay INSIDE the lock (empty lock round-trips too)
    if (type === 'LOCK') {
      flushLock();
      if (groupStack.length) {
        groupStack[groupStack.length - 1].steps.push({ type: 'LOCK', value: '', locked: locked });
      } else {
        const lockEl = mk('mfm_lock');
        const st = document.createElement('statement');
        st.setAttribute('name', 'DO');
        lockEl.appendChild(st);
        appendTo(cur.dom, lockEl);
        stacks.push({ dom: st, locked: true });
      }
      continue;
    }
    if (type === 'LOCK_END') {
      if (groupStack.length) {
        groupStack[groupStack.length - 1].steps.push({ type: 'LOCK_END', value: '', locked: false });
      } else if (stacks.length > 1) {
        stacks.pop();   // close the lock container
      }
      continue;
    }
    // GROUP opens a container (on the canvas) or nests (inside one)
    if (type === 'GROUP') {
      flushLock();
      if (groupStack.length) {
        groupStack[groupStack.length - 1].steps.push({ type: 'GROUP', value: value, locked: locked });
        groupStack[groupStack.length - 1].depth++;
      } else {
        const gel = mk('mfm_group');
        addField(gel, 'NAME', value);
        appendTo(cur.dom, gel);
        groupStack.push({ steps: [], el: gel, depth: 0 });
      }
      continue;
    }
    // GROUP_END closes the innermost container (or a raw nested marker)
    if (type === 'GROUP_END') {
      flushLock();
      if (groupStack.length) {
        const top = groupStack[groupStack.length - 1];
        if (top.depth > 0) {
          top.depth--;
          top.steps.push({ type: 'GROUP_END', value: '', locked: false });
        } else {
          groupStack.pop();
          const mut = document.createElement('mutation');
          try { mut.setAttribute('steps', JSON.stringify(top.steps)); }
          catch (e) { mut.setAttribute('steps', '[]'); }
          top.el.appendChild(mut);
        }
      }
      // stray GROUP_END outside any group: ignored
      continue;
    }
    // COMMENT renders as a light one-liner block
    if (type === 'COMMENT') {
      const cel = mk('mfm_comment');
      addField(cel, 'TEXT', value);
      if (groupStack.length) {
        groupStack[groupStack.length - 1].steps.push({ type: 'COMMENT', value: value, locked: locked });
      } else if (locked) {
        lockBuf.push(cel);
      } else {
        flushLock();
        appendTo(cur.dom, cel);
      }
      continue;
    }
    // inside a group: raw data item — no canvas block is created
    if (groupStack.length) {
      groupStack[groupStack.length - 1].steps.push({ type: type, value: value, locked: locked });
      continue;
    }

    function mkStatementChild(type_) {
      const holder = document.createElement('statement');
      holder.setAttribute('name', 'DO');
      const el = mk(type_);
      holder.appendChild(el);
      const parentBlock = cur.dom.tagName.toLowerCase() === 'block' ? cur.dom : cur.dom.lastElementChild;
      parentBlock.appendChild(holder);
      return el;
    }

    let el = null;
    // BOT-COMPAT — kept as Raw: image checks, IF/ELSE_IF/ELSE/END_IF
    // condition lines, SET_VARIABLE assignments, GRAB_IMAGE shots and
    // VARIABLE declarations carry runtime payloads the bot's plain macro
    // runner executes directly (its own schema), but this visual editor
    // cannot represent them 1:1 — rebuilding them as editable blocks
    // would silently rewrite their payloads into a different schema the
    // bot cannot run. So they load as Raw blocks instead: TYPE and VALUE
    // are preserved verbatim, they save back byte-for-byte, and the bot
    // keeps executing them exactly as before. Everything else stays 1:1.
    if (type === 'IF' || type === 'ELSE_IF' || type === 'ELSE' || type === 'END_IF' ||
        type === 'SET_VARIABLE' || type === 'IMAGE' || type === 'GRAB_IMAGE' ||
        type === 'VARIABLE') {
      el = mk('mfm_raw');
      addField(el, 'TYPE', type);
      addField(el, 'VALUE', value);
      unknown++;
    } else switch (type) {
      case 'DELAY': {
        el = mk('mfm_delay');
        addShadowNum(el, 'MS', value);
        break;
      }
      case 'PRINT': {
        el = mk('mfm_print');
        const tw = document.createElement('value'); tw.setAttribute('name', 'TEXT');
        const s = value || '';
        // ${…} occurrences that are full expressions come pre-parsed from
        // the server (step.exprs: occurrence index → node) — they rebuild
        // as real value blocks; plain ${var} refs stay the getter path
        const exprs = (item && item.exprs && typeof item.exprs === 'object') ? item.exprs : null;
        const pm = /^\$\{([^}]*)\}$/.exec(s.trim());
        if (pm) {
          // one single ref/expression — wrap it in a 1-item "create text
          // with": the print socket only takes String (text/text_join),
          // a bare getter or value block would be rejected on load
          const node = exprs ? exprs[0] : null;
          const jb = mk('text_join');
          const mut = document.createElement('mutation');
          mut.setAttribute('items', '1');
          jb.appendChild(mut);
          const vw = document.createElement('value'); vw.setAttribute('name', 'ADD0');
          if (node) vw.appendChild(_mfm_exprXml(node, document));
          else vw.appendChild(_mfm_getterXml(pm[1]));
          jb.appendChild(vw);
          tw.appendChild(jb);
        } else if (/\$\{[^}]*\}/.test(s)) {
          // mixed literals + ${} refs — rebuild "create text with"
          // (text_join) so every part stays an editable block
          const re = /\$\{([^}]*)\}/g;
          const parts = [];
          let last = 0, m, ri = 0;
          while ((m = re.exec(s))) {
            if (m.index > last) parts.push({ t: 'lit', v: s.slice(last, m.index) });
            const node = exprs ? exprs[ri] : null;
            parts.push(node ? { t: 'expr', v: node } : { t: 'var', v: m[1] });
            last = m.index + m[0].length; ri++;
          }
          if (last < s.length) parts.push({ t: 'lit', v: s.slice(last) });
          const jb = mk('text_join');
          const mut = document.createElement('mutation');
          mut.setAttribute('items', String(parts.length));
          jb.appendChild(mut);
          parts.forEach(function (p, i) {
            const vw = document.createElement('value'); vw.setAttribute('name', 'ADD' + i);
            if (p.t === 'var') vw.appendChild(_mfm_getterXml(p.v));
            else if (p.t === 'expr') vw.appendChild(_mfm_exprXml(p.v, document));
            else { const tb = mk('text'); addField(tb, 'TEXT', p.v); vw.appendChild(tb); }
            jb.appendChild(vw);
          });
          tw.appendChild(jb);
        } else {
          const tb = mk('text');
          addField(tb, 'TEXT', s);
          tw.appendChild(tb);
        }
        el.appendChild(tw);
        break;
      }
      case 'REPEAT': {
        flushLock();
        el = mk('mfm_repeat');
        addShadowNum(el, 'TIMES', value);
        const st = document.createElement('statement');
        st.setAttribute('name', 'DO');
        const inner = mk('mfm_raw_dummy'); // placeholder removed below
        st.appendChild(inner);
        el.appendChild(st);
        inner.remove();
        // open container: statement dom = st
        appendTo(cur.dom, el);
        stacks.push({ dom: st, locked: cur.locked || locked });
        continue;
      }
      case 'ENDREPEAT': {
        flushLock();
        if (stacks.length > 1) stacks.pop();
        cur = stacks[stacks.length - 1];
        continue;
      }
      case 'WHILE':
      case 'UNTIL': {
        // default Blockly controls_whileUntil (same block the flow
        // procedures use): "repeat [while/until] <cond> do []" — gains a
        // BACKGROUND arm via its own mutator whenever this loop's END
        // marker is followed by a BG_BEGIN arm.
        flushLock();
        if (groupStack.length) {
          groupStack[groupStack.length - 1].steps.push({ type: type, value: value, locked: locked });
        } else {
          // nesting-aware scan: does this loop's END marker get followed
          // by a BG_BEGIN arm?
          let d2 = 1, e2 = _bi + 1, hasBg = false;
          for (; e2 < _items.length; e2++) {
            const t2 = String((_items[e2] && _items[e2].type) || '').trim();
            if (t2 === 'WHILE' || t2 === 'UNTIL') d2++;
            else if (t2 === 'END_WHILE' || t2 === 'END_UNTIL') { d2--; if (d2 === 0) break; }
          }
          if (e2 < _items.length && e2 + 1 < _items.length &&
              String((_items[e2 + 1] && _items[e2 + 1].type) || '').trim() === 'BG_BEGIN') {
            hasBg = true;
          }
          el = mk('controls_whileUntil');
          addField(el, 'MODE', type);            // WHILE / UNTIL dropdown
          const cw = document.createElement('value'); cw.setAttribute('name', 'BOOL');
          cw.appendChild(_mfm_exprXml(_mfm_condExpr(value), document));
          el.appendChild(cw);
          if (hasBg) {
            const mu = document.createElement('mutation');
            mu.setAttribute('hasbg', '1');
            el.appendChild(mu);
          }
          const st = document.createElement('statement');
          st.setAttribute('name', 'DO');
          el.appendChild(st);
          appendTo(cur.dom, el);
          stacks.push({ dom: st, locked: cur.locked || locked });
          if (hasBg) awaitingBg.push(el);
        }
        continue;
      }
      case 'BG_BEGIN': {
        flushLock();
        if (groupStack.length) {
          groupStack[groupStack.length - 1].steps.push({ type: type, value: value, locked: locked });
        } else {
          // arm of the most recent controls_whileUntil (with hasbg): its steps render into the
          // block's BACKGROUND statement (END already popped the DO stack)
          const bel = awaitingBg.pop();
          if (bel) {
            const bSt = document.createElement('statement');
            bSt.setAttribute('name', 'BACKGROUND');
            bel.appendChild(bSt);
            stacks.push({ dom: bSt, locked: cur.locked || locked });
          }
        }
        continue;
      }
      case 'BG_END': {
        flushLock();
        if (groupStack.length) {
          groupStack[groupStack.length - 1].steps.push({ type: type, value: '', locked: false });
        } else if (stacks.length > 1) {
          stacks.pop();
          cur = stacks[stacks.length - 1];
        }
        continue;
      }
      case 'END_WHILE':
      case 'END_UNTIL': {
        flushLock();
        if (groupStack.length) {
          groupStack[groupStack.length - 1].steps.push({ type: type, value: '', locked: false });
        } else if (stacks.length > 1) {
          stacks.pop();
          cur = stacks[stacks.length - 1];
        }
        continue;
      }
      case 'SECTION': {
        flushLock();
        el = mk('mfm_section');
        addField(el, 'TEXT', value);
        const st = document.createElement('statement');
        st.setAttribute('name', 'DO');
        el.appendChild(st);
        appendTo(cur.dom, el);
        stacks.push({ dom: st, locked: cur.locked || locked });
        continue;
      }
      case 'SECTION_END': {
        flushLock();
        if (stacks.length > 1) stacks.pop();
        cur = stacks[stacks.length - 1];
        continue;
      }
      case 'LABEL': {
        el = mk('mfm_label');
        addField(el, 'NAME', value);
        break;
      }
      case 'GOTO': {
        el = mk('mfm_goto');
        addField(el, 'NAME', value);
        break;
      }
      case 'PLAY_MACRO': {
        el = mk('mfm_play_macro');
        addShadowText(el, 'PATH', value);
        break;
      }
      case 'IF': {
        // default Blockly controls_if (same block the flow procedures use,
        // mutator gear included) — IF/ELSE_IF/ELSE/END_IF lines fold into
        // ONE block with the matching mutation.
        flushLock();
        el = mk('controls_if');
        ifStack.push({ el: el, branches: 0, hasElse: false });
        const cw = document.createElement('value'); cw.setAttribute('name', 'IF0');
        cw.appendChild(_mfm_exprXml(_mfm_condExpr(value), document));
        el.appendChild(cw);
        const st = document.createElement('statement');
        st.setAttribute('name', 'DO0');
        el.appendChild(st);
        appendTo(cur.dom, el);
        stacks.push({ dom: st, locked: cur.locked || locked });
        continue;
      }
      case 'ELSE_IF': {
        const ifs = ifStack[ifStack.length - 1];
        if (ifs) {
          const outerLocked = stacks.length > 1 ? stacks[stacks.length - 2].locked : false;
          if (stacks.length > 1) stacks.pop();
          ifs.branches++;
          const cw = document.createElement('value'); cw.setAttribute('name', 'IF' + ifs.branches);
          cw.appendChild(_mfm_exprXml(_mfm_condExpr(value), document));
          ifs.el.appendChild(cw);
          const st = document.createElement('statement');
          st.setAttribute('name', 'DO' + ifs.branches);
          ifs.el.appendChild(st);
          stacks.push({ dom: st, locked: outerLocked });
          continue;
        }
        break;   // stray ELSE_IF (no open IF) → falls to raw below
      }
      case 'ELSE': {
        const ifs = ifStack[ifStack.length - 1];
        if (ifs && !ifs.hasElse) {
          const outerLocked = stacks.length > 1 ? stacks[stacks.length - 2].locked : false;
          if (stacks.length > 1) stacks.pop();
          ifs.hasElse = true;
          const st = document.createElement('statement');
          st.setAttribute('name', 'ELSE');
          ifs.el.appendChild(st);
          stacks.push({ dom: st, locked: outerLocked });
          continue;
        }
        break;
      }
      case 'LABEL': {
        el = mk('mfm_label');
        addField(el, 'NAME', value);
        break;
      }
      case 'GOTO': {
        el = mk('mfm_goto');
        addField(el, 'NAME', value);
        break;
      }
      case 'PLAY_MACRO': {
        el = mk('mfm_play_macro');
        addShadowText(el, 'PATH', value);
        break;
      }
      case 'END_IF': {
        flushLock();
        const ifs = ifStack.pop();
        if (ifs) {
          const mut = document.createElement('mutation');
          if (ifs.branches > 0) mut.setAttribute('elseif', String(ifs.branches));
          if (ifs.hasElse) mut.setAttribute('else', '1');
          ifs.el.appendChild(mut);
        }
        if (stacks.length > 1) stacks.pop();
        cur = stacks[stacks.length - 1];
        continue;
      }
      case 'VARIABLE': {
        // declarations live in the local-variables rail (1:1 with the editor)
        try {
          const d = JSON.parse(value || '{}');
          const raw = String(d.var_type || 'number').toLowerCase();
          const t = raw === 'boolean' ? 'logic' : raw === 'text' ? 'text'
            : raw === 'image' ? 'image' : raw === 'resloc' ? 'resloc'
            : raw === 'color' ? 'color' : 'number';
          window._pcrLocalVars = window._pcrLocalVars || {};
          window._pcrLocalVars[d.name || ''] = t;
        } catch (e) {}
        break;
      }
      case 'SET_VARIABLE': {
        let d = {};
        try { d = JSON.parse(value || '{}'); } catch (e) { d = {}; }
        const t = (window._pcrLocalVars || {})[d.name] || 'number';
        if (t === 'color') {
          el = mk('pcr_set_color');
          addField(el, 'VAR', d.name || '');
          const w = document.createElement('value'); w.setAttribute('name', 'VALUE');
          const v = d.value !== undefined ? d.value : {};
          if (v && typeof v === 'object' && (v.get || v.screen_color)) {
            w.appendChild(_mfm_exprXml(v, document));
          } else {
            const hx = mk('pcr_color_hex');
            addField(hx, 'HEX', (v && typeof v === 'object' ? (v.lit !== undefined ? v.lit : '') : v) || '#FFFFFF');
            w.appendChild(hx);
          }
          el.appendChild(w);
          break;
        }
        if (t === 'image' || t === 'resloc') {
          el = mk(t === 'image' ? 'pcr_set_image' : 'pcr_set_resloc');
          addField(el, 'VAR', d.name || '');
          const w = document.createElement('value'); w.setAttribute('name', 'VALUE');
          const v = d.value !== undefined ? d.value : {};
          if (v && typeof v === 'object' && (v.get || v.grab)) {
            w.appendChild(_mfm_exprXml(v, document));
          } else if (t === 'image') {
            w.appendChild(mfmImageXml(typeof v === 'object' ? (v.lit !== undefined ? v.lit : '') : v, document));
          } else {
            // resloc: wrap the path in the editor's pcr_res_location
            const rl = mk('pcr_res_location');
            const pw = document.createElement('value'); pw.setAttribute('name', 'PATH');
            const pt2 = mk('text');
            addField(pt2, 'TEXT', typeof v === 'object' ? (v.lit !== undefined ? v.lit : '') : v);
            pw.appendChild(pt2); rl.appendChild(pw);
            w.appendChild(rl);
          }
          el.appendChild(w);
          break;
        }
        el = mk(t === 'text' ? 'pcr_set_text' : t === 'logic' ? 'pcr_set_logic' : 'pcr_set_number');
        addField(el, 'VAR', d.name || '');
        const w = document.createElement('value'); w.setAttribute('name', 'VALUE');
        w.appendChild(_mfm_exprXml(d.value !== undefined ? d.value : 0, document));
        el.appendChild(w);
        break;
      }
      case 'IMAGE': {
        el = mk('mfm_image_check');
        let d = {};
        try { d = JSON.parse(value || '{}'); } catch (e) { d = {}; }
        const mut = document.createElement('mutation');   // raw payload round-trip
        mut.setAttribute('raw', value || '{}');
        el.appendChild(mut);
        addField(el, 'VAR', d.var || 'image_found');
        addField(el, 'MODE', d.result_mode || 'bool');
        addShadowNum(el, 'THRESH', d.threshold != null ? d.threshold : 85);
        const iv = document.createElement('value');
        iv.setAttribute('name', 'IMAGE');
        iv.appendChild(mfmImageXml(d.path, document));
        el.appendChild(iv);
        const sx = [d.search_x1, d.search_y1, d.search_x2, d.search_y2];
        if (sx.some(function (v) { return v != null; })) {
          const rv = document.createElement('value');
          rv.setAttribute('name', 'REGION');
          if (sx[0] && typeof sx[0] === 'object') {
            // scaled search region ({res_scale} node) — rebuild the scale block
            rv.appendChild(_mfm_exprXml(sx[0], document));
          } else {
            const bx = mk('pcr_box_xyxy');
            addShadowNum(bx, 'X1', sx[0] != null ? sx[0] : 0);
            addShadowNum(bx, 'Y1', sx[1] != null ? sx[1] : 0);
            addShadowNum(bx, 'X2', sx[2] != null ? sx[2] : 1920);
            addShadowNum(bx, 'Y2', sx[3] != null ? sx[3] : 1080);
            rv.appendChild(bx);
          }
          el.appendChild(rv);
        }
        break;
      }
      case 'GRAB_IMAGE': {
        // legacy statement (2.1.208) — upgraded 1:1 when the file passes
        // through the editor: SET <var> = grab(...). Playback of the
        // hand-written line still works via the engine's GRAB_IMAGE support.
        let d = {};
        try { d = JSON.parse(value || '{}'); } catch (e) { d = {}; }
        el = mk('pcr_set_image');
        addField(el, 'VAR', d.var || 'screen_shot');
        const w = document.createElement('value'); w.setAttribute('name', 'VALUE');
        w.appendChild(_mfm_exprXml({ grab: d }, document));
        el.appendChild(w);
        break;
      }
      case 'SMOOTH_MOVE': case 'LOOK': {
        el = mk('mfm_scaled_move');
        const parts = value.split(',').map(function (s) { return s.trim(); });
        addShadowPoint(el, 'POINT', parts[0] || '0', parts[1] || '0');
        addField(el, 'MS', parts[2] || 0);
        break;
      }
      case 'MOUSE_MOVE_ABS': {
        el = mk('mfm_abs_move');
        const sv = value.trim();
        if (sv.startsWith('scale(')) {
          // scale(x, y, rw, rh, dw, dh) — rebuild the 1:1 scale block
          const args = sv.slice(6, -1).split(',').map(function (s) { return s.trim(); });
          if (args.length >= 6) {
            const sc = mk('pcr_scale_res');
            const iv = document.createElement('value'); iv.setAttribute('name', 'INPUT');
            const ip = mk('pcr_point_xy');
            addShadowNum(ip, 'X', args[0]); addShadowNum(ip, 'Y', args[1]);
            iv.appendChild(ip); sc.appendChild(iv);
            const dv = document.createElement('value'); dv.setAttribute('name', 'DEFAULT');
            const rr = mk('pcr_res_ratio');
            addShadowNum(rr, 'RW', args[2]); addShadowNum(rr, 'RH', args[3]);
            addShadowNum(rr, 'DW', args[4]); addShadowNum(rr, 'DH', args[5]);
            dv.appendChild(rr); sc.appendChild(dv);
            const pv = document.createElement('value'); pv.setAttribute('name', 'POINT');
            pv.appendChild(sc); el.appendChild(pv);
            break;
          }
        }
        const parts = value.split(',').map(function (s) { return s.trim(); });
        addShadowPoint(el, 'POINT', parts[0] || '0', parts[1] || '0');
        break;
      }
      case 'MOUSE_LEFT_CLICK': case 'MOUSE_RIGHT_CLICK': case 'MOUSE_MIDDLE_CLICK': {
        el = mk('mfm_click');
        addShadowMouse(el, 'BUTTON', type === 'MOUSE_LEFT_CLICK' ? 'left' : (type === 'MOUSE_RIGHT_CLICK' ? 'right' : 'middle'));
        break;
      }
      case 'MOUSE_LEFT_DOWN': case 'MOUSE_RIGHT_DOWN': case 'MOUSE_MIDDLE_DOWN': {
        el = mk('mfm_mouse_down');
        addShadowMouse(el, 'BUTTON', type.endsWith('LEFT_DOWN') ? 'left' : (type.endsWith('RIGHT_DOWN') ? 'right' : 'middle'));
        break;
      }
      case 'MOUSE_LEFT_UP': case 'MOUSE_RIGHT_UP': case 'MOUSE_MIDDLE_UP': {
        el = mk('mfm_mouse_up');
        addShadowMouse(el, 'BUTTON', type.endsWith('LEFT_UP') ? 'left' : (type.endsWith('RIGHT_UP') ? 'right' : 'middle'));
        break;
      }
      case 'KEY_DOWN': case 'KEY_UP': case 'KEY_PRESS': {
        let vk = parseInt(value, 16);
        const keyName = MFM_VK_NAME[vk];
        if (keyName) {
          el = mk(type === 'KEY_DOWN' ? 'mfm_key_down' : (type === 'KEY_UP' ? 'mfm_key_up' : 'mfm_press_key'));
          addShadowKey(el, 'KEY', keyName);
        } else {
          el = mk('mfm_raw');
          addField(el, 'TYPE', type);
          addField(el, 'VALUE', value);
          unknown++;
        }
        break;
      }
      default: {
        if (!type) continue;
        el = mk('mfm_raw');
        addField(el, 'TYPE', type);
        addField(el, 'VALUE', value);
        unknown++;
        break;
      }
    }

    if (locked && el && el.tagName.toLowerCase() === 'block') {
      lockBuf.push(el);        // locked statement — may join a Lock run
    } else {
      flushLock();
      if (el) appendTo(cur.dom, el);
    }
  }

  flushLock();
  return { dom: xml, unknown: unknown };
}

// Blockly workspace → flat block list. includeLocals=false (the group
// popup) skips the local-variables rail — group data must only contain
// the steps themselves.
// ── embedded workspace (.macro dual format) ──────────────────────────────
// Blockly's own JSON serialization of the whole workspace — layout,
// arrangement, and group data (a group's mfmSteps ride inside its
// mutation/extraState). Embedded in the .macro header on save, reloaded
// verbatim on open: the editor reopens EXACTLY what was saved.
function mfmWorkspaceToJson(ws) {
  try { return Blockly.serialization.workspaces.save(ws); }
  catch (e) { return null; }
}

// The workspace as Blockly XML — what the v3 .macro container stores as
// blockly.xaml. This is the 1:1 fidelity format: every block position,
// stray stack, group bubble, mutator arm and note comment round-trips.
function mfmWorkspaceToXml(ws) {
  try { return Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(ws)); }
  catch (e) { return null; }
}

function mfmWorkspaceToList(workspace, includeLocals) {
  const out = [];

  function push(type, value, locked) {
    out.push({ type: type, value: value === undefined ? '' : String(value), locked: !!locked });
  }

  // legacy recorder payload → expression tree (old macros keep loading)
  function condData(block) {
    return JSON.stringify({ expr: _mfm_expr(block.getInputTargetBlock('COND')) });
  }
  // controls_if branch (IF0..IFn) → same payload shape
  function branchCond(b, inputName) {
    return JSON.stringify({ expr: _mfm_expr(b.getInputTargetBlock(inputName)) });
  }

  function emitStack(first, locked) {
    let b = first;
    while (b) {
      if (b.type === 'controls_if') {
        // default Blockly if: one block covers IF + ELSE_IF* + ELSE
        let bi = 0;
        while (b.getInput('IF' + bi)) {
          push(bi === 0 ? 'IF' : 'ELSE_IF', branchCond(b, 'IF' + bi), locked);
          emitStack(b.getInputTargetBlock('DO' + bi), locked);
          bi++;
        }
        if (b.getInput('ELSE')) {
          push('ELSE', '', locked);
          emitStack(b.getInputTargetBlock('ELSE'), locked);
        }
        push('END_IF', '', locked);
        b = b.getNextBlock();
      } else if (b.type === 'controls_whileUntil') {
        // while/until: mode dropdown decides the markers. DO body first,
        // then — if the mutator gear added a background arm — the arm
        // steps right after the END marker (they run on a background
        // thread until the loop exits).
        const mode = String(b.getFieldValue('MODE') || 'WHILE').toUpperCase() === 'UNTIL' ? 'UNTIL' : 'WHILE';
        push(mode, branchCond(b, 'BOOL'), locked);
        emitStack(b.getInputTargetBlock('DO'), locked);
        push(mode === 'UNTIL' ? 'END_UNTIL' : 'END_WHILE', '', locked);
        if (b.getInputTargetBlock('BACKGROUND')) {
          push('BG_BEGIN', '', locked);
          emitStack(b.getInputTargetBlock('BACKGROUND'), locked);
          push('BG_END', '', locked);
        }
        b = b.getNextBlock();
      } else if (b.type === 'mfm_section') {
        push('SECTION', b.getFieldValue('TEXT') || 'note', locked);
        emitStack(b.getInputTargetBlock('DO'), locked);
        push('SECTION_END', '', locked);
        b = b.getNextBlock();
      } else if (b.type === 'mfm_if') {
        // legacy chained custom if (workspaces built before controls_if)
        push('IF', condData(b), locked);
        emitStack(b.getInputTargetBlock('DO'), locked);
        let n = b.getNextBlock();
        while (n && n.type === 'mfm_elseif') {
          push('ELSE_IF', condData(n), locked);
          emitStack(n.getInputTargetBlock('DO'), locked);
          n = n.getNextBlock();
        }
        push('END_IF', '', locked);
        b = n;
      } else if (b.type === 'mfm_elseif') {
        b = b.getNextBlock(); // stray else-if (no open if) — skip
      } else {
        emitBlock(b, locked);
        b = b.getNextBlock();
      }
    }
  }

  function emitBlock(b, locked) {
    switch (b.type) {
      case 'mfm_delay':
        push('DELAY', _mfm_num(b, 'MS'), locked);
        break;
      case 'mfm_print': {
        // one composed text: literals inline, ${var} refs for getters,
        // "create text with" recursion — numbers etc. become text
        push('PRINT', _mfm_value_text(b.getInputTargetBlock('TEXT')), locked);
        break;
      }
      case 'mfm_repeat': {
        push('REPEAT', _mfm_num(b, 'TIMES'), locked);
        emitStack(b.getInputTargetBlock('DO'), locked);
        push('ENDREPEAT', '', locked);
        break;
      }
      case 'mfm_label':
        push('LABEL', b.getFieldValue('NAME'), locked);
        break;
      case 'mfm_goto':
        push('GOTO', b.getFieldValue('NAME'), locked);
        break;
      case 'mfm_play_macro':
        push('PLAY_MACRO', _mfm_str(b, 'PATH', ''), locked);
        break;
      case 'mfm_lock': {
        // visible LOCK { ... } envelope in the file — F5 re-record keeps
        // everything between the markers (contents carry no flags)
        push('LOCK', '', locked);
        emitStack(b.getInputTargetBlock('DO'), false);
        push('LOCK_END', '', locked);
        break;
      }
      case 'pcr_set_number': case 'pcr_set_text': case 'pcr_set_logic':
      case 'pcr_set_image': case 'pcr_set_resloc': case 'pcr_set_color': {
        const d = { name: b.getFieldValue('VAR') || '', value: _mfm_expr(b.getInputTargetBlock('VALUE')) };
        push('SET_VARIABLE', JSON.stringify(d), locked);
        break;
      }
      case 'mfm_image_check': {
        let raw = {};
        try { raw = JSON.parse(b.mfmRawPayload || '{}'); } catch (e) { raw = {}; }
        const d = Object.assign({}, raw);   // preserves x1..y2 / base_w etc. from recorded payloads
        d.var = b.getFieldValue('VAR') || '';
        d.result_mode = b.getFieldValue('MODE') || 'bool';
        d.threshold = Number(_mfm_num(b, 'THRESH', 85)) || 85;
        const img = b.getInputTargetBlock('IMAGE');
        const imgVal = _mfm_image_socket_value(img);
        d.path = (imgVal !== '') ? imgVal : (raw.path || '');
        const box = b.getInputTargetBlock('REGION');
        if (box && box.type === 'pcr_scale_res') {
          // scaled search region: all four coords carry the {res_scale} node
          const t = _mfm_expr(box);
          d.fixed = false;
          d.search_x1 = t; d.search_y1 = t; d.search_x2 = t; d.search_y2 = t;
        } else if (box && box.type === 'pcr_box_xyxy') {
          d.fixed = false;
          d.search_x1 = Number(_mfm_num(box, 'X1')) || 0;
          d.search_y1 = Number(_mfm_num(box, 'Y1')) || 0;
          d.search_x2 = Number(_mfm_num(box, 'X2')) || 0;
          d.search_y2 = Number(_mfm_num(box, 'Y2')) || 0;
        }
        push('IMAGE', JSON.stringify(d), locked);
        break;
      }
      case 'mfm_scaled_move': {
        const pt = _mfm_point(b, 'POINT');
        const ms = Number(b.getFieldValue('MS')) || 0;
        push('SMOOTH_MOVE', ms > 0 ? pt + ',' + ms : pt, locked);
        break;
      }
      case 'mfm_abs_move': {
        const sc = _mfm_scale_point_text(b.getInputTargetBlock('POINT'));
        push('MOUSE_MOVE_ABS', sc || _mfm_point(b, 'POINT'), locked);
        break;
      }
      case 'mfm_click': {
        var mb = _mfmSocketKey(b, 'BUTTON') || 'left';
        push('MOUSE_' + (mb === 'right' ? 'RIGHT' : (mb === 'middle' ? 'MIDDLE' : 'LEFT')) + '_CLICK', '', locked);
        break;
      }
      case 'mfm_mouse_down': {
        var md = _mfmSocketKey(b, 'BUTTON') || 'left';
        push('MOUSE_' + (md === 'right' ? 'RIGHT' : (md === 'middle' ? 'MIDDLE' : 'LEFT')) + '_DOWN', '', locked);
        break;
      }
      case 'mfm_mouse_up': {
        var mu = _mfmSocketKey(b, 'BUTTON') || 'left';
        push('MOUSE_' + (mu === 'right' ? 'RIGHT' : (mu === 'middle' ? 'MIDDLE' : 'LEFT')) + '_UP', '', locked);
        break;
      }
      case 'mfm_key_down': case 'mfm_key_up': case 'mfm_press_key': {
        const vk = MFM_KEY_VK[_mfmSocketKey(b, 'KEY')] || 0x41;
        push(b.type === 'mfm_key_down' ? 'KEY_DOWN' : (b.type === 'mfm_key_up' ? 'KEY_UP' : 'KEY_PRESS'), vk.toString(16), locked);
        break;
      }
      case 'mfm_raw':
        push(b.getFieldValue('TYPE') || 'UNKNOWN', b.getFieldValue('VALUE') || '', locked);
        break;
      case 'mfm_comment':
        push('COMMENT', b.getFieldValue('TEXT') || '', locked);
        break;
      case 'mfm_group': {
        push('GROUP', b.getFieldValue('NAME') || 'recording', locked);
        (b.mfmSteps || []).forEach(function (s) {
          if (!s || !s.type) return;
          out.push({ type: String(s.type), value: s.value === undefined ? '' : String(s.value), locked: !!s.locked });
        });
        push('GROUP_END', '', locked);
        break;
      }
      default:
        break; // unknown block type in workspace — skip
    }
  }

  // declared locals (the rail) first — like recorded macros declaring vars up top
  if (includeLocals !== false) {
    const locals = window._pcrLocalVars || {};
    Object.keys(locals).forEach(function (name) {
      const t = locals[name];
      const d = { name: name,
                  var_type: t === 'logic' ? 'boolean' : t === 'text' ? 'text'
                    : t === 'image' ? 'image' : t === 'resloc' ? 'resloc'
                    : t === 'color' ? 'color' : 'number',
                  value: t === 'logic' ? false : (t === 'text' || t === 'image' || t === 'resloc' || t === 'color') ? '' : 0 };
      push('VARIABLE', JSON.stringify(d));
    });
  }

  // ONLY hat-connected blocks are written: a stray top-level stack
  // floating on the canvas (dragged out, failed plug, leftover) is NOT
  // part of the macro and must never reach the .macro file.
  for (const top of workspace.getTopBlocks(true)) {
    if (top.type === 'mfm_hat' || top.type === 'mfm_group_hat') {
      emitStack(top.getInputTargetBlock('DO'), false);   // the cap is the entry point
    }
  }
  return out;
}

// ensure the hat exists exactly once; returns it (called after inject/load)
// hatType: 'mfm_hat' (main canvas) or 'mfm_group_hat' (group edit window)
function mfmEnsureHat(workspace, name, hatType) {
  hatType = hatType || 'mfm_hat';
  let hat = null;
  for (const top of workspace.getTopBlocks(true)) {
    if (top.type === hatType) {
      if (!hat) hat = top;
      else top.dispose();
    }
  }
  if (!hat) {
    hat = workspace.newBlock(hatType);
    hat.initSvg();
    hat.moveBy(24, 24);
    hat.render();
  }
  if (name) {
    try { hat.setFieldValue(String(name), 'NAME'); } catch (e) {}
  }
  return hat;
}
