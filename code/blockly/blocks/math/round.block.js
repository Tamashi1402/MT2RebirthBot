// ╔══════════════════════════════════════════════╗
// ║ Block: math_round                               ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Round / floor / ceil                     ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_round'] = function(block) {
  var op = block.getFieldValue('OP');
  var x = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_NONE) || '0';

  var func;
  switch (op) {
    case 'ROUND': func = 'round'; break;
    case 'ROUNDUP':   func = 'math.ceil'; break;
    case 'ROUNDDOWN': func = 'math.floor'; break;
    default:          func = 'round'; break;
  }

  return [func + '(' + x + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
