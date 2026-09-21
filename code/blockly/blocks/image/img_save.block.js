// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_save                            ║
// ║ Category: image                               ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Save an image to file                   ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_save'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_save", "message0": "Save %1 to %2",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" },
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true, "previousStatement": null, "nextStatement": null, "colour": 300,
      "tooltip": "Save an image to a file"
    });
  }
};

Blockly.Python['pcr_img_save'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_ATOMIC) || '_img';
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  return img + '.save(' + path + ')\n';
};
