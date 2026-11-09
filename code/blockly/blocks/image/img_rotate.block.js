// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_rotate                           ║
// ║ Category: image                               ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Rotate an image                          ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_rotate'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_rotate", "message0": "Rotate %1 by %2 degrees",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" },
        { "type": "input_value", "name": "ANGLE", "check": "Number" }
      ],
      "inputsInline": true, "output": "Image", "colour": 300,
      "tooltip": "Rotate an image by a given angle in degrees"
    });
  }
};

Blockly.Python['pcr_img_rotate'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_ATOMIC) || '_img';
  var angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '90';
  return [img + '.rotate(float(' + angle + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
