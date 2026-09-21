// ╔══════════════════════════════════════════════╗
// ║ Block: text_trim                                ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Strip whitespace                       ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_trim'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return [text + '.strip()', Blockly.Python.ORDER_FUNCTION_CALL];
};
