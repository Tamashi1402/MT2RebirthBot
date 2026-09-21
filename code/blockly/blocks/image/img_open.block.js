// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_open                              ║
// ║ Category: image                               ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Load an image file                      ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_open'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_open", "message0": "load image %1",
      "args0": [{ "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }],
      "output": "Image", "colour": 300,
      "tooltip": "Load an image file into the procedure as an image value (it does NOT open it in Windows). Works with resource locations (res://...) or plain paths. Arrow-corner icon: reads the pick metadata stored with the image (in the mode-settings value or embedded in the PNG) and drops its point + box as blocks."
    });
    // meta-drop icon → point + box the image was picked from
    if (Blockly.icons && Blockly.icons.MFMetaDropIcon) {
      this.addIcon(new Blockly.icons.MFMetaDropIcon(this));
    }
  }
};

Blockly.Python['pcr_img_open'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['Image.open(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
