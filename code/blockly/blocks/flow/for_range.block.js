// Block: controls_for — inclusive range + F9 stop
Blockly.Python['controls_for'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var start = Blockly.Python.valueToCode(block, 'FROM', Blockly.Python.ORDER_NONE) || '0';
  var end = Blockly.Python.valueToCode(block, 'TO', Blockly.Python.ORDER_NONE) || '0';
  var step = Blockly.Python.valueToCode(block, 'BY', Blockly.Python.ORDER_NONE) || '1';
  var branch = Blockly.Python.statementToCode(block, 'DO') || (Blockly.Python.INDENT + 'pass\n');
  var IND = Blockly.Python.INDENT || '    ';
  var code = '';
  code += varName + '_start = ' + start + '\n';
  code += varName + '_end = ' + end + '\n';
  code += varName + '_step = ' + step + '\n';
  code += 'if ' + varName + '_step == 0:\n';
  code += IND + varName + '_step = 1 if ' + varName + '_end >= ' + varName + '_start else -1\n';
  code += varName + '_stop = (' + varName + '_end + ' + varName + '_step)\n';
  code += 'for ' + varName + ' in range(' + varName + '_start, ' + varName + '_stop, ' + varName + '_step):\n';
  code += IND + 'if stopped():\n';
  code += IND + IND + 'break\n';
  code += branch;
  return code;
};
