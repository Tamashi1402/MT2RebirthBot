// ╔══════════════════════════════════════════════╗
// ║ Block: run external program (workspace tool)    ║
// ║ Category: workspace (advanced)                  ║
// ║ Desc: Run an executable (normally one found    ║
// ║ with the tool blocks) and get its result.     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['mf_workspace_run'] = {
  init: function() {
    this.appendValueInput('EXE')
      .setCheck('String')
      .appendField('run program');
    this.appendValueInput('ARGS')
      .setCheck('String')
      .appendField('with arguments');
    this.appendDummyInput()
      .appendField('wait for exit')
      .appendField(new Blockly.FieldCheckbox('TRUE'), 'WAIT');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(160);
    this.setTooltip('Run an external program (usually a tool path from the workspace blocks). Arguments may use spaces like on a command line. Returns {"ok", "code", "stdout", "stderr"} — read it with the "run result" blocks below.');
  }
};
Blockly.Python['mf_workspace_run'] = function(block) {
  var exe = Blockly.Python.valueToCode(block, 'EXE', Blockly.Python.ORDER_NONE) || "''";
  var args = Blockly.Python.valueToCode(block, 'ARGS', Blockly.Python.ORDER_NONE) || "''";
  var wait = block.getFieldValue('WAIT') === 'TRUE' ? 'True' : 'False';
  return 'macroforge.engine.functions.call("macroforge.engine.workspace.run", ' + exe + ', ' + args + ', ' + wait + ')\n';
};

Blockly.Blocks['mf_workspace_run_get'] = {
  init: function() {
    this.appendValueInput('RESULT')
      .setCheck(null)
      .appendField('of run result');
    this.appendDummyInput()
      .appendField(new Blockly.FieldDropdown([['succeeded?', 'ok'], ['exit code', 'code'], ['output text', 'stdout'], ['error text', 'stderr']]), 'FIELD');
    this.setOutput(true, null);
    this.setColour(160);
    this.setTooltip('Read a field of a "run program" result: ok (true/false), exit code, or the printed output/error text.');
  }
};
Blockly.Python['mf_workspace_run_get'] = function(block) {
  var result = Blockly.Python.valueToCode(block, 'RESULT', Blockly.Python.ORDER_NONE) || '{}';
  var field = JSON.stringify(block.getFieldValue('FIELD') || 'ok');
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.run_get", ' + result + ', ' + field + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
