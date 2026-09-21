// ╔══════════════════════════════════════════════╗
// ║ Block: lists_sort                               ║
// ║ Category: base/lists                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Sort list                              ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['lists_sort'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_NONE) || '[]';
  var type = block.getFieldValue('TYPE');
  var direction = block.getFieldValue('DIRECTION');

  var reverse = (direction === '1') ? 'True' : 'False';

  if (type === 'NUMERIC') {
    return ['sorted(' + list + ', key=lambda x: float(x), reverse=' + reverse + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  } else {
    return ['sorted(' + list + ', reverse=' + reverse + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  }
};
