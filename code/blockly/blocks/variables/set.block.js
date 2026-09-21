// ╔══════════════════════════════════════════════╗
// ║ Block: variables_set                             ║
// ║ Category: base/variables                      ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Set variable value                      ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['variables_set'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return varName + ' = ' + value + '\n';
};
