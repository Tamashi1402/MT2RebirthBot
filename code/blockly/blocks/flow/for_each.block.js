Blockly.Python['controls_forEach'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_NONE) || '[]';
  var branch = Blockly.Python.statementToCode(block, 'DO') || (Blockly.Python.INDENT + 'pass\n');
  var IND = Blockly.Python.INDENT || '    ';
  var code = 'for ' + varName + ' in ' + list + ':\n';
  code += IND + 'if stopped():\n';
  code += IND + IND + 'break\n';
  code += branch;
  return code;
};
