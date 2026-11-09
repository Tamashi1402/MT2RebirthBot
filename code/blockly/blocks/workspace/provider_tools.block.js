// ╔══════════════════════════════════════════════╗
// ║ Blocks: installed provider workspace tools       ║
// ║ Category: workspace                              ║
// ║ Desc: Look up tools in an INSTALLED provider      ║
// ║ workspace (Download Center), e.g. tesseract-ocr. ║
// ╚══════════════════════════════════════════════╝

function mfProviderMenu() {
  var list = window.__MF_PROVIDER_WORKSPACES;
  if (list && list.length) return list;
  return [["tesseract-ocr", "tesseract-ocr"]];
}

Blockly.Blocks['mf_provider_tool'] = {
  init: function() {
    this.appendValueInput('REL')
      .setCheck('String')
      .appendField('tool');
    this.appendDummyInput()
      .appendField('from installed workspace')
      .appendField(new Blockly.FieldDropdown(mfProviderMenu), 'WS');
    this.setOutput(true, 'String');
    this.setColour(160);
    this.setTooltip('Full path of a tool inside an installed provider workspace (Download Center). Empty text when that workspace is not installed.');
  }
};
Blockly.Python['mf_provider_tool'] = function(block) {
  var rel = Blockly.Python.valueToCode(block, 'REL', Blockly.Python.ORDER_NONE) || "''";
  var ws = JSON.stringify(block.getFieldValue('WS') || '');
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.provider_tool", ' + ws + ', ' + rel + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['mf_provider_tool_available'] = {
  init: function() {
    this.appendValueInput('REL')
      .setCheck('String')
      .appendField('tool');
    this.appendDummyInput()
      .appendField('from installed workspace')
      .appendField(new Blockly.FieldDropdown(mfProviderMenu), 'WS')
      .appendField('is installed');
    this.setOutput(true, 'Boolean');
    this.setColour(160);
    this.setTooltip('True when the provider workspace (Download Center) is installed AND ships the given tool. Blocks that need a provider (OCR, AI, ...) should check this and show a friendly message when missing.');
  }
};
Blockly.Python['mf_provider_tool_available'] = function(block) {
  var rel = Blockly.Python.valueToCode(block, 'REL', Blockly.Python.ORDER_NONE) || "''";
  var ws = JSON.stringify(block.getFieldValue('WS') || '');
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.provider_available", ' + ws + ', ' + rel + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['mf_provider_workspace_root'] = {
  init: function() {
    this.appendDummyInput()
      .appendField('folder of installed workspace')
      .appendField(new Blockly.FieldDropdown(mfProviderMenu), 'WS');
    this.setOutput(true, 'String');
    this.setColour(160);
    this.setTooltip('Folder of an installed provider workspace (Download Center). Empty text when it is not installed.');
  }
};
Blockly.Python['mf_provider_workspace_root'] = function(block) {
  var ws = JSON.stringify(block.getFieldValue('WS') || '');
  return ['macroforge.engine.functions.call("macroforge.engine.workspace.provider_root", ' + ws + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
