// lists_getIndex — 1-based like Blockly UI
Blockly.Python['lists_getIndex'] = function(block) {
  var mode = block.getFieldValue('MODE');
  var where = block.getFieldValue('WHERE');
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_MEMBER) || '[]';
  var at = Blockly.Python.valueToCode(block, 'AT', Blockly.Python.ORDER_NONE) || '1';

  var index;
  switch (where) {
    case 'FROM_START': index = '(int(' + at + ') - 1)'; break;
    case 'FROM_END':   index = '-int(' + at + ')'; break;
    case 'FIRST':      index = '0'; break;
    case 'LAST':       index = '-1'; break;
    case 'RANDOM':     index = 'random.randrange(len(' + list + '))'; break;
    default:           index = '(int(' + at + ') - 1)'; break;
  }

  if (mode === 'GET') {
    return [list + '[' + index + ']', Blockly.Python.ORDER_MEMBER];
  } else if (mode === 'GET_REMOVE') {
    return [list + '.pop(' + index + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  } else if (mode === 'REMOVE') {
    return 'del ' + list + '[' + index + ']\n';
  }
  return '';
};
