Blockly.Python['lists_setIndex'] = function(block) {
  var mode = block.getFieldValue('MODE');
  var where = block.getFieldValue('WHERE');
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_MEMBER) || '[]';
  var at = Blockly.Python.valueToCode(block, 'AT', Blockly.Python.ORDER_NONE) || '1';
  var to = Blockly.Python.valueToCode(block, 'TO', Blockly.Python.ORDER_NONE) || 'None';

  var index;
  switch (where) {
    case 'FROM_START': index = '(int(' + at + ') - 1)'; break;
    case 'FROM_END':   index = '-int(' + at + ')'; break;
    case 'FIRST':      index = '0'; break;
    case 'LAST':       index = '-1'; break;
    default:           index = '(int(' + at + ') - 1)'; break;
  }

  if (mode === 'INSERT') {
    return list + '.insert(' + index + ', ' + to + ')\n';
  }
  return list + '[' + index + '] = ' + to + '\n';
};
