// ╔══════════════════════════════════════════════╗
// ║ Block: math_trig                                ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Trig functions (sin, cos, tan, etc.)    ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_trig'] = function(block) {
  var op = block.getFieldValue('OP');
  var x = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_NONE) || '0';

  var func;
  switch (op) {
    case 'SIN':   func = 'math.sin';  break;
    case 'COS':   func = 'math.cos';  break;
    case 'TAN':   func = 'math.tan';  break;
    case 'ASIN':  func = 'math.asin'; break;
    case 'ACOS':  func = 'math.acos'; break;
    case 'ATAN':  func = 'math.atan'; break;
    default:      func = 'math.sin';  break;
  }

  return [func + '(' + x + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
