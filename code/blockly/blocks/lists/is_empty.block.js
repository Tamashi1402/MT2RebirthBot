// ╔══════════════════════════════════════════════╗
// ║ Block: lists_isEmpty                            ║
// ║ Category: base/lists                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Check if list is empty                 ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['lists_isEmpty'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '[]';
  return ['len(' + list + ') == 0', Blockly.Python.ORDER_RELATIONAL];
};
