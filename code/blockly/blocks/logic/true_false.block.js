// ╔══════════════════════════════════════════════╗
// ║ Block: logic_boolean                           ║
// ║ Category: base/logic                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Boolean literal (True / False)          ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['logic_boolean'] = function(block) {
  var value = block.getFieldValue('BOOL');
  return [(value === 'TRUE') ? 'True' : 'False', Blockly.Python.ORDER_ATOMIC];
};
