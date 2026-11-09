// ╔══════════════════════════════════════════════╗
// ║ Block: variables_get                             ║
// ║ Category: base/variables                      ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Get variable value                      ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['variables_get'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  return [varName, Blockly.Python.ORDER_ATOMIC];
};
