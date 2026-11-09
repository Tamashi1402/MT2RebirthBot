// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_crop                             ║
// ║ Category: image                               ║
// ║ Desc: Crop image to a box                      ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_crop'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_crop", "message0": "Crop %1 to box %2",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" },
        { "type": "input_value", "name": "BOX", "check": "Box" }
      ],
      "inputsInline": true, "output": "Image", "colour": 300,
      "tooltip": "Crop a box region (x1, y1, x2, y2) from an image"
    });
  }
};

Blockly.Python['pcr_img_crop'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_ATOMIC) || '_img';
  var box = Blockly.Python.valueToCode(block, 'BOX', Blockly.Python.ORDER_NONE) || 'box(0, 0, 100, 100)';
  return [img + '.crop(tuple(' + box + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
