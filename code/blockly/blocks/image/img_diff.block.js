// ╔════════════════════════════════════════════╗
// ║ Block: pcr_img_diff — image difference      ║
// ║ Category: image                             ║
// ║ Desc: 0.0 (identical) - 1.0 (max diff)     ║
// ╚════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_diff'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_diff",
      "message0": "get image difference between %1 and %2",
      "args0": [
        { "type": "input_value", "name": "IMG1", "check": "Image" },
        { "type": "input_value", "name": "IMG2", "check": "Image" }
      ],
      "inputsInline": true,
      "output": "Number", "colour": 230,
      "tooltip": "Mean pixel difference between two images as a number from 0.0 (identical) to 1.0 (completely different). Sizes are auto-matched."
    });
  }
};

Blockly.Python['pcr_img_diff'] = function(block) {
  var i1 = Blockly.Python.valueToCode(block, 'IMG1', Blockly.Python.ORDER_NONE) || 'None';
  var i2 = Blockly.Python.valueToCode(block, 'IMG2', Blockly.Python.ORDER_NONE) || 'None';
  return ['img_diff(' + i1 + ', ' + i2 + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
