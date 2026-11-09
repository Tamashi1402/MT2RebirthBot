// ╔════════════════════════════════════════════╗
// ║ Block: pcr_color_diff — color difference    ║
// ║ Category: color                             ║
// ║ Desc: 0.0 (identical) - 1.0 (max distance) ║
// ╚════════════════════════════════════════════╝

Blockly.Blocks['pcr_color_diff'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_diff",
      "message0": "get color difference between %1 and %2",
      "args0": [
        { "type": "input_value", "name": "COLOR1", "check": ["String", "Color"] },
        { "type": "input_value", "name": "COLOR2", "check": ["String", "Color"] }
      ],
      "inputsInline": true,
      "output": "Number", "colour": 230,
      "tooltip": "Difference between two colors as a number from 0.0 (identical) to 1.0 (opposite)."
    });
  }
};

Blockly.Python['pcr_color_diff'] = function(block) {
  var c1 = Blockly.Python.valueToCode(block, 'COLOR1', Blockly.Python.ORDER_NONE) || '"#000000"';
  var c2 = Blockly.Python.valueToCode(block, 'COLOR2', Blockly.Python.ORDER_NONE) || '"#000000"';
  return ['color_diff(' + c1 + ', ' + c2 + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
