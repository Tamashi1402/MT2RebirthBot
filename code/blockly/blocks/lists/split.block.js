// ╔══════════════════════════════════════════════╗
// ║ Block: lists_split                              ║
// ║ Category: base/lists                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Split string into list                  ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['lists_split'] = function(block) {
  var mode = block.getFieldValue('MODE');
  var input = Blockly.Python.valueToCode(block, 'INPUT', Blockly.Python.ORDER_NONE) || "''";

  if (mode === 'SPLIT') {
    var delim = Blockly.Python.valueToCode(block, 'DELIM', Blockly.Python.ORDER_NONE) || "' '";
    return [input + '.split(' + delim + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  } else {
    // JOIN mode
    return [input + '.split()', Blockly.Python.ORDER_FUNCTION_CALL];
  }
};
