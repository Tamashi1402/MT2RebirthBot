Blockly.Python['controls_repeat_ext'] = function(block) {
  var times = Blockly.Python.valueToCode(block, 'TIMES', Blockly.Python.ORDER_NONE) || '0';
  var branch = Blockly.Python.statementToCode(block, 'DO') || (Blockly.Python.INDENT + 'pass\n');
  var IND = Blockly.Python.INDENT || '    ';
  var code = 'for _ in range(max(0, int(' + times + '))):\n';
  code += IND + 'if stopped():\n';
  code += IND + IND + 'break\n';
  code += branch;
  return code;
};
