// ╔══════════════════════════════════════════════╗
// ║ Block: math_modulo                              ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Modulo (%)                              ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_modulo'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'DIVIDEND', Blockly.Python.ORDER_MULTIPLICATIVE) || '0';
  var b = Blockly.Python.valueToCode(block, 'DIVISOR', Blockly.Python.ORDER_MULTIPLICATIVE) || '1';
  return [a + ' % ' + b, Blockly.Python.ORDER_MULTIPLICATIVE];
};
