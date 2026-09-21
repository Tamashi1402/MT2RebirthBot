// ╔════════════════════════════════════════════╗
// ║ Block: GUI elements (core)                  ║
// ║ Category: GUI → GUI Elements (dark green)   ║
// ║ Desc: A gui element is a handle to ONE      ║
// ║ widget inside a GUI window (button, slider, ║
// ║ label, ...). Typed Add-blocks create them,  ║
// ║ generic element blocks control them.       ║
// ╚════════════════════════════════════════════╝

// GUI element green — same hue as GUI, a bit darker so element blocks
// read differently from GUI window blocks (#2f9e44).
var PCR_GUIEL_COLOUR = '#257b35';

var PCR_GUIEL_ANCHORS = [
  ['center', 'center'],
  ['top center', 'n'],
  ['bottom center', 's'],
  ['left', 'w'],
  ['right', 'e'],
  ['top left', 'nw']
];

// every block type that owns a GuiElem ITER socket (auto-locked iterator)
window.MF_GUIEL_ITER_PARENTS = [
  'pcr_guiel_foreach',
  'pcr_guiel_on_button', 'pcr_guiel_on_checkbox', 'pcr_guiel_on_combobox',
  'pcr_guiel_on_list', 'pcr_guiel_on_text_area', 'pcr_guiel_on_inputfield',
  'pcr_guiel_on_slider'
];

/* ── create empty GUI element (value block) ── */
Blockly.Blocks['pcr_guiel_new'] = {
  init: function () {
    this.appendDummyInput().appendField('empty GUI element');
    this.setOutput(true, 'GuiElem');
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('An empty gui element — plugs into any gui element socket. Store one in a variable, then fill it with "get GUI element with id".');
  }
};
Blockly.Python['pcr_guiel_new'] = function () {
  return ['guiel_new()', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── get GUI element with id [string] from [gui] ── */
Blockly.Blocks['pcr_guiel_get'] = {
  init: function () {
    this.appendValueInput('ID').setCheck('String').appendField('get GUI element with id');
    this.appendValueInput('GUI').setCheck('Gui').appendField('from');
    this.setOutput(true, 'GuiElem');
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Retrieves ANY element of a GUI by its id as a gui element, so it can be managed with the element blocks. Empty element if the id does not exist.');
  }
};
Blockly.Python['pcr_guiel_get'] = function (block) {
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return ['guiel_get(' + g + ', ' + id + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── does [GUI] have GUI element with id [string] (logic) ── */
Blockly.Blocks['pcr_guiel_has'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('does');
    this.appendValueInput('ID').setCheck('String').appendField('have GUI element with id');
    this.setOutput(true, 'Boolean');
    this.setInputsInline(true);
    this.setColour(210);
    this.setTooltip('True if the GUI window has an element with this id (button, label, slider, ... — anything added with an id).');
  }
};
Blockly.Python['pcr_guiel_has'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  return ['guiel_has(' + g + ', ' + id + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── is [gui element] of type [dropdown] (logic) ── */
Blockly.Blocks['pcr_guiel_is_type'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('is');
    this.appendDummyInput().appendField('of type')
      .appendField(new Blockly.FieldDropdown([
        ['button', 'button'], ['checkbox', 'checkbox'],
        ['combobox', 'combobox'], ['list', 'list'],
        ['text area', 'text_area'], ['rectangle', 'rectangle'],
        ['image', 'image'], ['inputfield', 'inputfield'],
        ['list view', 'list_view'], ['progress bar', 'progress'],
        ['slider', 'slider'], ['tab', 'tab'],
        ['tree view', 'tree_view'], ['label', 'label']
      ]), 'TYPE');
    this.setOutput(true, 'Boolean');
    this.setInputsInline(true);
    this.setColour(210);
    this.setTooltip('True if the gui element is of this type. Empty elements are no type.');
  }
};
Blockly.Python['pcr_guiel_is_type'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var t = block.getFieldValue('TYPE') || 'button';
  return ['guiel_is_type(' + e + ", '" + t + "')", Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── GUI element iterator (value block) ──
   Inside "For each GUI element in" loops and "When ... do" event blocks:
   the element of the current iteration / the element that fired. */
Blockly.Blocks['pcr_guiel_iter'] = {
  init: function () {
    this.appendDummyInput().appendField('GUI element iterator');
    this.setOutput(true, 'GuiElem');
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('The current gui element inside a "For each GUI element" loop, or the element that fired in a "When ... do" event block. Inside its block it is locked in place — right-click and Duplicate to get a free copy for other element sockets.');
  }
};
Blockly.Python['pcr_guiel_iter'] = function () {
  return ['mf_guiel_iter', Blockly.Python.ORDER_ATOMIC];
};

/* ── For each GUI element in [gui] do as [gui element iterator] ── */
Blockly.Blocks['pcr_guiel_foreach'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('For each GUI element in');
    this.appendValueInput('ITER').setCheck('GuiElem').appendField('do as');
    this.appendStatementInput('DO');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Loop over EVERY element of a GUI window (buttons, labels, sliders, ... — anything with an id). The GUI element iterator stays locked in the loop — right-click it and Duplicate to plug the current element into other element blocks.');
  }
};
Blockly.Python['pcr_guiel_foreach'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var branch = Blockly.Python.statementToCode(block, 'DO') || '  pass\n';
  return 'for mf_guiel_iter in guiel_iter_elems(' + g + '):\n' + branch;
};

/* ── get width of [gui element] (number) ── */
Blockly.Blocks['pcr_guiel_get_width'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('get width of');
    this.setOutput(true, 'Number');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('Current pixel width of a gui element (as it is right now). 0 if the element is empty or gone.');
  }
};
Blockly.Python['pcr_guiel_get_width'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return ['guiel_get_width(' + e + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── get height of [gui element] (number) ── */
Blockly.Blocks['pcr_guiel_get_height'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('get height of');
    this.setOutput(true, 'Number');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('Current pixel height of a gui element (as it is right now). 0 if the element is empty or gone.');
  }
};
Blockly.Python['pcr_guiel_get_height'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return ['guiel_get_height(' + e + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── get width / height of [gui] (number) — current ACTUAL window size ── */
Blockly.Blocks['pcr_gui_get_width'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('get width of');
    this.setOutput(true, 'Number');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('The CURRENT width of a GUI window in pixels — not the default that was set by blocks, since GUIs can get rescaled by the user or by blocks.');
  }
};
Blockly.Python['pcr_gui_get_width'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return ['gui_get_width(' + g + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['pcr_gui_get_height'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('get height of');
    this.setOutput(true, 'Number');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('The CURRENT height of a GUI window in pixels — not the default that was set by blocks, since GUIs can get rescaled by the user or by blocks.');
  }
};
Blockly.Python['pcr_gui_get_height'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return ['gui_get_height(' + g + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── iterator lock (same behaviour as the GUI foreach lock): the gui
   element iterator inside its parent block can not be removed or moved;
   duplicates (context menu) are normal movable blocks. ── */
function mfGuielIterLockSync(ws, iterBlock) {
  if (!iterBlock || !iterBlock.getParent) return;
  var p = iterBlock.getParent();
  var inLoop = false;
  if (p && (window.MF_GUIEL_ITER_PARENTS || []).indexOf(p.type) >= 0) {
    var inp = p.getInput('ITER');
    inLoop = !!(inp && inp.connection && inp.connection.targetBlock() === iterBlock);
  }
  try {
    iterBlock.setMovable(!inLoop);
    iterBlock.setDeletable(!inLoop);
  } catch (e) {}
  if (inLoop) {
    iterBlock.customContextMenu = function (options) {
      options.unshift({
        text: 'Duplicate',
        enabled: true,
        callback: function () {
          try {
            var dup = ws.newBlock('pcr_guiel_iter');
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

function mfGuielIterEnsure(ws, parentBlock) {
  if (!parentBlock || !parentBlock.getInput) return;
  var inp = parentBlock.getInput('ITER');
  if (!inp || !inp.connection) return;
  var child = inp.connection.targetBlock();
  if (!child) {
    var it = ws.newBlock('pcr_guiel_iter');
    it.initSvg();
    it.render();
    inp.connection.connect(it.outputConnection);
    try { parentBlock.render(); } catch (e2) {}
    child = it;
  }
  mfGuielIterLockSync(ws, child);
}

function mfGuielIterSweep(ws) {
  if (!ws || !ws.getBlocksByType) return;
  var parents = window.MF_GUIEL_ITER_PARENTS || [];
  try {
    parents.forEach(function (pt) {
      (ws.getBlocksByType(pt) || []).forEach(function (b) { mfGuielIterEnsure(ws, b); });
    });
    (ws.getBlocksByType('pcr_guiel_iter') || []).forEach(function (b) { mfGuielIterLockSync(ws, b); });
  } catch (e) {}
}
window.mfGuielIterSweep = mfGuielIterSweep;

function mfInstallGuielIterLock(ws) {
  if (!ws || !ws.addChangeListener || ws.__mfGuielIterLockInstalled) return;
  ws.__mfGuielIterLockInstalled = true;
  ws.addChangeListener(function (e) {
    try {
      if (e.type !== Blockly.Events.BLOCK_CREATE && e.type !== Blockly.Events.BLOCK_MOVE) return;
      var ids = (e.ids && e.ids.length) ? e.ids : [e.blockId];
      ids.forEach(function (id) {
        var b = ws.getBlockById(id);
        if (!b) return;
        if ((window.MF_GUIEL_ITER_PARENTS || []).indexOf(b.type) >= 0) mfGuielIterEnsure(ws, b);
        else if (b.type === 'pcr_guiel_iter') mfGuielIterLockSync(ws, b);
      });
    } catch (err) {}
  });
}
window.mfInstallGuielIterLock = mfInstallGuielIterLock;
