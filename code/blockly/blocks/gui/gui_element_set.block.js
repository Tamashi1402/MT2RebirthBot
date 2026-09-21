// ╔════════════════════════════════════════════╗
// ║ Block: GUI element control                   ║
// ║ Category: GUI → GUI Elements (dark green)   ║
// ║ Desc: Generic control for ANY gui element.  ║
// ║ Capability-safe: if the element doesn't     ║
// ║ support an op it just ignores it — nothing  ║
// ║ ever crashes.                                ║
// ╚════════════════════════════════════════════╝

/* ── Add GUI element [elem] with id [string] to [GUI] ── */
Blockly.Blocks['pcr_guiel_add'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('Add GUI element');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('GUI').setCheck('Gui').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Attach a gui element (from any GUI) to a GUI window under an id — get element, loops and remove see it there. tk widgets can\u2019t change parent window, so this is a registered attachment, not a move.');
  }
};
Blockly.Python['pcr_guiel_add'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return 'guiel_add(' + g + ', ' + e + ', ' + id + ')\n';
};

/* ── Remove GUI element with id [string] from [GUI] ── */
Blockly.Blocks['pcr_guiel_remove'] = {
  init: function () {
    this.appendValueInput('ID').setCheck('String').appendField('Remove GUI element with id');
    this.appendValueInput('GUI').setCheck('Gui').appendField('from');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Removes the element (and its widget) from the GUI window by id. Does nothing if the id doesn\u2019t exist.');
  }
};
Blockly.Python['pcr_guiel_remove'] = function (block) {
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  return 'guiel_remove(' + g + ', ' + id + ')\n';
};

/* ── set width of [gui element] to [number] ── */
Blockly.Blocks['pcr_guiel_set_width'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set width of');
    this.appendValueInput('W').setCheck('Number').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Set the width of a gui element. Works only if the element supports width — buttons and entries take character units, other elements pixels. Elements that can\u2019t just ignore it (nothing crashes).');
  }
};
Blockly.Python['pcr_guiel_set_width'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '0';
  return 'guiel_set_width(' + e + ', ' + w + ')\n';
};

/* ── set height of [gui element] to [number] ── */
Blockly.Blocks['pcr_guiel_set_height'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set height of');
    this.appendValueInput('H').setCheck('Number').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Set the height of a gui element (pixels; buttons and text areas take character/line units). Works only if the element supports height — otherwise it is ignored, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_height'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '0';
  return 'guiel_set_height(' + e + ', ' + h + ')\n';
};

/* ── set scale of [gui element] to [number] ── */
Blockly.Blocks['pcr_guiel_set_scale'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set scale of');
    this.appendValueInput('S').setCheck('Number').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Scale a gui element (1 = original size). Supported by labels (font scale) and images (pixel scale) — everything else ignores it, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_scale'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var s = Blockly.Python.valueToCode(block, 'S', Blockly.Python.ORDER_NONE) || '1';
  return 'guiel_set_scale(' + e + ', ' + s + ')\n';
};

/* ── set color of [gui element] to [color] ── */
Blockly.Blocks['pcr_guiel_set_color'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set color of');
    this.appendValueInput('COLOR').setCheck(['Color', 'String']).appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Set the color of a gui element — text color for labels/buttons/checkboxes, fill color for rectangles. Elements that can\u2019t take a color just ignore it, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_color'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || 'None';
  return 'guiel_set_color(' + e + ', ' + c + ')\n';
};

/* ── set position of [gui element] to x [number] y [number] ── */
Blockly.Blocks['pcr_guiel_set_position'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set position of');
    this.appendValueInput('X').setCheck('Number').appendField('to x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Move a gui element to a new position inside the GUI window. The element keeps its anchor from creation. Works on every placed element.');
  }
};
Blockly.Python['pcr_guiel_set_position'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  return 'guiel_set_position(' + e + ', ' + x + ', ' + y + ')\n';
};

/* ── set label of [gui element] to [string] ── */
Blockly.Blocks['pcr_guiel_set_label'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set label of');
    this.appendValueInput('TEXT').setCheck('String').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Set the text of a gui element — works for labels, buttons and checkboxes (their label). Other elements ignore it, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_label'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var t = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'guiel_set_label(' + e + ', ' + t + ')\n';
};

/* ── set value of [gui element] to [any] ── */
Blockly.Blocks['pcr_guiel_set_value'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set value of');
    this.appendValueInput('VALUE').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Set the value of a gui element: number for sliders (and progress bars 0-100), logic for checkboxes, text for inputfields/text areas/comboboxes, index for lists. Elements without a value ignore it, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_value'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var v = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return 'guiel_set_value(' + e + ', ' + v + ')\n';
};

/* ── get value of [gui element] (number) ── */
Blockly.Blocks['pcr_guiel_get_value'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('get value of');
    this.setOutput(true, null);
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('The current value of a gui element: number for sliders and progress bars, logic for checkboxes, text for inputfields/text areas/comboboxes, selected entry for lists. 0 if the element has no value.');
  }
};
Blockly.Python['pcr_guiel_get_value'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return ['guiel_get_value(' + e + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};


/* ── set text of [gui element] to [text] ──
   Capability-safe: label / button / checkbox captions and inputfield /
   text area content accept text; every other element ignores it. */
Blockly.Blocks['pcr_guiel_set_text'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set text of');
    this.appendValueInput('TEXT').setCheck('String').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Set the text of a gui element: label/button/checkbox captions and inputfield/text area content. Elements without text ignore it, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_text'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var t = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'guiel_set_text(' + e + ', ' + t + ')\n';
};

/* ── get text of [gui element] (string) ── */
Blockly.Blocks['pcr_guiel_get_text'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('get text of');
    this.setOutput(true, 'String');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('The text of a gui element: label/button/checkbox captions, inputfield/text area content, combobox entry. Empty text if the element has none.');
  }
};
Blockly.Python['pcr_guiel_get_text'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return ['guiel_get_text(' + e + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── set items of [gui element] to [list] ──
   Combobox / list / list view replace their entries; others ignore it. */
Blockly.Blocks['pcr_guiel_set_items'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set items of');
    this.appendValueInput('ITEMS').setCheck('Array').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Replace the items of a gui element: combobox / list / list view entries. Elements without items ignore it, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_items'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var it = Blockly.Python.valueToCode(block, 'ITEMS', Blockly.Python.ORDER_NONE) || '[]';
  return 'guiel_set_items(' + e + ', ' + it + ')\n';
};

/* ── get items of [gui element] (list) ── */
Blockly.Blocks['pcr_guiel_get_items'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('get items of');
    this.setOutput(true, 'Array');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('The items of a gui element as a list: combobox / list / list view entries, tab page names. Empty list if the element has none.');
  }
};
Blockly.Python['pcr_guiel_get_items'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return ['guiel_get_items(' + e + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

/* ── set active of [gui element] to [logic] ──
   Checkbox checked state; other elements ignore it. */
Blockly.Blocks['pcr_guiel_set_active'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('set active of');
    this.appendValueInput('ACTIVE').setCheck('Boolean').appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_GUIEL_COLOUR);
    this.setTooltip('Set the active (checked) state of a checkbox gui element. Other elements ignore it, nothing crashes.');
  }
};
Blockly.Python['pcr_guiel_set_active'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var a = Blockly.Python.valueToCode(block, 'ACTIVE', Blockly.Python.ORDER_NONE) || 'False';
  return 'guiel_set_active(' + e + ', bool(' + a + '))\n';
};

/* ── get active of [gui element] (logic) ── */
Blockly.Blocks['pcr_guiel_get_active'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('get active of');
    this.setOutput(true, 'Boolean');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('True if a checkbox gui element is active/checked. False for everything else.');
  }
};
Blockly.Python['pcr_guiel_get_active'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return ['guiel_get_active(' + e + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
