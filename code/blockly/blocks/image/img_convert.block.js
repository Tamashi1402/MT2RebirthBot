// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_convert                          ║
// ║ Category: image                               ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Image → average color value             ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_convert'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_convert", "message0": "convert %1 to color",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" }
      ],
      "inputsInline": true, "output": "Color", "colour": 20,
      "tooltip": "The image's average color as a color value \u2014 plug it into any color block (difference, red/green/blue, opacity). Works with screenshots, loaded images, anything image-shaped."
    });
  }
};

Blockly.Python['pcr_img_convert'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_ATOMIC) || '_img';
  return ['img_to_color(' + img + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
