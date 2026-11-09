// ╔══════════════════════════════════════════════╗
// ║ Blocks: workspace resource / library paths      ║
// ║ Category: workspace                              ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['mf_workspace_resource'] = {
  init: function() {
    this.appendValueInput('REL')
      .setCheck('String')
      .appendField('resource');
    this.setOutput(true, ['String', 'RESLOC']);
    this.setColour(160);
    this.setTooltip('Path of a file in this workspace\'s resources folder. Pass a relative name like "macros/mine.macro" or "images/icon.png".');
  }
};
Blockly.Python['mf_workspace_resource'] = function(block) {
  var rel = Blockly.Python.valueToCode(block, 'REL', Blockly.Python.ORDER_NONE) || "''";
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.resource", ' + rel + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['mf_workspace_lib'] = {
  init: function() {
    this.appendValueInput('REL')
      .setCheck('String')
      .appendField('library folder');
    this.appendDummyInput().appendField('in this workspace');
    this.setOutput(true, ['String', 'RESLOC']);
    this.setColour(160);
    this.setTooltip('Path of a folder/file in this workspace\'s libs folder. External tools shipped by a workspace live there (e.g. libs/tesseract-ocr).');
  }
};
Blockly.Python['mf_workspace_lib'] = function(block) {
  var rel = Blockly.Python.valueToCode(block, 'REL', Blockly.Python.ORDER_NONE) || "''";
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.lib", ' + rel + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
