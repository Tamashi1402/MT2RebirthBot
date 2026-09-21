// ╔══════════════════════════════════════════════╗
// ║ Block: text_append                              ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Append text to variable                 ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_append'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return varName + ' = str(' + varName + ') + str(' + text + ')\n';
};
