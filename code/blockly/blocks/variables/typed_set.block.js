// ╔══════════════════════════════════════════════╗
// ║ Block: Typed variable SET blocks               ║
// ║ Category: Variables                           ║
// ║ PYCreator 1:1 — dropdown Global: / Local:     ║
// ╚══════════════════════════════════════════════╝

if (typeof _pcrPyName !== 'function') {
  function _pcrPyName(raw) {
    var n = (raw || '').trim().replace(/[^A-Za-z0-9_]/g, '_');
    if (/^[0-9]/.test(n)) n = '_' + n;
    return n;
  }
}
if (typeof pcrVarDropdown !== 'function') {
  function pcrVarDropdown(varType) {
    return new Blockly.FieldDropdown(function () {
      return [['(no variables of this type)', '']];
    });
  }
}

Blockly.Blocks['pcr_set_text'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('set text')
      .appendField(pcrVarDropdown('text'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck('String')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(160);
    this.setTooltip('Set a text (string) variable.');
  }
};

Blockly.Blocks['pcr_set_number'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('set number')
      .appendField(pcrVarDropdown('number'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck('Number')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip('Set a number variable.');
  }
};

Blockly.Blocks['pcr_set_logic'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('set logic')
      .appendField(pcrVarDropdown('logic'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck('Boolean')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(210);
    this.setTooltip('Set a boolean variable.');
  }
};

Blockly.Blocks['pcr_set_list'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('set list')
      .appendField(pcrVarDropdown('list'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck('Array')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(260);
    this.setTooltip('Set a list variable.');
  }
};

Blockly.Blocks['pcr_set_image'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('set image')
      .appendField(pcrVarDropdown('image'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck('Image')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(300);
    this.setTooltip('Set an image variable to a loaded image.');
  }
};

Blockly.Blocks['pcr_set_resloc'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('set resource location')
      .appendField(pcrVarDropdown('resloc'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck(['String', 'RESLOC'])
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(270);
    this.setTooltip('Set a resource location variable (res:// name or a path).');
  }
};

Blockly.Blocks['pcr_set_color'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('set color')
      .appendField(pcrVarDropdown('color'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck(['String', 'Color'])
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(20);
    this.setTooltip('Set a color variable (#RRGGBB).');
  }
};

Blockly.Python['pcr_set_gui'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return '';
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return varName + ' = ' + value + '\n';
};

Blockly.Python['pcr_set_guiel'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return '';
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'guiel_new()';
  return varName + ' = ' + value + '\n';
};

Blockly.Python['pcr_set_text'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  if (!varName) return '';
  return varName + ' = ' + value + '\n';
};

Blockly.Python['pcr_set_number'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  if (!varName) return '';
  return varName + ' = ' + value + '\n';
};

Blockly.Python['pcr_set_logic'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'False';
  if (!varName) return '';
  return varName + ' = ' + value + '\n';
};

Blockly.Python['pcr_set_list'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '[]';
  if (!varName) return '';
  return varName + ' = ' + value + '\n';
};

Blockly.Blocks['pcr_set_gui'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('Set GUI')
      .appendField(pcrVarDropdown('gui'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck('Gui')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour('#2f9e44');
    this.setTooltip('Set a gui variable to a GUI window (from "create empty GUI").');
  }
};

Blockly.Blocks['pcr_set_guiel'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('Set GUI element')
      .appendField(pcrVarDropdown('guiel'), 'VAR');
    this.appendValueInput('VALUE')
      .setCheck('GuiElem')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('to');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour('#257b35');
    this.setTooltip('Set a gui element variable to any element (from "get GUI element with id", loops or event blocks).');
  }
};

Blockly.Python['pcr_set_image'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  if (!varName) return '';
  return varName + ' = ' + value + '\n';
};

Blockly.Python['pcr_set_resloc'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  if (!varName) return '';
  return varName + ' = ' + value + '\n';
};

Blockly.Python['pcr_set_color'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '"#000000"';
  if (!varName) return '';
  return varName + ' = ' + value + '\n';
};
