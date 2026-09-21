// ╔══════════════════════════════════════════════╗
// ║ Block: text_isEmpty                            ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Check if string is empty              ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_isEmpty'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  return ['len(' + text + ') == 0', Blockly.Python.ORDER_RELATIONAL];
};
