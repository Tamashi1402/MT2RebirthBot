// ╔════════════════════════════════════════════╗
// ║ Block: GUI windows                            ║
// ║ Category: GUI (green)                        ║
// ║ Desc: Real OS windows (app or overlay style) ║
// ║ Every action takes a GUI VALUE INPUT — plug  ║
// ║ a gui variable (get gui), "create empty gui" ║
// ║ or any gui-typed output into it.             ║
// ╚════════════════════════════════════════════╝

var PCR_GUI_COLOUR = '#2f9e44';

if (typeof _pcrPyName !== 'function') {
  function _pcrPyName(raw) {
    var n = (raw || '').trim().replace(/[^A-Za-z0-9_]/g, '_');
    if (/^[0-9]/.test(n)) n = '_' + n;
    return n;
  }
}

/* ── create empty gui (value block) ── */
Blockly.Blocks['pcr_gui_new'] = {
  init: function () {
    this.appendDummyInput().appendField('create empty GUI');
    this.setOutput(true, 'Gui');
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Creates a new empty GUI window (a real OS window, hidden until you show it). Store it in a gui variable, set its resolution and style, then show it.');
  }
};
Blockly.Python['pcr_gui_new'] = function () {
  return ['gui_new()', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── Show GUI <gui value> at x y ── */
Blockly.Blocks['pcr_gui_show'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Show');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Show a GUI window at a screen position. Plug a gui variable (get gui), "create empty gui", or any gui value. The window is pulled to the front via Win32, so a fullscreen game can\u2019t bury it.');
  }
};
Blockly.Python['pcr_gui_show'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '100';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '100';
  return 'gui_show(' + g + ', ' + x + ', ' + y + ')\n';
};

/* ── Hide GUI <gui value> ── */
Blockly.Blocks['pcr_gui_hide'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Hide');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Hide a GUI window. It stays alive \u2014 show it again later.');
  }
};
Blockly.Python['pcr_gui_hide'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return 'gui_hide(' + g + ')\n';
};

/* ── Set GUI <gui value> resolution to x y ── */
Blockly.Blocks['pcr_gui_resize'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Set');
    this.appendValueInput('X').setCheck('Number').appendField('resolution to x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Set the size (resolution) of a GUI window in pixels.');
  }
};
Blockly.Python['pcr_gui_resize'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '400';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '300';
  return 'gui_resize(' + g + ', ' + x + ', ' + y + ')\n';
};

/* ── Move GUI <gui value> to x y ── */
Blockly.Blocks['pcr_gui_move'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Move');
    this.appendValueInput('X').setCheck('Number').appendField('to x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Move a GUI window to a screen position.');
  }
};
Blockly.Python['pcr_gui_move'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '100';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '100';
  return 'gui_move(' + g + ', ' + x + ', ' + y + ')\n';
};

/* ── Set GUI <gui value> app window to <bool input> ── */
Blockly.Blocks['pcr_gui_style'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Set');
    this.appendValueInput('APP').setCheck('Boolean').appendField('app window to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('true = normal app window (title bar, minimize / maximize / close). false = borderless overlay \u2014 no top bar, always on top.');
  }
};
Blockly.Python['pcr_gui_style'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var app = Blockly.Python.valueToCode(block, 'APP', Blockly.Python.ORDER_NONE) || 'True';
  return 'gui_style(' + g + ', bool(' + app + '))\n';
};

/* ── Set color of GUI <gui value> to <color> ── */
Blockly.Blocks['pcr_gui_set_color'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Set color of');
    this.appendValueInput('COLOR').setCheck(['Color', 'String']).appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Set the window (background) color of a GUI window. A bare overlay window (app window = false) is just a rectangle — it gets fully recolored. Plug a color value (R/G/B/A), a \'#RRGGBB\' string or a color name like \'red\'. Alpha below 255 makes the whole window translucent — e.g. color(16,20,24,128) or \'#10141880\'.');
  }
};
Blockly.Python['pcr_gui_set_color'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || 'None';
  return 'gui_set_color(' + g + ', ' + c + ')\n';
};

/* ── Allow resize of GUI <gui value> to <bool> ── */
Blockly.Blocks['pcr_gui_set_resizable'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Allow resize of');
    this.appendValueInput('ON').setCheck('Boolean').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('true = the window can be resized (corners/edges). false = fixed size. Windows are fixed-size by default. App windows resize natively; overlay windows (app window = false) get a drag grip on the bottom-right corner.');
  }
};
Blockly.Python['pcr_gui_set_resizable'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var on = Blockly.Python.valueToCode(block, 'ON', Blockly.Python.ORDER_NONE) || 'False';
  return 'gui_set_resizable(' + g + ', bool(' + on + '))\n';
};

/* ── GUI <gui value> is visible (value block) ── */
Blockly.Blocks['pcr_gui_is_visible'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('is');
    this.appendDummyInput().appendField('visible');
    this.setOutput(true, 'Boolean');
    this.setInputsInline(true);
    this.setColour(210); // default logic colour
    this.setTooltip('True if the GUI window is currently shown (visible on screen), false if hidden.');
  }
};
Blockly.Python['pcr_gui_is_visible'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return ['gui_visible(' + g + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── For each active GUI do as [gui iterator] ──
   The iterator in the socket is permanent: locked in place, can't be removed
   or dragged out. Right-click it \u2192 Duplicate to get a movable copy for
   other GUI sockets. (mfInstallGuiIterLock below enforces this.) */
Blockly.Blocks['pcr_gui_foreach'] = {
  init: function () {
    this.appendValueInput('ITER').setCheck('Gui').appendField('For each active GUI do as');
    this.appendStatementInput('DO');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Loop over every GUI window of the running mode that is currently SHOWN. The GUI iterator stays in the loop \u2014 right-click it and Duplicate to plug the current window into other GUI blocks.');
  }
};
Blockly.Python['pcr_gui_foreach'] = function (block) {
  var branch = Blockly.Python.statementToCode(block, 'DO') || '  pass\n';
  return 'for mf_gui_iter in gui_iter_active():\n' + branch;
};

/* ── Set title of GUI <gui value> to <string> ── */
Blockly.Blocks['pcr_gui_set_title'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Set title of');
    this.appendValueInput('TITLE').setCheck('String').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Set the window title of a GUI window \u2014 the app title shown on the top bar.');
  }
};
Blockly.Python['pcr_gui_set_title'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var t = Blockly.Python.valueToCode(block, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  return 'gui_set_title(' + g + ', ' + t + ')\n';
};

/* ── get title of <gui value> (string) ── */
Blockly.Blocks['pcr_gui_get_title'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('get title of');
    this.setOutput(true, 'String');
    this.setInputsInline(true);
    this.setColour(160); // string colour
    this.setTooltip('The window title of a GUI window \u2014 the app title shown on the top bar. Handy to identify windows while looping over active GUIs.');
  }
};
Blockly.Python['pcr_gui_get_title'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return ['gui_get_title(' + g + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── iterator lock: the gui iterator inside a For-each-active-GUI loop can
   not be removed or moved; duplicates (context menu) are normal blocks. ── */
function mfGuiIterLockSync(ws, iterBlock) {
  if (!iterBlock || !iterBlock.getParent) return;
  var p = iterBlock.getParent();
  var inLoop = false;
  if (p && p.type === 'pcr_gui_foreach') {
    var inp = p.getInput('ITER');
    inLoop = !!(inp && inp.connection && inp.connection.targetBlock() === iterBlock);
  }
  try {
    iterBlock.setMovable(!inLoop);
    iterBlock.setDeletable(!inLoop);
  } catch (e) {}
  if (inLoop) {
    // locked iterator: built-in Duplicate is gated by deletable/movable,
    // so give it its own duplicate that spawns a fresh MOVABLE copy
    iterBlock.customContextMenu = function (options) {
      options.unshift({
        text: 'Duplicate',
        enabled: true,
        callback: function () {
          try {
            var ws = iterBlock.workspace;
            var dup = ws.newBlock('pcr_gui_iter');
            dup.initSvg();
            dup.render();
            var xy = iterBlock.getRelativeToSurfaceXY();
            dup.moveBy(xy.x + 40, xy.y + 40);
            dup.select();
          } catch (e2) {}
        }
      });
    };
  } else {
    try { iterBlock.customContextMenu = null; } catch (e3) {}
  }
}

function mfGuiIterEnsure(ws, foreachBlock) {
  if (!foreachBlock || !foreachBlock.getInput) return;
  var inp = foreachBlock.getInput('ITER');
  if (!inp || !inp.connection) return;
  var child = inp.connection.targetBlock();
  if (!child) {
    var it = ws.newBlock('pcr_gui_iter');
    it.initSvg();
    it.render();
    inp.connection.connect(it.outputConnection);
    try { foreachBlock.render(); } catch (e2) {}
    child = it;
  }
  mfGuiIterLockSync(ws, child);
}

// full sweep: call after loading saved XML
function mfGuiIterSweep(ws) {
  if (!ws || !ws.getBlocksByType) return;
  try {
    (ws.getBlocksByType('pcr_gui_foreach') || []).forEach(function (b) { mfGuiIterEnsure(ws, b); });
    (ws.getBlocksByType('pcr_gui_iter') || []).forEach(function (b) { mfGuiIterLockSync(ws, b); });
  } catch (e) {}
}
window.mfGuiIterSweep = mfGuiIterSweep;

// install the live listener (fires for flyout drops, pastes, manual drags)
function mfInstallGuiIterLock(ws) {
  if (!ws || !ws.addChangeListener || ws.__mfIterLockInstalled) return;
  ws.__mfIterLockInstalled = true;
  ws.addChangeListener(function (e) {
    try {
      if (e.type !== Blockly.Events.BLOCK_CREATE && e.type !== Blockly.Events.BLOCK_MOVE) return;
      var ids = (e.ids && e.ids.length) ? e.ids : [e.blockId];
      ids.forEach(function (id) {
        var b = ws.getBlockById(id);
        if (!b) return;
        if (b.type === 'pcr_gui_foreach') mfGuiIterEnsure(ws, b);
        else if (b.type === 'pcr_gui_iter') mfGuiIterLockSync(ws, b);
      });
    } catch (err) {}
  });
}
window.mfInstallGuiIterLock = mfInstallGuiIterLock;

/* ── Add label [text] to GUI [gui] with id [id], anchor, scale, at x y ── */
Blockly.Blocks['pcr_gui_add_label'] = {
  init: function () {
    this.appendValueInput('TEXT').setCheck('String').appendField('Add label');
    this.appendValueInput('GUI').setCheck('Gui').appendField('to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendDummyInput()
      .appendField('anchor')
      .appendField(new Blockly.FieldDropdown([
        ['center', 'center'],
        ['top center', 'n'],
        ['bottom center', 's'],
        ['left', 'w'],
        ['right', 'e']
      ]), 'ANCHOR');
    this.appendValueInput('COLOR').setCheck(['Color', 'String']).appendField('color');
    this.appendValueInput('SCALE').setCheck('Number').appendField('scale');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default
    this.setColour(PCR_GUI_COLOUR);
    this.setTooltip('Add a text label to a GUI window at a position. Anchor decides how the label sits on x/y (center = middle of the label is at the point). Scale grows the font (1 = normal). Adding again with the SAME id replaces the old label \u2014 no separate \u201Cchange\u201D block needed. Use the id with \u201Cget label\u201D to read it back.');
  }
};
Blockly.Python['pcr_gui_add_label'] = function (block) {
  var t = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var an = block.getFieldValue('ANCHOR') || 'center';
  var sc = Blockly.Python.valueToCode(block, 'SCALE', Blockly.Python.ORDER_NONE) || '1';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var col = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || 'None';
  return 'gui_add_label(' + g + ', ' + t + ', ' + id + ", '" + an + "', float(" + sc + '), float(' + x + '), float(' + y + '), ' + col + ')\n';
};

/* ── get label [id] of GUI [gui] (string) ── */
Blockly.Blocks['pcr_gui_get_label'] = {
  init: function () {
    this.appendValueInput('ID').setCheck('String').appendField('get label');
    this.appendValueInput('GUI').setCheck('Gui').appendField('of');
    this.setOutput(true, 'String');
    this.setInputsInline(true);
    this.setColour(160); // string colour
    this.setTooltip('Read the current text of a GUI label by its id.');
  }
};
Blockly.Python['pcr_gui_get_label'] = function (block) {
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return ['gui_get_label(' + g + ', ' + id + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
