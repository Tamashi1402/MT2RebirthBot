// ╔══════════════════════════════════════════════╗
// ║ Block: text_join                                ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: String concatenation                    ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_join'] = function(block) {
  // Mutator block — can have N inputs
  var elements = [];
  for (var i = 0; i < block.itemCount_; i++) {
    var code = Blockly.Python.valueToCode(block, 'ADD' + i, Blockly.Python.ORDER_NONE) || "''";
    elements.push(code);
  }
  if (elements.length === 0) return ["''", Blockly.Python.ORDER_ATOMIC];
  if (elements.length === 1) return ['str(' + elements[0] + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  var code = 'str(' + elements[0] + ')';
  for (var j = 1; j < elements.length; j++) {
    code += ' + str(' + elements[j] + ')';
  }
  return [code, Blockly.Python.ORDER_ADDITIVE];
};
