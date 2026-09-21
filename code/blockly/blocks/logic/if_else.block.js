// ╔══════════════════════════════════════════════╗
// ║ Block: controls_if                            ║
// ║ Category: base/logic                          ║
// ║ Built-in: Yes (Blockly provides the block)    ║
// ║ Desc: If / Else If / Else conditional          ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['controls_if'] = function(block) {
  var code = '';
  var n = 0;
  var condition, branch;

  // Collect all if/elif/else from the mutator
  while (block.getInput('IF' + n)) {
    condition = Blockly.Python.valueToCode(block, 'IF' + n, Blockly.Python.ORDER_NONE) || 'False';
    branch = Blockly.Python.statementToCode(block, 'DO' + n) || '    pass\n';
    if (n === 0) {
      code = 'if ' + condition + ':\n' + branch;
    } else {
      code += 'elif ' + condition + ':\n' + branch;
    }
    n++;
  }

  if (block.getInput('ELSE')) {
    branch = Blockly.Python.statementToCode(block, 'ELSE') || '    pass\n';
    code += 'else:\n' + branch;
  }

  return code + '\n';
};
