// Typed comparisons — one block per type (not a generic A ? B).
Blockly.Blocks['pcr_compare_text'] = {
  init: function() {
    this.appendValueInput('A').setCheck('String');
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ['=', 'EQ'], ['\u2260', 'NEQ']
    ]), 'OP');
    this.appendValueInput('B').setCheck('String');
    this.setInputsInline(true);
    this.setOutput(true, 'Boolean');
    this.setColour(160);
    this.setTooltip('Compare two strings');
  }
};
Blockly.Python['pcr_compare_text'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || "''";
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || "''";
  var op = block.getFieldValue('OP') === 'NEQ' ? '!=' : '==';
  return [a + ' ' + op + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};

Blockly.Blocks['pcr_compare_number'] = {
  init: function() {
    this.appendValueInput('A').setCheck('Number');
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ['=', 'EQ'], ['\u2260', 'NEQ'], ['<', 'LT'], ['\u2264', 'LTE'], ['>', 'GT'], ['\u2265', 'GTE']
    ]), 'OP');
    this.appendValueInput('B').setCheck('Number');
    this.setInputsInline(true);
    this.setOutput(true, 'Boolean');
    this.setColour(230);
    this.setTooltip('Compare two numbers');
  }
};
Blockly.Python['pcr_compare_number'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || '0';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || '0';
  var map = { EQ: '==', NEQ: '!=', LT: '<', LTE: '<=', GT: '>', GTE: '>=' };
  var op = map[block.getFieldValue('OP')] || '==';
  return [a + ' ' + op + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};

Blockly.Blocks['pcr_compare_logic'] = {
  init: function() {
    this.appendValueInput('A').setCheck('Boolean');
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ['=', 'EQ'], ['\u2260', 'NEQ']
    ]), 'OP');
    this.appendValueInput('B').setCheck('Boolean');
    this.setInputsInline(true);
    this.setOutput(true, 'Boolean');
    this.setColour(210);
    this.setTooltip('Compare two booleans');
  }
};
Blockly.Python['pcr_compare_logic'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || 'False';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || 'False';
  var op = block.getFieldValue('OP') === 'NEQ' ? '!=' : '==';
  return [a + ' ' + op + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};

// ── Image comparison (Image category) ──
Blockly.Blocks['pcr_compare_image'] = {
  init: function() {
    this.appendValueInput('A').setCheck('Image');
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ['=', 'EQ'], ['\u2260', 'NEQ']
    ]), 'OP');
    this.appendValueInput('B').setCheck('Image');
    this.setInputsInline(true);
    this.setOutput(true, 'Boolean');
    this.setColour(300);
    this.setTooltip('Compare two images pixel-by-pixel (same size, exact match)');
  }
};
Blockly.Python['pcr_compare_image'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || 'None';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || 'None';
  var call = 'images_equal(' + a + ', ' + b + ')';
  if (block.getFieldValue('OP') === 'NEQ') call = '(not ' + call + ')';
  return [call, Blockly.Python.ORDER_RELATIONAL];
};

// ── Resource location comparison (Components category) ──
Blockly.Blocks['pcr_compare_resloc'] = {
  init: function() {
    this.appendValueInput('A').setCheck(['String', 'RESLOC']);
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ['=', 'EQ'], ['\u2260', 'NEQ']
    ]), 'OP');
    this.appendValueInput('B').setCheck(['String', 'RESLOC']);
    this.setInputsInline(true);
    this.setOutput(true, 'Boolean');
    this.setColour(230);
    this.setTooltip('Compare two resource locations (res:// paths)');
  }
};
Blockly.Python['pcr_compare_resloc'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || "''";
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || "''";
  var op = block.getFieldValue('OP') === 'NEQ' ? '!=' : '==';
  return [a + ' ' + op + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};

// ── List comparison (Lists category) ──
Blockly.Blocks['pcr_compare_list'] = {
  init: function() {
    this.appendValueInput('A').setCheck('Array');
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ['=', 'EQ'], ['\u2260', 'NEQ']
    ]), 'OP');
    this.appendValueInput('B').setCheck('Array');
    this.setInputsInline(true);
    this.setOutput(true, 'Boolean');
    this.setColour(260);
    this.setTooltip('Compare two lists (same items in the same order)');
  }
};
Blockly.Python['pcr_compare_list'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || '[]';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || '[]';
  var op = block.getFieldValue('OP') === 'NEQ' ? '!=' : '==';
  return [a + ' ' + op + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};
