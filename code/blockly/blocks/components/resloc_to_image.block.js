// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_resloc_to_image — resource         ║
// ║         location → image conversion           ║
// ║ Category: components                           ║
// ║ Desc: Loads the image behind a resource         ║
// ║       location (res:// or any path) as a       ║
// ║       PIL image, usable anywhere an image      ║
// ║       value fits (variables, OCR, image        ║
// ║       compare, host calls...).                 ║
// ╚══════════════════════════════════════════════╝
Blockly.Blocks['pcr_resloc_to_image'] = {
  init: function() {
    this.appendValueInput('PATH')
      .setCheck(['String', 'RESLOC'])
      .appendField('to image');
    this.appendDummyInput().appendField('resource location');
    this.setInputsInline(true);
    this.setOutput(true, 'Image');
    this.setColour(300);
    this.setTooltip('Convert a resource location (res://name.png or any path) into a loaded image value. Use it to put resource pictures into image variables or any block that takes an image. Arrow-corner icon: reads the pick metadata stored with the image (in the mode-settings value or embedded in the PNG) and drops its point + box as blocks.');
    // meta-drop icon → point + box the resource was picked from
    if (Blockly.icons && Blockly.icons.MFMetaDropIcon) {
      this.addIcon(new Blockly.icons.MFMetaDropIcon(this));
    }
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_resloc_to_image'] = function(block) {
  var path = Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''";
  return ['image_from_res(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
