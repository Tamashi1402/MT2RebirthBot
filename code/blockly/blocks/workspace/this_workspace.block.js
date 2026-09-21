// ╔══════════════════════════════════════════════╗
// ║ Block: mf_workspace_this — this workspace       ║
// ║ Category: workspace                              ║
// ║ Desc: The folder of the workspace this mode is   ║
// ║       running from ("" outside a workspace).     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['mf_workspace_this'] = {
  init: function() {
    this.appendDummyInput().appendField('this workspace');
    this.setOutput(true, ['String', 'RESLOC']);
    this.setColour(160);
    this.setTooltip('The folder of the workspace this mode/project is running from. Empty text when the mode is not running from a workspace. Use it to build paths to your own resources/macros/libraries.');
  }
};

Blockly.Python['mf_workspace_this'] = function() {
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.root")', Blockly.Python.ORDER_FUNCTION_CALL];
};
