// ╔══════════════════════════════════════════════╗
// ║ Block: lists_create_with                        ║
// ║ Category: base/lists                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Create list with items                 ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['lists_create_with'] = function(block) {
  var elements = [];
  for (var i = 0; i < block.itemCount_; i++) {
    var code = Blockly.Python.valueToCode(block, 'ADD' + i, Blockly.Python.ORDER_NONE) || 'None';
    elements.push(code);
  }
  return ['[' + elements.join(', ') + ']', Blockly.Python.ORDER_COLLECTION];
};
