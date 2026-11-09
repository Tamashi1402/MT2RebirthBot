// ╔══════════════════════════════════════════════╗
// ║ Block: logic_ternary                           ║
// ║ Category: base/logic                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Ternary (condition ? a : b → a if cond) ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['logic_ternary'] = function(block) {
  var ifTrue = Blockly.Python.valueToCode(block, 'THEN', Blockly.Python.ORDER_CONDITIONAL) || 'None';
  var condition = Blockly.Python.valueToCode(block, 'IF', Blockly.Python.ORDER_CONDITIONAL) || 'False';
  var ifFalse = Blockly.Python.valueToCode(block, 'ELSE', Blockly.Python.ORDER_CONDITIONAL) || 'None';

  var code = ifTrue + ' if ' + condition + ' else ' + ifFalse;
  return [code, Blockly.Python.ORDER_CONDITIONAL];
};
