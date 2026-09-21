// ╔══════════════════════════════════════════════╗
// ║ Blocks: workspace tool lookup + availability    ║
// ║ Category: workspace                              ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['mf_workspace_tool'] = {
  init: function() {
    this.appendValueInput('REL')
      .setCheck('String')
      .appendField('tool');
    this.appendDummyInput().appendField('in this workspace');
    this.setOutput(true, 'String');
    this.setColour(160);
    this.setTooltip('Full path of an executable in this workspace\'s libs folder (a file, a folder, or a file without its .exe extension). Empty text when the workspace ships no such tool.');
  }
};
Blockly.Python['mf_workspace_tool'] = function(block) {
  var rel = Blockly.Python.valueToCode(block, 'REL', Blockly.Python.ORDER_NONE) || "''";
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.tool", ' + rel + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['mf_workspace_tool_available'] = {
  init: function() {
    this.appendValueInput('REL')
      .setCheck('String')
      .appendField('tool');
    this.appendDummyInput().appendField('is available in this workspace');
    this.setOutput(true, 'Boolean');
    this.setColour(160);
    this.setTooltip('True when this workspace ships the given tool in its libs folder. Lets a mode check before using it.');
  }
};
Blockly.Python['mf_workspace_tool_available'] = function(block) {
  var rel = Blockly.Python.valueToCode(block, 'REL', Blockly.Python.ORDER_NONE) || "''";
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.available", ' + rel + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
