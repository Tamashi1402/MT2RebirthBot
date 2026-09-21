// ╔══════════════════════════════════════════════╗
// ║ Block: math_constrain                           ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Clamp value to range                    ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_constrain'] = function(block) {
  var x = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  var lo = Blockly.Python.valueToCode(block, 'LOW', Blockly.Python.ORDER_NONE) || '0';
  var hi = Blockly.Python.valueToCode(block, 'HIGH', Blockly.Python.ORDER_NONE) || '0';
  return ['max(' + lo + ', min(' + hi + ', ' + x + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
