// ╔══════════════════════════════════════════════╗
// ║ Block: logic_negate                            ║
// ║ Category: base/logic                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Boolean NOT                             ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['logic_negate'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'BOOL', Blockly.Python.ORDER_LOGICAL_NOT) || 'False';
  return ['not ' + value, Blockly.Python.ORDER_LOGICAL_NOT];
};
