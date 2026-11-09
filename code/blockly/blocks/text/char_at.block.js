// ╔══════════════════════════════════════════════╗
// ║ Block: text_charAt                             ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Get character at index                  ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_charAt'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_MEMBER) || "''";
  var at = Blockly.Python.valueToCode(block, 'AT', Blockly.Python.ORDER_NONE) || '0';
  return [text + '[' + at + ']', Blockly.Python.ORDER_MEMBER];
};
