// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_resize                           ║
// ║ Category: image                               ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Resize an image                          ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_resize'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_resize", "message0": "Resize %1 to %2 × %3",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" },
        { "type": "input_value", "name": "WIDTH", "check": "Number" },
        { "type": "input_value", "name": "HEIGHT", "check": "Number" }
      ],
      "inputsInline": true, "output": "Image", "colour": 300,
      "tooltip": "Resize an image to a specific width and height"
    });
  }
};

Blockly.Python['pcr_img_resize'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_ATOMIC) || '_img';
  var w = Blockly.Python.valueToCode(block, 'WIDTH', Blockly.Python.ORDER_NONE) || '100';
  var h = Blockly.Python.valueToCode(block, 'HEIGHT', Blockly.Python.ORDER_NONE) || '100';
  return [img + '.resize((int(' + w + '), int(' + h + ')))', Blockly.Python.ORDER_FUNCTION_CALL];
};
