// ╔══════════════════════════════════════════════╗
// ║ Block: text_length                              ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: String length (len)                    ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_length'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  return ['len(' + text + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
