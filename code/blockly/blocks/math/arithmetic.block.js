// ╔══════════════════════════════════════════════╗
// ║ Block: math_arithmetic                         ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Arithmetic (+, -, *, /, **, %)          ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_arithmetic'] = function(block) {
  var op = block.getFieldValue('OP');
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_ATOMIC) || '0';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_ATOMIC) || '0';

  var pyOp, precedence;
  switch (op) {
    case 'ADD':      pyOp = '+';  precedence = Blockly.Python.ORDER_ADDITIVE; break;
    case 'MINUS':    pyOp = '-';  precedence = Blockly.Python.ORDER_ADDITIVE; break;
    case 'MULTIPLY': pyOp = '*';  precedence = Blockly.Python.ORDER_MULTIPLICATIVE; break;
    case 'DIVIDE':   pyOp = '/';  precedence = Blockly.Python.ORDER_MULTIPLICATIVE; break;
    case 'POWER':    pyOp = '**'; precedence = Blockly.Python.ORDER_EXPONENTIATION; break;
    default:         pyOp = '+';  precedence = Blockly.Python.ORDER_ADDITIVE; break;
  }

  return [a + ' ' + pyOp + ' ' + b, precedence];
};
