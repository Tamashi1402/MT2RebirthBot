// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_compare_color — color = color     ║
// ║ Category: color                              ║
// ║ Desc: Compare two colors (#hex or rgba())   ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_compare_color'] = {
  init: function() {
    this.appendValueInput('A').setCheck(['String', 'Color']);
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ['=', 'EQ'], ['\u2260', 'NEQ']
    ]), 'OP');
    this.appendValueInput('B').setCheck(['String', 'Color']);
    this.setInputsInline(true);
    this.setOutput(true, 'Boolean');
    this.setColour(20);
    this.setTooltip('Compare two colors — #hex or rgba() strings (e.g. is the pixel color still #FF0000?)');
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_compare_color'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || '"#FFFFFF"';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || '"#FFFFFF"';
  var op = block.getFieldValue('OP') === 'NEQ' ? '!=' : '==';
  return [a + ' ' + op + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};
