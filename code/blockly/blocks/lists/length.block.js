// ╔══════════════════════════════════════════════╗
// ║ Block: lists_length                             ║
// ║ Category: base/lists                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: List length (len)                      ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['lists_length'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '[]';
  return ['len(' + list + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
