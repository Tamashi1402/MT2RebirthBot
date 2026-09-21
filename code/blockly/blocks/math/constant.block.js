// ╔══════════════════════════════════════════════╗
// ║ Block: math_constant                            ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Math constants (π, e, φ, etc.)          ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_constant'] = function(block) {
  var constant = block.getFieldValue('CONSTANT');

  var value;
  switch (constant) {
    case 'PI':     value = 'math.pi'; break;
    case 'E':      value = 'math.e'; break;
    case 'GOLDEN': value = '(1 + math.sqrt(5)) / 2'; break;
    case 'SQRT2':  value = 'math.sqrt(2)'; break;
    case 'HALF':   value = '0.5'; break;
    case 'INFINITY': value = 'float("inf")'; break;
    default:       value = '0'; break;
  }

  return [value, Blockly.Python.ORDER_ATOMIC];
};
