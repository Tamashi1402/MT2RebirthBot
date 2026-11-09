// ╔══════════════════════════════════════════════╗
// ║ Block: text_indexOf                            ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Find substring index                   ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_indexOf'] = function(block) {
  var op = block.getFieldValue('END');
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  var sub = Blockly.Python.valueToCode(block, 'FIND', Blockly.Python.ORDER_NONE) || "''";

  if (op === 'FIRST') {
    return [text + '.find(' + sub + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  } else {
    // Last occurrence — rfind
    return [text + '.rfind(' + sub + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  }
};
