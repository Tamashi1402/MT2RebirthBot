// ╔══════════════════════════════════════════════╗
// ║ Block: text_changeCase                         ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Upper / lower case                     ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_changeCase'] = function(block) {
  var op = block.getFieldValue('CASE');
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";

  if (op === 'UPPERCASE') {
    return [text + '.upper()', Blockly.Python.ORDER_FUNCTION_CALL];
  } else {
    return [text + '.lower()', Blockly.Python.ORDER_FUNCTION_CALL];
  }
};
