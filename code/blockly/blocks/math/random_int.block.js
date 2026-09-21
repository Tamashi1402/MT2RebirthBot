// ╔══════════════════════════════════════════════╗
// ║ Block: math_random_int                          ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Random integer in range                 ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_random_int'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'FROM', Blockly.Python.ORDER_NONE) || '0';
  var b = Blockly.Python.valueToCode(block, 'TO', Blockly.Python.ORDER_NONE) || '0';
  return ['random.randint(' + a + ', ' + b + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
