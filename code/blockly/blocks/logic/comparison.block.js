// ╔══════════════════════════════════════════════╗
// ║ Block: logic_compare                           ║
// ║ Category: base/logic                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Comparison operators (=, ≠, <, >, ≤, ≥) ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['logic_compare'] = function(block) {
  var op = block.getFieldValue('OP');
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || '0';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || '0';

  var pyOp;
  switch (op) {
    case 'EQ':  pyOp = '=='; break;
    case 'NEQ': pyOp = '!='; break;
    case 'LT':  pyOp = '<';  break;
    case 'LTE': pyOp = '<='; break;
    case 'GT':  pyOp = '>';  break;
    case 'GTE': pyOp = '>='; break;
    default:    pyOp = '=='; break;
  }

  return [a + ' ' + pyOp + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};
