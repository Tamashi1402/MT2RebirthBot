// ╔══════════════════════════════════════════════════════╗
// ║ Block: GUI element STUDIO                             ║
// ║ Category: GUI (popup-only inner blocks + creators)    ║
// ║ Desc: Every "Add <element>" block is a MINIMAL        ║
// ║ block: gui, id, x/y, anchor (+ scale where real).    ║
// ║ Click ✎ edit → its own editor window opens (group-    ║
// ║ style) with PER-ELEMENT categories on the left:       ║
// ║ fonts, colors, borders, behavior, events... FULL      ║
// ║ style control, edited from inside.                    ║
// ║                                                       ║
// ║ Rules: blocks from the inside categories (mfg_*)     ║
// ║ can NEVER leave the editor window — not to the main   ║
// ║ canvas, not into a group. Regular flow blocks travel  ║
// ║ in/out freely (they run in the flow, right where the  ║
// ║ Add block sits). Inner blocks reference "this         ║
// ║ element" — no element input needed.                   ║
// ║                                                       ║
// ║ Storage: same as the group block — inner XML in the   ║
// ║ mutation (innerxml attr), hat chain + parked strays.  ║
// ║                                                       ║
// ║ Generation: the create call + one element handle var   ║
// ║ (guiel_get), then the inner chain inline. Event  ║
// ║ hats hoist their def to module level (sentinel) and   ║
// ║ register AFTER creation with the real id value.       ║
// ╚══════════════════════════════════════════════════════╝

// version-proof XML parse (this build: Blockly.utils.xml.textToDom)
function mfStudioTextToDom(t) {
  var u = (typeof Blockly !== 'undefined') && Blockly.utils;
  var f = (u && u.xml && u.xml.textToDom) || (Blockly.Xml && Blockly.Xml.textToDom);
  return f ? f(t) : null;
}

// blocks that may NEVER leave the element editor window
function mfIsStudioBlock(type) { return typeof type === 'string' && type.indexOf('mfg_') === 0; }

// clickable '✎ edit' — same pattern as the group block
function mfStudioEditField() {
  var field = new Blockly.FieldLabel('\u270e edit');
  field.EDITABLE = true;
  field.SERIALIZABLE = false;
  field.showEditor_ = function () {
    if (window.__mfOpenGuiel) window.__mfOpenGuiel(this.sourceBlock_);
  };
  return field;
}

// count the blocks chained under the hat (badge) — strays excluded
function mfStudioCountChain(innerXml) {
  if (!innerXml || !innerXml.replace) return 0;
  try {
    var dom = mfStudioTextToDom('<xml>' + innerXml + '</xml>');
    if (!dom) return 0;
    var n = 0;
    var kids = dom.children || [];
    for (var i = 0; i < kids.length; i++) {
      var k = kids[i];
      if (k.nodeName !== 'block' || k.getAttribute('type') !== 'pcr_group_hat') continue;
      var st = k.getElementsByTagName('statement');
      for (var s = 0; s < st.length; s++) {
        var b = st[s].firstChild;
        while (b) {
          if (b.nodeName === 'block') { n++; b = b.getElementsByTagName('next')[0]; if (b) b = b.firstChild; }
          else break;
        }
      }
    }
    return n;
  } catch (e) { return 0; }
}

// mutation mixin shared by every studio creator — identical to the group
function mfStudioMutation() {
  return {
    domToMutation: function (el) {
      try { this.mfInnerXml = el.getAttribute('innerxml') || ''; }
      catch (e) { this.mfInnerXml = ''; }
      this.mfStudioBadge();
    },
    mutationToDom: function () {
      var m = document.createElement('mutation');
      try { m.setAttribute('innerxml', this.mfInnerXml || ''); }
      catch (e) { m.setAttribute('innerxml', ''); }
      return m;
    },
    mfStudioBadge: function () {
      var n = 0;
      try { n = mfStudioCountChain(this.mfInnerXml || ''); } catch (e) { n = 0; }
      try { this.setFieldValue(n === 1 ? '(1 block)' : ('(' + n + ' blocks)'), 'STEPS'); } catch (e) {}
    },
    mfSetInnerXml: function (xml) {
      this.mfInnerXml = xml || '';
      try { this.mfStudioBadge(); } catch (e) {}
    }
  };
}

// ── inner block factory ─────────────────────────────────────────
// spec: { t: type, label: 'set text to', args: [...], out: 'String'|null,
//         tip: '...', py: function(v) -> code }
//  arg = { n: inputName, check: 'String', label: 'text', def: default value }
//  v.EL = the element var (from the creator ctx), v.<arg> = generated value
function mfStudioBlock(spec) {
  Blockly.Blocks[spec.t] = {
    init: function () {
      var dummy = this.appendDummyInput();
      if (spec.label) dummy.appendField(spec.label);
      (spec.fields || []).forEach(function (f) {
        if (f.label) dummy.appendField(f.label);
        dummy.appendField(new Blockly.FieldDropdown(f.options), f.name);
      });
      var self = this;
      (spec.args || []).forEach(function (a) {
        var inp = self.appendValueInput(a.n).setCheck(a.check || null);
        if (a.label) inp.appendField(a.label);
      });
      if (spec.statement) this.appendStatementInput('DO').setCheck(null);
      if (spec.out) this.setOutput(true, spec.out);
      else {
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
      }
      if (spec.floating) { this.setPreviousStatement(false); this.setNextStatement(false); }
      this.setInputsInline(true);
      this.setColour(spec.colour || 188);
      if (spec.tip) this.setTooltip(spec.tip);
    }
  };
  Blockly.Python[spec.t] = function (block) {
    var v = { EL: (window._mfgCtx || 'mf_guiel_iter') };
    (spec.args || []).forEach(function (a) {
      v[a.n] = Blockly.Python.valueToCode(block, a.n, Blockly.Python.ORDER_NONE) ||
        (a.def !== undefined
          ? (typeof a.def === 'boolean' ? (a.def ? 'True' : 'False')
            : typeof a.def === 'string' ? ("'" + String(a.def).replace(/'/g, "\\'") + "'")
            : a.def)
          : 'None');
    });
    if (spec.statement) {
      v.DO = Blockly.Python.statementToCode(block, 'DO') || '  pass\n';
    }
    try {
      return spec.py(v, block);
    } catch (e) {
      return '# studio block failed: ' + (e && e.message) + '\n';
    }
  };
}

// flyout default children for common sockets (embedded in the popup XML)
var MF_STUDIO_DEFS = {
  String: function (d) { return '<block type="text"><field name="TEXT">' + (d === undefined ? '' : d) + '</field></block>'; },
  Number: function (d) { return '<block type="math_number"><field name="NUM">' + (d === undefined ? 0 : d) + '</field></block>'; },
  Boolean: function (d) { return '<block type="logic_boolean"><field name="BOOL">' + (d === undefined || d ? 'TRUE' : 'FALSE') + '</field></block>'; },
  Array: function () { return '<block type="lists_create_with"><mutation items="2"></mutation><value name="ADD0">' + MF_STUDIO_DEFS.String('option a') + '</value><value name="ADD1">' + MF_STUDIO_DEFS.String('option b') + '</value></block>'; },
  Color: function (d) { return '<block type="pcr_color_hex"><field name="HEX">' + (d || '#ffffff') + '</field></block>'; },
  Box: function () { return '<block type="pcr_point_xy"><value name="X">' + MF_STUDIO_DEFS.Number(50) + '</value><value name="Y">' + MF_STUDIO_DEFS.Number(50) + '</value></block>'; },
  Image: function () { return '<block type="pcr_img_new"><value name="WIDTH">' + MF_STUDIO_DEFS.Number(100) + '</value><value name="HEIGHT">' + MF_STUDIO_DEFS.Number(100) + '</value><value name="COLOR">' + MF_STUDIO_DEFS.Color('#2f9e44') + '</value></block>'; },
  ResLoc: function () { return '<block type="pcr_res_location"><value name="PATH">' + MF_STUDIO_DEFS.String('res://') + '</value></block>'; },
};

// build the flyout XML entry for a spec (with default children)
function mfStudioFlyoutXml(spec) {
  var inner = (spec.args || []).map(function (a) {
    if (a.def === undefined) return '';
    var check = Array.isArray(a.check) ? a.check[0] : a.check;
    if (!check || !MF_STUDIO_DEFS[check]) return '';
    return '<value name="' + a.n + '">' + MF_STUDIO_DEFS[check](a.def) + '</value>';
  }).join('');
  var fields = (spec.fields || []).map(function (f) {
    var val = (f.options && f.options.length) ? f.options[0][1] : '';
    return '<field name="' + f.name + '">' + val + '</field>';
  }).join('');
  return '<block type="' + spec.t + '">' + fields + inner + '</block>';
}

// dropdown helpers
var MF_FONT_FAMILIES = [
  ['Segoe UI', 'Segoe UI'], ['Arial', 'Arial'], ['Calibri', 'Calibri'],
  ['Consolas', 'Consolas'], ['Courier New', 'Courier New'], ['Georgia', 'Georgia'],
  ['Tahoma', 'Tahoma'], ['Times New Roman', 'Times New Roman'],
  ['Trebuchet MS', 'Trebuchet MS'], ['Verdana', 'Verdana'],
];
var MF_RELIEFS = [
  ['flat', 'flat'], ['raised', 'raised'], ['sunken', 'sunken'],
  ['groove', 'groove'], ['ridge', 'ridge'], ['solid', 'solid'],
];
var MF_CURSORS = [
  ['arrow', 'arrow'], ['hand', 'hand2'], ['text', 'xterm'],
  ['busy', 'watch'], ['crosshair', 'crosshair'], ['move', 'fleur'],
];
var MF_JUSTIFY = [['left', 'left'], ['center', 'center'], ['right', 'right']];
var MF_DIRECTIONS = [
  ['left to right', 'left to right'], ['right to left', 'right to left'],
  ['top to bottom', 'top to bottom'], ['bottom to top', 'bottom to top'],
];

// ── the shared inner block library ────────────────────────────────
// statements use the implicit "this element" (window._mfgCtx var)
var MF_SPECS = [];
function mfSpec(s) { MF_SPECS.push(s); return s; }

// text & font
mfSpec({ t: 'mfg_set_text', label: 'set text to', args: [{ n: 'TEXT', check: 'String', label: 'text', def: 'Hello' }],
  tip: "Set the text of this element (button label, label text, checkbox caption, field content).",
  py: function (v) { return 'guiel_set_text(' + v.EL + ', ' + v.TEXT + ')\n'; } });
mfSpec({ t: 'mfg_set_font', label: 'set font', fields: [{ name: 'FAM', options: MF_FONT_FAMILIES, label: 'family' }],
  args: [{ n: 'SIZE', check: 'Number', label: 'size', def: 10 }],
  tip: "Set the font family and size of this element's text. Bold/italic/underline stack on top.",
  py: function (v, b) { var fam = b.getFieldValue('FAM') || 'Segoe UI';
    return 'guiel_set_font(' + v.EL + ', ' + JSON.stringify(fam) + ', int(' + v.SIZE + '))\n'; } });
mfSpec({ t: 'mfg_set_bold', label: 'bold', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'Bold the text of this element on/off.',
  py: function (v) { return 'guiel_set_font(' + v.EL + ', None, None, ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_italic', label: 'italic', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'Italicize the text of this element on/off.',
  py: function (v) { return 'guiel_set_font(' + v.EL + ', None, None, None, ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_underline', label: 'underline', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'Underline the text of this element on/off.',
  py: function (v) { return 'guiel_set_font(' + v.EL + ', None, None, None, None, ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_justify', label: 'align text', fields: [{ name: 'J', options: MF_JUSTIFY }],
  tip: 'Left/center/right-align the text of this element.',
  py: function (v, b) { return 'guiel_set_justify(' + v.EL + ", '" + (b.getFieldValue('J') || 'left') + "')\n"; } });

// colors & border
mfSpec({ t: 'mfg_set_text_color', label: 'set text color to', args: [{ n: 'COL', check: ['Color', 'String'], label: 'color', def: '#ffffff' }],
  tip: 'Text color of this element.',
  py: function (v) { return 'guiel_set_text_color(' + v.EL + ', ' + v.COL + ')\n'; } });
mfSpec({ t: 'mfg_set_bg_color', label: 'set background color to', args: [{ n: 'COL', check: ['Color', 'String'], label: 'color', def: '#2f9e44' }],
  tip: 'Background color of this element.',
  py: function (v) { return 'guiel_set_bg_color(' + v.EL + ', ' + v.COL + ')\n'; } });
mfSpec({ t: 'mfg_set_hover_color', label: 'set hover color to', args: [{ n: 'COL', check: ['Color', 'String'], label: 'color', def: '#4dabf7' }],
  tip: 'Color while the mouse hovers/presses this element (buttons & labels).',
  py: function (v) { return 'guiel_set_hover_color(' + v.EL + ', ' + v.COL + ')\n'; } });
mfSpec({ t: 'mfg_set_border', label: 'set border width', args: [{ n: 'W', check: 'Number', label: 'width', def: 2 }],
  fields: [{ name: 'STYLE', options: MF_RELIEFS, label: 'style' }],
  tip: 'Border width + style (flat / raised / sunken / groove / ridge / solid).',
  py: function (v, b) { return 'guiel_set_border(' + v.EL + ', int(' + v.W + "), '" + (b.getFieldValue('STYLE') || 'flat') + "')\n"; } });
mfSpec({ t: 'mfg_set_padding', label: 'set padding x', args: [{ n: 'PX', check: 'Number', def: 8 }, { n: 'PY', check: 'Number', label: 'y', def: 4 }],
  tip: 'Inner padding of this element (space between text and border).',
  py: function (v) { return 'guiel_set_padding(' + v.EL + ', int(' + v.PX + '), int(' + v.PY + '))\n'; } });
mfSpec({ t: 'mfg_set_sel_color', label: 'set selection color to', args: [{ n: 'COL', check: ['Color', 'String'], label: 'color', def: '#339af0' }],
  tip: 'Highlight color of the selected item (lists).',
  py: function (v) { return 'guiel_set_sel_color(' + v.EL + ', ' + v.COL + ')\n'; } });
mfSpec({ t: 'mfg_set_bar_color', label: 'set bar color to', args: [{ n: 'COL', check: ['Color', 'String'], label: 'color', def: '#2f9e44' }],
  tip: 'Color of the filled part of this progress bar.',
  py: function (v) { return 'guiel_set_bar_color(' + v.EL + ', ' + v.COL + ')\n'; } });

// size & place
mfSpec({ t: 'mfg_set_width', label: 'set width to', args: [{ n: 'W', check: 'Number', label: 'width', def: 120 }],
  tip: 'Width of this element (buttons/entries in character units, others pixels).',
  py: function (v) { return 'guiel_set_width(' + v.EL + ', int(' + v.W + '))\n'; } });
mfSpec({ t: 'mfg_set_height', label: 'set height to', args: [{ n: 'H', check: 'Number', label: 'height', def: 30 }],
  tip: 'Height of this element.',
  py: function (v) { return 'guiel_set_height(' + v.EL + ', int(' + v.H + '))\n'; } });
mfSpec({ t: 'mfg_move', label: 'move to x', args: [{ n: 'X', check: 'Number', def: 50 }, { n: 'Y', check: 'Number', label: 'y', def: 50 }],
  tip: 'Move this element to a new position in the window.',
  py: function (v) { return 'guiel_set_position(' + v.EL + ', int(' + v.X + '), int(' + v.Y + '))\n'; } });
mfSpec({ t: 'mfg_move_to', label: 'move to', args: [{ n: 'PT', check: 'Box', label: 'point', def: 50 }],
  tip: 'Move this element to a point (or the top-left corner of a box) from the Components category. Pair it with \'scale to resolution\' to work on any screen.',
  py: function (v) { return 'guiel_set_position(' + v.EL + ', int(' + v.PT + '[0]), int(' + v.PT + '[1]))\n'; } });
mfSpec({ t: 'mfg_set_scale', label: 'set scale to', args: [{ n: 'S', check: 'Number', label: 'scale', def: 2 }],
  tip: 'Scale this element (labels grow the font, images grow the picture).',
  py: function (v) { return 'guiel_set_scale(' + v.EL + ', float(' + v.S + '))\n'; } });

// behavior
mfSpec({ t: 'mfg_set_enabled', label: 'set enabled', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'Enable/disable this element — disabled elements ignore clicks.',
  py: function (v) { return 'guiel_set_enabled(' + v.EL + ', ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_read_only', label: 'set read-only', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'Make this element read-only (text fields and text areas).',
  py: function (v) { return 'guiel_set_read_only(' + v.EL + ', ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_wrap', label: 'set word wrap', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'Wrap long text to multiple lines instead of running off the window.',
  py: function (v) { return 'guiel_set_wrap(' + v.EL + ', ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_cursor', label: 'set mouse cursor', fields: [{ name: 'CUR', options: MF_CURSORS }],
  tip: 'Mouse cursor shape over this element (hand, text, busy...).',
  py: function (v, b) { return 'guiel_set_cursor(' + v.EL + ", '" + (b.getFieldValue('CUR') || 'arrow') + "')\n"; } });
mfSpec({ t: 'mfg_set_hyperlink', label: 'open link when clicked', args: [{ n: 'URL', check: 'String', label: 'url', def: 'https://example.com' }],
  tip: 'Clicking this element opens the link in the browser — the text turns into a hyperlink (label, button, image).',
  py: function (v) { return 'guiel_set_hyperlink(' + v.EL + ', ' + v.URL + ')\n'; } });

// content / values
mfSpec({ t: 'mfg_set_value', label: 'set value to', args: [{ n: 'VAL', check: null, label: 'value', def: 0 }],
  tip: 'Set the value of this element (checkbox on/off, combobox text, field text, slider/progress number, list index, tab index).',
  py: function (v) { return 'guiel_set_value(' + v.EL + ', ' + v.VAL + ')\n'; } });
mfSpec({ t: 'mfg_set_checked', label: 'set checked', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'Check/uncheck this checkbox.',
  py: function (v) { return 'guiel_set_value(' + v.EL + ', ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_progress', label: 'set progress to', args: [{ n: 'VAL', check: 'Number', label: '%', def: 50 }],
  tip: 'Set the progress value 0-100.',
  py: function (v) { return 'guiel_set_value(' + v.EL + ', float(' + v.VAL + '))\n'; } });
mfSpec({ t: 'mfg_set_items', label: 'set items to', args: [{ n: 'ITEMS', check: 'Array', label: 'list', def: [] }],
  tip: 'Replace the item list of this element (combobox, list, list view).',
  py: function (v) { return 'guiel_set_items(' + v.EL + ', list(' + v.ITEMS + '))\n'; } });
mfSpec({ t: 'mfg_set_tabs', label: 'set tab pages to', args: [{ n: 'TABS', check: 'Array', label: 'names', def: [] }],
  tip: 'Replace the tab pages of this tab element with the names from the list.',
  py: function (v) { return 'guiel_set_tabs(' + v.EL + ', list(' + v.TABS + '))\n'; } });
mfSpec({ t: 'mfg_set_active_tab', label: 'show tab page', args: [{ n: 'IDX', check: 'Number', label: 'index', def: 0 }],
  tip: 'Switch to the tab page at this index (0 = first).',
  py: function (v) { return 'guiel_set_value(' + v.EL + ', int(' + v.IDX + '))\n'; } });
mfSpec({ t: 'mfg_set_image', label: 'set image to', args: [{ n: 'IMG', check: 'Image', label: 'image', def: undefined }],
  tip: 'Replace the picture of this image element.',
  py: function (v) { return 'guiel_set_image(' + v.EL + ', ' + v.IMG + ')\n'; } });
mfSpec({ t: 'mfg_set_rotation', label: 'rotate by', args: [{ n: 'DEG', check: 'Number', label: 'degrees', def: 90 }],
  tip: 'Rotate this image by degrees (0-360).',
  py: function (v) { return 'guiel_set_rotation(' + v.EL + ', float(' + v.DEG + '))\n'; } });
mfSpec({ t: 'mfg_set_target', label: 'show folder', args: [{ n: 'PATH', check: ['RESLOC', 'String'], def: undefined }, { n: 'WL', check: 'String', label: 'whitelist', def: '.png .txt' }],
  tip: 'Rebuild the content of this view from a resource folder (whitelist = allowed file types).',
  py: function (v) { return 'guiel_rescan(' + v.EL + ', ' + v.PATH + ', ' + v.WL + ')\n'; } });

// slider / progress
mfSpec({ t: 'mfg_set_min', label: 'set min value to', args: [{ n: 'V', check: 'Number', label: 'min', def: 0 }],
  tip: 'Lower end of this slider.',
  py: function (v) { return 'guiel_set_min(' + v.EL + ', float(' + v.V + '))\n'; } });
mfSpec({ t: 'mfg_set_max', label: 'set max value to', args: [{ n: 'V', check: 'Number', label: 'max', def: 100 }],
  tip: 'Upper end of this slider.',
  py: function (v) { return 'guiel_set_max(' + v.EL + ', float(' + v.V + '))\n'; } });
mfSpec({ t: 'mfg_set_step', label: 'snap to whole numbers', args: [{ n: 'ON', check: 'Boolean', def: true }],
  tip: 'On = the slider snaps to whole numbers and shows tick marks.',
  py: function (v) { return 'guiel_set_step(' + v.EL + ', ' + v.ON + ')\n'; } });
mfSpec({ t: 'mfg_set_length', label: 'set length to', args: [{ n: 'L', check: 'Number', label: 'pixels', def: 200 }],
  tip: 'Length of this slider / progress bar in pixels.',
  py: function (v) { return 'guiel_set_length(' + v.EL + ', int(' + v.L + '))\n'; } });
mfSpec({ t: 'mfg_set_direction', label: 'set direction', fields: [{ name: 'DIR', options: MF_DIRECTIONS }],
  tip: 'Direction of this progress bar.',
  py: function (v, b) { return 'guiel_set_direction(' + v.EL + ", '" + (b.getFieldValue('DIR') || 'left to right') + "')\n"; } });

// getters
mfSpec({ t: 'mfg_get_text', label: 'text of this element', out: 'String',
  tip: 'The current text of this element.',
  py: function (v) { return ['guiel_get_text(' + v.EL + ')', Blockly.Python.ORDER_ATOMIC]; } });
mfSpec({ t: 'mfg_get_value', label: 'value of this element', out: 'Number',
  tip: 'The current value of this element (slider number, checkbox 0/1...).',
  py: function (v) { return ['guiel_get_value(' + v.EL + ')', Blockly.Python.ORDER_ATOMIC]; } });
mfSpec({ t: 'mfg_get_checked', label: 'is checked', out: 'Boolean',
  tip: 'True if this checkbox is checked.',
  py: function (v) { return ['bool(guiel_get_value(' + v.EL + '))', Blockly.Python.ORDER_ATOMIC]; } });
mfSpec({ t: 'mfg_get_items', label: 'items of this element', out: 'Array',
  tip: 'The item list of this element as a list.',
  py: function (v) { return ['guiel_get_items(' + v.EL + ')', Blockly.Python.ORDER_ATOMIC]; } });
mfSpec({ t: 'mfg_get_width', label: 'width of this element', out: 'Number',
  tip: 'Current on-screen width in pixels.',
  py: function (v) { return ['guiel_get_width(' + v.EL + ')', Blockly.Python.ORDER_ATOMIC]; } });
mfSpec({ t: 'mfg_get_height', label: 'height of this element', out: 'Number',
  tip: 'Current on-screen height in pixels.',
  py: function (v) { return ['guiel_get_height(' + v.EL + ')', Blockly.Python.ORDER_ATOMIC]; } });
mfSpec({ t: 'mfg_this', label: 'this element', out: 'GuiElem',
  tip: 'This element as a gui element handle — plug it into the generic element blocks (loops, get/set, remove...).',
  py: function (v) { return [v.EL, Blockly.Python.ORDER_ATOMIC]; } });

// event hats — floating, hoisted def + registration by the creator
function mfStudioEventHat(type, label, tip) {
  mfSpec({
    t: type, label: label, floating: true, statement: true,
    tip: tip, colour: 188,
    py: function (v, block) {
      var fn = '_mfg_evt_' + String(block.id || 'x').replace(/[^a-zA-Z0-9_]/g, '_');
      var doCode = (v.DO || '  pass\n').replace(/\s+$/, '');
      return '#@@PCR_FUNC_DEF@@\ndef ' + fn + '(mf_guiel_iter):\n' + doCode + '\n#@@PCR_FUNC_DEF_END@@\n';
    },
  });
}
mfStudioEventHat('mfg_on_click', 'When this element clicked',
  'Runs the blocks inside whenever this element is clicked. The handler is registered when the element is created — drag regular flow blocks in from the canvas too.');
mfStudioEventHat('mfg_on_change', 'When this element changed',
  'Runs the blocks inside whenever this element changes (checkbox toggled, combo selected, text typed, slider moved...). Registered when the element is created.');
mfStudioEventHat('mfg_on_return', 'When return pressed',
  'Runs the blocks inside when the user presses Enter in this input field. Registered when the element is created.');
mfStudioEventHat('mfg_on_select', 'When item selected',
  'Runs the blocks inside when the user selects an item in this tree view. Registered when the element is created.');

MF_SPECS.forEach(mfStudioBlock);

// ── per-element metadata ─────────────────────────────────────────
// label: on the block. title: popup window. cats: popup flyout categories.
// old: migration map (old value input → inner block + its input name).
window.MFG_KINDS = {
  button: {
    type: 'pcr_guiel_add_button', label: 'button', title: 'Button', colour: null,
    evt: 'mfg_on_click', evtKind: 'button',
    old: { LABEL: ['mfg_set_text', 'TEXT'], W: ['mfg_set_width', 'W'], H: ['mfg_set_height', 'H'] },
    cats: [
      ['Text & font', ['mfg_set_text', 'mfg_set_font', 'mfg_set_bold', 'mfg_set_italic', 'mfg_set_underline', 'mfg_set_justify', 'mfg_get_text']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color', 'mfg_set_hover_color', 'mfg_set_border', 'mfg_set_padding']],
      ['Size & place', ['mfg_set_width', 'mfg_set_height', 'mfg_move', 'mfg_move_to']],
      ['Behavior', ['mfg_set_enabled', 'mfg_set_cursor', 'mfg_set_hyperlink']],
      ['Events', ['mfg_on_click']],
      ['Element', ['mfg_this', 'mfg_get_width', 'mfg_get_height']]
    ]
  },
  label: {
    type: 'pcr_gui_add_label', label: 'label', title: 'Label', colour: null, scale: true,
    evt: 'mfg_on_click', evtKind: 'label_click',
    old: { TEXT: ['mfg_set_text', 'TEXT'], COLOR: ['mfg_set_text_color', 'COL'] },
    cats: [
      ['Text & font', ['mfg_set_text', 'mfg_set_font', 'mfg_set_bold', 'mfg_set_italic', 'mfg_set_underline', 'mfg_set_justify', 'mfg_set_wrap', 'mfg_get_text']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color', 'mfg_set_border', 'mfg_set_padding']],
      ['Size & place', ['mfg_set_scale', 'mfg_move', 'mfg_move_to']],
      ['Hyperlink', ['mfg_set_hyperlink', 'mfg_on_click']],
      ['Element', ['mfg_this', 'mfg_get_width', 'mfg_get_height']]
    ]
  },
  checkbox: {
    type: 'pcr_guiel_add_checkbox', label: 'checkbox', title: 'Checkbox', colour: null,
    evt: 'mfg_on_change', evtKind: 'checkbox',
    old: { LABEL: ['mfg_set_text', 'TEXT'], DEFAULT: ['mfg_set_checked', 'ON'] },
    cats: [
      ['Text & font', ['mfg_set_text', 'mfg_set_font', 'mfg_set_bold', 'mfg_set_italic', 'mfg_set_justify', 'mfg_get_text']],
      ['State', ['mfg_set_checked', 'mfg_get_checked']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color', 'mfg_set_border', 'mfg_set_padding']],
      ['Behavior', ['mfg_set_enabled', 'mfg_set_cursor']],
      ['Events', ['mfg_on_change']],
      ['Element', ['mfg_this']]
    ]
  },
  combobox: {
    type: 'pcr_guiel_add_combobox', label: 'combobox', title: 'Combobox', colour: null,
    evt: 'mfg_on_change', evtKind: 'combobox',
    old: { VALUES: ['mfg_set_items', 'ITEMS'] },
    cats: [
      ['Items', ['mfg_set_items', 'mfg_get_items', 'mfg_set_value', 'mfg_get_value']],
      ['Font', ['mfg_set_font', 'mfg_set_bold', 'mfg_set_italic']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_sel_color', 'mfg_set_border']],
      ['Behavior', ['mfg_set_enabled', 'mfg_set_read_only', 'mfg_set_cursor']],
      ['Events', ['mfg_on_change']],
      ['Element', ['mfg_this']]
    ]
  },
  list: {
    type: 'pcr_guiel_add_list', label: 'list', title: 'List', colour: null,
    evt: 'mfg_on_change', evtKind: 'list',
    old: { VALUES: ['mfg_set_items', 'ITEMS'] },
    cats: [
      ['Items', ['mfg_set_items', 'mfg_get_items', 'mfg_set_value', 'mfg_get_value']],
      ['Font', ['mfg_set_font', 'mfg_set_bold', 'mfg_set_italic']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color', 'mfg_set_sel_color', 'mfg_set_border']],
      ['Behavior', ['mfg_set_enabled', 'mfg_set_height']],
      ['Events', ['mfg_on_change']],
      ['Element', ['mfg_this']]
    ]
  },
  text_area: {
    type: 'pcr_guiel_add_text_area', label: 'text area', title: 'Text area', colour: null,
    evt: 'mfg_on_change', evtKind: 'text_area',
    old: { TEXT: ['mfg_set_text', 'TEXT'], W: ['mfg_set_width', 'W'], H: ['mfg_set_height', 'H'] },
    cats: [
      ['Text', ['mfg_set_text', 'mfg_get_text', 'mfg_set_read_only', 'mfg_set_wrap']],
      ['Font', ['mfg_set_font', 'mfg_set_bold', 'mfg_set_italic']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color', 'mfg_set_border']],
      ['Size & place', ['mfg_set_width', 'mfg_set_height', 'mfg_move', 'mfg_move_to']],
      ['Events', ['mfg_on_change']],
      ['Element', ['mfg_this']]
    ]
  },
  rectangle: {
    type: 'pcr_guiel_add_rectangle', label: 'rectangle', title: 'Rectangle', colour: null,
    evt: null, evtKind: null,
    old: { SIZE: null, COLOR: ['mfg_set_bg_color', 'COL'] },
    cats: [
      ['Colors', ['mfg_set_bg_color', 'mfg_set_border']],
      ['Size & place', ['mfg_set_width', 'mfg_set_height', 'mfg_move', 'mfg_move_to']],
      ['Element', ['mfg_this']]
    ]
  },
  image: {
    type: 'pcr_guiel_add_image', label: 'image', title: 'Image', colour: null, scale: true,
    evt: 'mfg_on_click', evtKind: 'image_click',
    old: { IMAGE: ['mfg_set_image', 'IMG'], HUE: ['mfg_set_bg_color', 'COL'] },
    cats: [
      ['Picture', ['mfg_set_image', 'mfg_set_rotation', 'mfg_set_scale']],
      ['Behavior', ['mfg_set_hyperlink', 'mfg_set_cursor', 'mfg_set_enabled']],
      ['Events', ['mfg_on_click']],
      ['Element', ['mfg_this', 'mfg_get_width', 'mfg_get_height']]
    ]
  },
  inputfield: {
    type: 'pcr_guiel_add_inputfield', label: 'inputfield', title: 'Input field', colour: null,
    evt: 'mfg_on_change', evtKind: 'inputfield',
    old: { DEFAULT: ['mfg_set_text', 'TEXT'], W: ['mfg_set_width', 'W'] },
    cats: [
      ['Text', ['mfg_set_text', 'mfg_get_text', 'mfg_set_read_only', 'mfg_set_value']],
      ['Font', ['mfg_set_font', 'mfg_set_bold', 'mfg_set_italic']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color', 'mfg_set_sel_color', 'mfg_set_border']],
      ['Behavior', ['mfg_set_enabled', 'mfg_set_cursor']],
      ['Events', ['mfg_on_change', 'mfg_on_return']],
      ['Element', ['mfg_this']]
    ]
  },
  list_view: {
    type: 'pcr_guiel_add_list_view', label: 'list view', title: 'List view', colour: null,
    evt: null, evtKind: null,
    old: { TARGET: ['mfg_set_target', 'PATH'], WHITELIST: ['mfg_set_target', 'WL'], W: ['mfg_set_width', 'W'], H: ['mfg_set_height', 'H'] },
    cats: [
      ['Content', ['mfg_set_target', 'mfg_set_items', 'mfg_get_items']],
      ['Font', ['mfg_set_font']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color', 'mfg_set_sel_color']],
      ['Size & place', ['mfg_set_width', 'mfg_set_height', 'mfg_move', 'mfg_move_to']],
      ['Element', ['mfg_this']]
    ]
  },
  tree_view: {
    type: 'pcr_guiel_add_tree_view', label: 'tree view', title: 'Tree view', colour: null,
    evt: 'mfg_on_select', evtKind: 'tree_view',
    old: { TARGET: ['mfg_set_target', 'PATH'], WHITELIST: ['mfg_set_target', 'WL'], W: ['mfg_set_width', 'W'], H: ['mfg_set_height', 'H'] },
    cats: [
      ['Content', ['mfg_set_target']],
      ['Font', ['mfg_set_font']],
      ['Colors', ['mfg_set_sel_color', 'mfg_set_border']],
      ['Size & place', ['mfg_set_width', 'mfg_set_height', 'mfg_move', 'mfg_move_to']],
      ['Events', ['mfg_on_select']],
      ['Element', ['mfg_this']]
    ]
  },
  progress: {
    type: 'pcr_guiel_add_progress', label: 'progress', title: 'Progress', colour: null,
    evt: null, evtKind: null,
    old: { COLOR: ['mfg_set_bar_color', 'COL'], W: ['mfg_set_length', 'L'] },
    cats: [
      ['Value', ['mfg_set_progress', 'mfg_set_direction', 'mfg_set_length', 'mfg_get_value']],
      ['Colors', ['mfg_set_bar_color']],
      ['Element', ['mfg_this']]
    ]
  },
  slider: {
    type: 'pcr_guiel_add_slider', label: 'slider', title: 'Slider', colour: null,
    evt: 'mfg_on_change', evtKind: 'slider',
    old: { MIN: ['mfg_set_min', 'V'], MAX: ['mfg_set_max', 'V'], DEFAULT: ['mfg_set_value', 'VAL'], STEP: ['mfg_set_step', 'ON'], LENGTH: ['mfg_set_length', 'L'] },
    cats: [
      ['Range', ['mfg_set_min', 'mfg_set_max', 'mfg_set_value', 'mfg_set_step', 'mfg_set_length', 'mfg_get_value']],
      ['Colors', ['mfg_set_text_color', 'mfg_set_bg_color']],
      ['Events', ['mfg_on_change']],
      ['Element', ['mfg_this']]
    ]
  },
  tab: {
    type: 'pcr_guiel_add_tab', label: 'tab', title: 'Tabs', colour: null,
    evt: 'mfg_on_change', evtKind: 'tab',
    old: { TABS: ['mfg_set_tabs', 'TABS'], W: ['mfg_set_width', 'W'], H: ['mfg_set_height', 'H'] },
    cats: [
      ['Tabs', ['mfg_set_tabs', 'mfg_set_active_tab', 'mfg_get_value']],
      ['Colors', ['mfg_set_border']],
      ['Events', ['mfg_on_change']],
      ['Element', ['mfg_this']]
    ]
  }
};
window.MFG_POPUP_KINDS = {};
Object.keys(window.MFG_KINDS).forEach(function (k) { window.MFG_POPUP_KINDS[window.MFG_KINDS[k].type] = k; });

// popup flyout XML per kind (built from the specs, with defaults)
window.MFG_CATEGORIES = {};
(function () {
  var byType = {};
  MF_SPECS.forEach(function (s) { byType[s.t] = s; });
  Object.keys(window.MFG_KINDS).forEach(function (k) {
    var K = window.MFG_KINDS[k];
    var cats = K.cats.map(function (c) {
      var blocks = c[1].map(function (t) {
        var s = byType[t];
        return s ? mfStudioFlyoutXml(s) : '';
      }).join('');
      return '<category name="' + c[0] + '" colour="#2f9e44">' + blocks + '</category>';
    }).join('');
    window.MFG_CATEGORIES[k] = '<xml>' + cats + '</xml>';
  });
})();

// ── creator blocks: minimal form + studio mutation ───────────────
// old value inputs (label, size, values...) come off the block; their
// defaults move INSIDE (migration turns saved projects into inner
// blocks, so nothing is lost).
function mfStudioCreatorInit(K) {
  return function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add ' + K.label + ' to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    if (K.scale) this.appendValueInput('SCALE').setCheck('Number').appendField('scale');
    this.appendDummyInput()
      .appendField(mfStudioEditField(), 'EDIT')
      .appendField('', 'STEPS');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);
    this.setColour(K.colour || PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('Add a ' + K.label + ' to a GUI window. Keep it simple here \u2014 click \u270e edit to open the ' + K.title + ' studio: fonts, colors, behavior and events for THIS element, each with its own categories. Everything in the studio applies to this one element.');
    this.mfInnerXml = '';
    this.mfmSteps = [];
  };
}

// element handle var — unique per generation
var mfStudioVarN = 0;
function mfStudioVar() {
  mfStudioVarN += 1;
  return '_mfg_el' + (mfStudioVarN > 1 ? String(mfStudioVarN) : '');
}

// create call per kind — evaluated defaults, inner blocks refine after
var MF_CREATE = {
  button: function (v) { return 'guiel_add_button(' + v.GUI + ', ' + v.ID + ", '', 0, 0, " + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  checkbox: function (v) { return 'guiel_add_checkbox(' + v.GUI + ', ' + v.ID + ", '', False, " + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  combobox: function (v) { return 'guiel_add_combobox(' + v.GUI + ', ' + v.ID + ', [], ' + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  list: function (v) { return 'guiel_add_list(' + v.GUI + ', ' + v.ID + ', [], ' + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  text_area: function (v) { return 'guiel_add_text_area(' + v.GUI + ', ' + v.ID + ", '', 0, 0, " + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  rectangle: function (v) { return 'guiel_add_rectangle(' + v.GUI + ', ' + v.ID + ', None, None, ' + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  image: function (v) { return 'guiel_add_image(' + v.GUI + ', ' + v.ID + ', None, None, ' + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  inputfield: function (v) { return 'guiel_add_inputfield(' + v.GUI + ', ' + v.ID + ", '', 0, " + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  list_view: function (v) { return 'guiel_add_list_view(' + v.GUI + ', ' + v.ID + ", 'res://', '', 30, 8, " + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  tree_view: function (v) { return 'guiel_add_tree_view(' + v.GUI + ', ' + v.ID + ", 'res://', '', 40, 10, " + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  progress: function (v) { return 'guiel_add_progress(' + v.GUI + ', ' + v.ID + ", 'left to right', None, 150, 0, " + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  slider: function (v) { return 'guiel_add_slider(' + v.GUI + ', ' + v.ID + ', 0, 100, 0, False, 200, ' + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  tab: function (v) { return 'guiel_add_tab(' + v.GUI + ', ' + v.ID + ', None, 0, 0, ' + v.X + ', ' + v.Y + ", '" + v.ANCHOR + "')\n"; },
  label: function (v) { return 'gui_add_label(' + v.GUI + ", '', " + v.ID + ", '" + v.ANCHOR + "', float(" + v.SCALE + '), ' + v.X + ', ' + v.Y + ', None)\n'; }
};

// creator generator: create + handle var + inner chain + event hats
function mfStudioCreatorGen(kind) {
  var K = window.MFG_KINDS[kind];
  return function (block) {
    var v = {
      GUI: Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0',
      ID: Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''",
      X: Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50',
      Y: Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50',
      ANCHOR: block.getFieldValue('ANCHOR') || 'center',
      SCALE: K.scale ? (Blockly.Python.valueToCode(block, 'SCALE', Blockly.Python.ORDER_NONE) || '1') : '1'
    };
    var code = MF_CREATE[kind](v);
    var innerXml = block.mfInnerXml || '';
    if (!innerXml) return code;

    var dom = null;
    try { dom = mfStudioTextToDom('<xml>' + innerXml + '</xml>'); } catch (e) { dom = null; }
    if (!dom) return code;

    var kids = dom.children || [];
    var hatChild = null, evtKids = [];
    for (var i = 0; i < kids.length; i++) {
      var kd = kids[i];
      if (kd.nodeName !== 'block') continue;
      var kt = kd.getAttribute('type');
      if (kt === 'pcr_group_hat') hatChild = kd;
      else if (kt.indexOf('mfg_on_') === 0) evtKids.push(kd);
    }
    if (!hatChild && !evtKids.length) return code;

    var elVar = mfStudioVar();
    var prev = window._mfgCtx;
    window._mfgCtx = elVar;
    try {
      if (hatChild) {
        var tws = new Blockly.Workspace();
        var hatBlock = Blockly.Xml.domToBlock(hatChild, tws);
        var head = hatBlock.getInputTargetBlock('DO');
        if (head) code += elVar + ' = guiel_get(' + v.GUI + ', ' + v.ID + ')\n' + Blockly.Python.blockToCode(head);
        try { tws.dispose(); } catch (e) {}
      }
      evtKids.forEach(function (kd) {
        var t = kd.getAttribute('type');
        var evtKind = (t === 'mfg_on_click') ? (K.evtKind || 'button')
          : (t === 'mfg_on_change') ? (K.evtKind || 'checkbox')
          : (t === 'mfg_on_return') ? 'inputfield_return'
          : (t === 'mfg_on_select') ? 'tree_view' : null;
        if (!evtKind) return;
        var ews = new Blockly.Workspace();
        var hb = Blockly.Xml.domToBlock(kd, ews);
        var fn = '_mfg_evt_' + String(kd.getAttribute('id') || ('e' + evtKids.indexOf(kd))).replace(/[^a-zA-Z0-9_]/g, '_');
        // inside the handler, "this element" = the element that fired
        window._mfgCtx = 'mf_guiel_iter';
        var doCode = '';
        try { doCode = Blockly.Python.statementToCode(hb, 'DO') || '  pass\n'; } catch (e) { doCode = '  pass\n'; }
        window._mfgCtx = elVar;
        code += '#@@PCR_FUNC_DEF@@\ndef ' + fn + '(mf_guiel_iter):\n' + doCode.replace(/\s+$/, '') + '\n#@@PCR_FUNC_DEF_END@@\n';
        code += 'guiel_on(' + JSON.stringify(evtKind) + ', ' + v.ID + ', ' + fn + ')\n';
        try { ews.dispose(); } catch (e) {}
      });
    } finally {
      window._mfgCtx = prev;
    }
    return code;
  };
}

// install: replace every creator's init + generator, add the mutation
Object.keys(window.MFG_KINDS).forEach(function (kind) {
  var K = window.MFG_KINDS[kind];
  var def = { init: mfStudioCreatorInit(K) };
  var mix = mfStudioMutation();
  Object.keys(mix).forEach(function (m) { def[m] = mix[m]; });
  Blockly.Blocks[K.type] = def;
  Blockly.Python[K.type] = mfStudioCreatorGen(kind);
});

// ── migration: old creators (label/values/size on the block) → studio ──
// Saved projects keep their type names, so an old "Add button" loads as
// the new minimal block — its old value inputs (label, width, ...) are
// moved INSIDE as studio blocks under a hat. Nothing is lost.
window.mfStudioMigrate = function (dom) {
  if (!dom || !dom.getElementsByTagName || !window.MFG_KINDS) return dom;
  var list = [];
  var all = dom.getElementsByTagName('block');
  for (var i = 0; i < all.length; i++) list.push(all[i]);
  list.forEach(function (be) {
    var kind = window.MFG_POPUP_KINDS[be.getAttribute('type')];
    if (!kind) return;
    var K = window.MFG_KINDS[kind];
    // already migrated?
    for (var c = 0; c < be.children.length; c++) {
      if (be.children[c].nodeName === 'mutation') return;
    }
    var vals = {};
    for (var v = 0; v < be.children.length; v++) {
      var ch = be.children[v];
      if (ch.nodeName === 'value' && K.old && K.old[ch.getAttribute('name')] !== undefined) {
        vals[ch.getAttribute('name')] = ch;
      }
    }
    var names = Object.keys(vals);
    if (!names.length) return;
    var inner = [];
    names.forEach(function (n) {
      var m = K.old[n];
      if (!m) return;   // unmapped input (e.g. rectangle box) — engine default
      var child = vals[n].firstElementChild;
      if (!child) return;
      inner.push('<block type="' + m[0] + '"><value name="' + m[1] + '">' +
                 Blockly.Xml.domToText(child) + '</value></block>');
    });
    if (!inner.length) return;
    var chain = inner[inner.length - 1];
    for (var j = inner.length - 2; j >= 0; j--) {
      chain = inner[j].slice(0, -8) + '<next>' + chain + '</next></block>';
    }
    var hat = '<block type="pcr_group_hat" x="24" y="14"><field name="NAME">' + K.title +
              '</field><statement name="DO">' + chain + '</statement></block>';
    names.forEach(function (n) { try { be.removeChild(vals[n]); } catch (e) {} });
    var mut = document.createElement('mutation');
    mut.setAttribute('innerxml', hat);
    be.appendChild(mut);
  });
  return dom;
};
