// ╔════════════════════════════════════════════╗
// ║  MacroForge — gui elements: webview kit     ║
// ╚════════════════════════════════════════════╝

// embedded browser for GUI windows (needs 'pip install tkinterweb' —
// without it the element shows a hint label and never crashes)
var PCR_WV_COLOUR = '#2f9e44';
var PCR_WV_ANCHORS = (typeof PCR_GUIEL_ANCHORS !== 'undefined' && PCR_GUIEL_ANCHORS.length)
  ? PCR_GUIEL_ANCHORS
  : [['center', 'center'], ['nw', 'nw'], ['n', 'n'], ['ne', 'ne'], ['w', 'w'],
     ['e', 'e'], ['sw', 'sw'], ['s', 's'], ['se', 'se']];

/* ── Add webview to [gui] with id [string] default [url] scroll [bool] interact [bool] width/h at x/y anchor ── */
Blockly.Blocks['pcr_guiel_add_webview'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add webview to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('DEFAULT').setCheck('String').appendField('default');
    this.appendValueInput('SCROLL').setCheck('Boolean').appendField('scroll');
    this.appendValueInput('INTERACT').setCheck('Boolean').appendField('interact');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('H').setCheck('Number').appendField('height');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_WV_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_WV_COLOUR);
    this.setTooltip('An embedded browser page inside the GUI window (needs pip install tkinterweb). scroll = the page can be scrolled, interact = clicks/links work like a real browser. Navigate with Load page / Go back / Go forward.');
  }
};
Blockly.Python['pcr_guiel_add_webview'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var url = Blockly.Python.valueToCode(block, 'DEFAULT', Blockly.Python.ORDER_NONE) || "''";
  var sc = Blockly.Python.valueToCode(block, 'SCROLL', Blockly.Python.ORDER_NONE) || 'True';
  var ia = Blockly.Python.valueToCode(block, 'INTERACT', Blockly.Python.ORDER_NONE) || 'True';
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '0';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '0';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_webview(' + g + ', ' + id + ', ' + url + ', bool(' + sc + '), bool(' + ia + '), int(' + w + '), int(' + h + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Load page [url] in [gui element] ── */
Blockly.Blocks['pcr_guiel_load_page'] = {
  init: function () {
    this.appendValueInput('TEXT').setCheck('String').appendField('Load page');
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('in');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_WV_COLOUR);
    this.setTooltip('Load a url into a webview gui element (adds it to the back/forward history).');
  }
};
Blockly.Python['pcr_guiel_load_page'] = function (block) {
  var t = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return 'guiel_load_page(' + e + ', ' + t + ')\n';
};

/* ── Go back in [gui element] ── */
Blockly.Blocks['pcr_guiel_webview_back'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('Go back in');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_WV_COLOUR);
    this.setTooltip('Go back one page in a webview gui element (does nothing at the start of the history).');
  }
};
Blockly.Python['pcr_guiel_webview_back'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return 'guiel_webview_back(' + e + ')\n';
};

/* ── Go forward in [gui element] ── */
Blockly.Blocks['pcr_guiel_webview_forward'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('Go forward in');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_WV_COLOUR);
    this.setTooltip('Go forward one page in a webview gui element (does nothing at the end of the history).');
  }
};
Blockly.Python['pcr_guiel_webview_forward'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return 'guiel_webview_forward(' + e + ')\n';
};

/* ── Scroll [gui element] up/down [lines] lines ── */
Blockly.Blocks['pcr_guiel_scroll_webview'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('Scroll');
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([['up', 'up'], ['down', 'down']]), 'DIR');
    this.appendValueInput('LINES').setCheck('Number').appendField('lines');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(PCR_WV_COLOUR);
    this.setTooltip('Scroll a webview gui element up or down by a number of lines.');
  }
};
Blockly.Python['pcr_guiel_scroll_webview'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  var dir = block.getFieldValue('DIR') || 'down';
  var n = Blockly.Python.valueToCode(block, 'LINES', Blockly.Python.ORDER_NONE) || '10';
  var dy = (dir === 'up') ? ('-' + n) : n;
  return 'guiel_scroll(' + e + ', int(' + dy + '))\n';
};

/* ── get url of [gui element] (string) ── */
Blockly.Blocks['pcr_guiel_get_url'] = {
  init: function () {
    this.appendValueInput('ELEM').setCheck('GuiElem').appendField('get url of');
    this.setOutput(true, 'String');
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('The url of the page a webview gui element is currently showing.');
  }
};
Blockly.Python['pcr_guiel_get_url'] = function (block) {
  var e = Blockly.Python.valueToCode(block, 'ELEM', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return ['guiel_get_url(' + e + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
