// ╔══════════════════════════════════════════════╗
// ║ Block: math_change                               ║
// ║ Category: base/variables                      ║
// ║ Built-in: Yes (listed under math in Blockly)  ║
// ║ Desc: Increment variable by delta             ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_change'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var delta = Blockly.Python.valueToCode(block, 'DELTA', Blockly.Python.ORDER_NONE) || '1';
  return varName + ' = ' + varName + ' + ' + delta + '\n';
};
