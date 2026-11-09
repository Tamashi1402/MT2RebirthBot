// ╔══════════════════════════════════════════════╗
// ║ Block: math_single                             ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Single-arg math (sqrt, abs, neg, etc.)  ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_single'] = function(block) {
  var op = block.getFieldValue('OP');
  var x = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_NONE) || '0';

  var code, precedence = Blockly.Python.ORDER_FUNCTION_CALL;

  switch (op) {
    case 'ABS':   code = 'abs(' + x + ')'; break;
    case 'NEG':   code = '-' + x; precedence = Blockly.Python.ORDER_UNARY_SIGN; break;
    case 'ROOT':  code = 'math.sqrt(' + x + ')'; break;
    case 'LN':    code = 'math.log(' + x + ')'; break;
    case 'LOG10': code = 'math.log10(' + x + ')'; break;
    case 'EXP':   code = 'math.exp(' + x + ')'; break;
    case 'INV':   code = '1 / ' + x; precedence = Blockly.Python.ORDER_MULTIPLICATIVE; break;
    case 'SQUARE': code = x + ' ** 2'; precedence = Blockly.Python.ORDER_EXPONENTIATION; break;
    case 'CUBE':  code = x + ' ** 3'; precedence = Blockly.Python.ORDER_EXPONENTIATION; break;
    default:      code = 'abs(' + x + ')'; break;
  }

  return [code, precedence];
};
