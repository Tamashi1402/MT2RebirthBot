Blockly.Python['lists_indexOf'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '[]';
  var item = Blockly.Python.valueToCode(block, 'FIND', Blockly.Python.ORDER_NONE) || 'None';
  var op = block.getFieldValue('END');
  // 1-based index, 0 if not found (Blockly convention)
  if (op === 'FIRST') {
    return ['((' + list + '.index(' + item + ') + 1) if (' + item + ' in ' + list + ') else 0)', Blockly.Python.ORDER_CONDITIONAL];
  }
  return ['((len(' + list + ') - ' + list + '[::-1].index(' + item + ')) if (' + item + ' in ' + list + ') else 0)', Blockly.Python.ORDER_CONDITIONAL];
};
