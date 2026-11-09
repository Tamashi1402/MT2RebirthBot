// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_res_location — resource location     ║
// ║ Category: components                           ║
// ║ Desc: A pointer to a file: res://name.png is a ║
// ║       workspace resource, any path works too. ║
// ║       Pipette icon opens a native file dialog. ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_res_location'] = {
  init: function() {
    this.appendValueInput('PATH')
      .setCheck(['String', 'RESLOC'])
      .appendField('resource location');
    this.setOutput(true, ['String', 'RESLOC']);
    this.setColour(270);
    this.setTooltip('A resource location: res://name.png points at a file in this workspace\'s resources folder, or use any absolute/relative path. Pipette icon opens a file dialog.');
    // pipette icon → native file dialog
    if (Blockly.icons && Blockly.icons.MFPickIcon) {
      this.addIcon(new Blockly.icons.MFPickIcon('file', this));
    }
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_res_location'] = function(block) {
  var path = Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''";
  return ['resloc(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
