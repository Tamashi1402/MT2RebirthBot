// ╔════════════════════════════════════════════╗
// ║ Block: GUI element creators                 ║
// ║ Category: GUI → Actions (GUI green, like   ║
// ║ Add label — they ADD widgets to a window)  ║
// ║ Desc: Add typed widgets (default Windows   ║
// ║ look) to a GUI. Every creator takes an id — ║
// ║ the same id replaces the old element.       ║
// ║ Control them afterwards through the generic ║
// ║ element blocks in the Elements subcategory. ║
// ╚════════════════════════════════════════════╝

// creators are GUI actions on the window itself — GUI green, like Add label
var PCR_GUIEL_CREATE_COLOUR = '#2f9e44';

/* ── Add button to [gui] with id [id] label [label] width [w] height [h] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_button'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add button to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('LABEL').setCheck('String').appendField('label');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('H').setCheck('Number').appendField('height');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A standard Windows button. Width/height are in character units (tk style, 0 = auto size). Fire clicks with the "When button id clicked" block — it can live in another procedure.');
  }
};
Blockly.Python['pcr_guiel_add_button'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var lb = Blockly.Python.valueToCode(block, 'LABEL', Blockly.Python.ORDER_NONE) || "''";
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '0';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '0';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_button(' + g + ', ' + id + ', ' + lb + ', int(' + w + '), int(' + h + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add checkbox to [gui] with id [id] label [label] default [bool] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_checkbox'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add checkbox to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('LABEL').setCheck('String').appendField('label');
    this.appendValueInput('DEFAULT').setCheck('Boolean').appendField('default');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A standard checkbox with a label. Default = checked or not. Listen with the "When checkbox id changed" block.');
  }
};
Blockly.Python['pcr_guiel_add_checkbox'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var lb = Blockly.Python.valueToCode(block, 'LABEL', Blockly.Python.ORDER_NONE) || "''";
  var d = Blockly.Python.valueToCode(block, 'DEFAULT', Blockly.Python.ORDER_NONE) || 'False';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_checkbox(' + g + ', ' + id + ', ' + lb + ', bool(' + d + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add combobox to [gui] with id [id] values [list] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_combobox'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add combobox to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('VALUES').setCheck('Array').appendField('values');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A dropdown selector. The first value from the list is selected by default. Listen with the "When combobox id changed" block.');
  }
};
Blockly.Python['pcr_guiel_add_combobox'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var v = Blockly.Python.valueToCode(block, 'VALUES', Blockly.Python.ORDER_NONE) || '[]';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_combobox(' + g + ', ' + id + ', list(' + v + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add list to [gui] with id [id] values [list] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_list'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add list to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('VALUES').setCheck('Array').appendField('values');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A selection list — all values visible, first one selected by default. Listen with the "When list id changed" block.');
  }
};
Blockly.Python['pcr_guiel_add_list'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var v = Blockly.Python.valueToCode(block, 'VALUES', Blockly.Python.ORDER_NONE) || '[]';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_list(' + g + ', ' + id + ', list(' + v + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add text area to [gui] with id [id] text [text] width [w] height [h] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_text_area'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add text area to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('TEXT').setCheck('String').appendField('text');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('H').setCheck('Number').appendField('height');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A multi-line text box with a starting text. Width/height are in character/line units. Listen with the "When text area id changed" block (typing, deleting...).');
  }
};
Blockly.Python['pcr_guiel_add_text_area'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var t = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '40';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '6';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_text_area(' + g + ', ' + id + ', ' + t + ', int(' + w + '), int(' + h + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add rectangle to [gui] with id [id] size [box] color [color] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_rectangle'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add rectangle to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('BOX').setCheck('Box').appendField('size');
    this.appendValueInput('COLOR').setCheck(['Color', 'String']).appendField('color');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A filled rectangle — panel, background, divider. Size box gives width/height (x2-x1, y2-y1), color fills it. Resize later with "set width/height of".');
  }
};
Blockly.Python['pcr_guiel_add_rectangle'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var b = Blockly.Python.valueToCode(block, 'BOX', Blockly.Python.ORDER_NONE) || '[0, 0, 100, 50]';
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || 'None';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_rectangle(' + g + ', ' + id + ', ' + b + ', ' + c + ', ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add image to [gui] with id [id] image [image] hue [color] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_image'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add image to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('IMAGE').setCheck('Image').appendField('image');
    this.appendValueInput('HUE').setCheck(['Color', 'String']).appendField('hue');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('Show an image (from the image blocks) inside a GUI. Hue tints the image with the color — leave it empty for the original look. Scale it later with "set scale of".');
  }
};
Blockly.Python['pcr_guiel_add_image'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var im = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_NONE) || 'None';
  var hu = Blockly.Python.valueToCode(block, 'HUE', Blockly.Python.ORDER_NONE) || 'None';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_image(' + g + ', ' + id + ', ' + im + ', ' + hu + ', ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add inputfield to [gui] with id [id] default [string] width [w] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_inputfield'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add inputfield to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('DEFAULT').setCheck('String').appendField('default');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A single-line input field (like a text area but one line). Listen with the "When inputfield id changed" block (typing, deleting...).');
  }
};
Blockly.Python['pcr_guiel_add_inputfield'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var d = Blockly.Python.valueToCode(block, 'DEFAULT', Blockly.Python.ORDER_NONE) || "''";
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '20';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_inputfield(' + g + ', ' + id + ', ' + d + ', int(' + w + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add list view to [gui] with id [id] target [res] whitelist [string] width [w] height [h] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_list_view'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add list view to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('TARGET').setCheck(['RESLOC', 'String']).appendField('target');
    this.appendValueInput('WHITELIST').setCheck('String').appendField('whitelist');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('H').setCheck('Number').appendField('height');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A typical Windows file list: shows the files (and folders) of a resource location. Whitelist like ".png .txt" filters by extension — empty shows everything. Advanced.');
  }
};
Blockly.Python['pcr_guiel_add_list_view'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var t = Blockly.Python.valueToCode(block, 'TARGET', Blockly.Python.ORDER_NONE) || "''";
  var wl = Blockly.Python.valueToCode(block, 'WHITELIST', Blockly.Python.ORDER_NONE) || "''";
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '30';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '8';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_list_view(' + g + ', ' + id + ', ' + t + ', ' + wl + ', int(' + w + '), int(' + h + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add tree view to [gui] with id [id] target [res] whitelist [string] width [w] height [h] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_tree_view'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add tree view to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('TARGET').setCheck(['RESLOC', 'String']).appendField('target');
    this.appendValueInput('WHITELIST').setCheck('String').appendField('whitelist');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('H').setCheck('Number').appendField('height');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('Like the list view but as a Windows tree — folders of the resource location are branches that expand one level. Advanced.');
  }
};
Blockly.Python['pcr_guiel_add_tree_view'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var t = Blockly.Python.valueToCode(block, 'TARGET', Blockly.Python.ORDER_NONE) || "''";
  var wl = Blockly.Python.valueToCode(block, 'WHITELIST', Blockly.Python.ORDER_NONE) || "''";
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '40';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '10';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_tree_view(' + g + ', ' + id + ', ' + t + ', ' + wl + ', int(' + w + '), int(' + h + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add progress bar to [gui] with id [id] direction [dropdown] color [color] width [w] height [h] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_progress'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add progress bar to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendDummyInput().appendField('direction')
      .appendField(new Blockly.FieldDropdown([
        ['left to right', 'left to right'],
        ['right to left', 'right to left'],
        ['bottom to top', 'bottom to top'],
        ['top to bottom', 'top to bottom']
      ]), 'DIRECTION');
    this.appendValueInput('COLOR').setCheck(['Color', 'String']).appendField('color');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('H').setCheck('Number').appendField('height');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A plain progress bar, no background — just the bar. Width = length in pixels (height for vertical directions). Fill it with "set value of" 0-100. Right-to-left / bottom-to-top bars read the value mirrored.');
  }
};
Blockly.Python['pcr_guiel_add_progress'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var dr = block.getFieldValue('DIRECTION') || 'left to right';
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || 'None';
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '150';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '0';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_progress(' + g + ', ' + id + ", '" + dr + "', " + c + ', int(' + w + '), int(' + h + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add slider to [gui] with id [id] min [n] max [n] default [n] step [bool] length [n] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_slider'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add slider to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('MIN').setCheck('Number').appendField('min');
    this.appendValueInput('MAX').setCheck('Number').appendField('max');
    this.appendValueInput('DEFAULT').setCheck('Number').appendField('default');
    this.appendValueInput('STEP').setCheck('Boolean').appendField('step');
    this.appendValueInput('LENGTH').setCheck('Number').appendField('length');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A default Windows slider. Step true = whole numbers with tick marks. Length in pixels. Read it with "get value of", listen with the "When slider id changed" block.');
  }
};
Blockly.Python['pcr_guiel_add_slider'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var mn = Blockly.Python.valueToCode(block, 'MIN', Blockly.Python.ORDER_NONE) || '0';
  var mx = Blockly.Python.valueToCode(block, 'MAX', Blockly.Python.ORDER_NONE) || '100';
  var d = Blockly.Python.valueToCode(block, 'DEFAULT', Blockly.Python.ORDER_NONE) || '0';
  var st = Blockly.Python.valueToCode(block, 'STEP', Blockly.Python.ORDER_NONE) || 'False';
  var ln = Blockly.Python.valueToCode(block, 'LENGTH', Blockly.Python.ORDER_NONE) || '200';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_slider(' + g + ', ' + id + ', ' + mn + ', ' + mx + ', ' + d + ', bool(' + st + '), int(' + ln + '), ' + x + ', ' + y + ", '" + an + "')\n";
};

/* ── Add tab to [gui] with id [id] tabs [list] width [w] height [h] at x [x] y [y] [anchor] ── */
Blockly.Blocks['pcr_guiel_add_tab'] = {
  init: function () {
    this.appendValueInput('GUI').setCheck('Gui').appendField('Add tab to');
    this.appendValueInput('ID').setCheck('String').appendField('with id');
    this.appendValueInput('TABS').setCheck('Array').appendField('tabs');
    this.appendValueInput('W').setCheck('Number').appendField('width');
    this.appendValueInput('H').setCheck('Number').appendField('height');
    this.appendValueInput('X').setCheck('Number').appendField('at x');
    this.appendValueInput('Y').setCheck('Number').appendField('y');
    this.appendDummyInput().appendField('anchor').appendField(new Blockly.FieldDropdown(PCR_GUIEL_ANCHORS), 'ANCHOR');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(false);  // external by default — right-click offers "Inline Inputs"
    this.setColour(PCR_GUIEL_CREATE_COLOUR);
    this.setTooltip('A tab control — each string from the list becomes a tab. Advanced; the selected tab is readable with "get value of".');
  }
};
Blockly.Python['pcr_guiel_add_tab'] = function (block) {
  var g = Blockly.Python.valueToCode(block, 'GUI', Blockly.Python.ORDER_NONE) || '0';
  var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var v = Blockly.Python.valueToCode(block, 'TABS', Blockly.Python.ORDER_NONE) || '[]';
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '0';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '0';
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '50';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '50';
  var an = block.getFieldValue('ANCHOR') || 'center';
  return 'guiel_add_tab(' + g + ', ' + id + ', list(' + v + '), int(' + w + '), int(' + h + '), ' + x + ', ' + y + ", '" + an + "')\n";
};
